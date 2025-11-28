import logging
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    tokenize,
    function_tool,
    RunContext,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
CATALOG_PATH = os.path.join(BASE_DIR, "shared_data", "day7_catalog.json")
ORDERS_DIR = os.path.join(BASE_DIR, "orders")
ORDERS_FILE = os.path.join(ORDERS_DIR, "day7_orders.json")


def load_catalog() -> List[Dict[str, Any]]:
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        logger.exception("Failed to read catalog")
        return []


def append_order(order: Dict[str, Any]) -> None:
    os.makedirs(ORDERS_DIR, exist_ok=True)
    data: List[Dict[str, Any]] = []
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if isinstance(existing, list):
                data = existing
        except Exception:
            data = []
    data.append(order)
    tmp = ORDERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, ORDERS_FILE)


class FoodOrderAgent(Agent):
    """
    Food & grocery ordering assistant for a fictional brand 'QuickBasket'.
    """

    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are a friendly voice assistant for a fictional brand called "QuickBasket".

Your job:
- Help the user order groceries and simple meal ingredients from a catalog.
- Ask clarifying questions when needed (quantity, size, type).
- Maintain a cart with items and quantities while you talk.
- Support requests like:
  - "Add 2 breads and 1 peanut butter."
  - "I need ingredients for a peanut butter sandwich."
  - "Get me what I need for pasta for two people."

You have access to these tools:
- load_catalog
- search_items
- add_item_to_cart
- remove_item_from_cart
- update_item_quantity
- list_cart
- add_recipe_ingredients
- place_order

CONVERSATION GUIDELINES:

1) On first interaction:
   - Briefly introduce yourself as QuickBasket voice assistant.
   - Explain that you can add groceries and prepared foods to their cart, and also add ingredients for simple dishes.
   - Call 'load_catalog' to ensure the catalog is ready.

2) When user mentions specific items:
   - Use 'search_items' to find the best match for the item name or keywords.
   - Ask for missing details only if necessary (e.g., quantity).
   - Call 'add_item_to_cart' with the chosen item id and quantity.
   - Confirm verbally what you added.

3) When user says "ingredients for ..." or similar:
   - Call 'add_recipe_ingredients' with the user's phrase.
   - This tool will figure out which set of items to add (for example, bread + peanut butter for a sandwich, pasta + sauce for pasta).
   - After the tool runs, clearly tell the user which items and quantities were added.

4) Cart management:
   - When user asks "what's in my cart", call 'list_cart' and read back items and total.
   - If user wants to remove or change quantities, use 'remove_item_from_cart' or 'update_item_quantity'.
   - Always confirm what changed.

5) Placing the order:
   - If user says things like "that's all", "place my order", or "I'm done":
     - First, call 'list_cart'.
     - If cart is empty, explain that there is nothing to place.
     - Otherwise, confirm cart contents and total.
     - Ask for a simple customer name and delivery note (you can collect them in conversation).
     - Then call 'place_order' with the name and note.
     - After that, tell user the order has been placed in the system and give the order id.

6) Style:
   - Be concise, warm, and practical.
   - Do not talk about real payments or real delivery; keep it clearly as a demo ordering experience.
   - Use only the catalog and tools provided. Do not invent extra products or prices.
""".strip()
        )

        self.catalog: List[Dict[str, Any]] = []
        # cart: list of {"item_id", "name", "unit_price", "quantity"}
        self.cart: List[Dict[str, Any]] = []

    # ---------- internal helpers ----------

    def _find_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        for item in self.catalog:
            if item.get("id") == item_id:
                return item
        return None

    def _find_best_match(self, query: str) -> Optional[Dict[str, Any]]:
        q = (query or "").lower()
        best = None
        best_score = 0
        for item in self.catalog:
            text = f"{item.get('name','')} {item.get('category','')} {' '.join(item.get('tags', []))}".lower()
            score = 0
            for word in q.split():
                if len(word) < 3:
                    continue
                if word in text:
                    score += 1
            if score > best_score:
                best_score = score
                best = item
        return best

    def _add_to_cart(self, item: Dict[str, Any], quantity: int):
        if quantity <= 0:
            return
        item_id = item.get("id")
        for row in self.cart:
            if row["item_id"] == item_id:
                row["quantity"] += quantity
                return
        self.cart.append(
            {
                "item_id": item_id,
                "name": item.get("name"),
                "unit_price": float(item.get("price", 0)),
                "quantity": quantity,
            }
        )

    def _remove_from_cart(self, item_id: str) -> bool:
        before = len(self.cart)
        self.cart = [row for row in self.cart if row["item_id"] != item_id]
        return len(self.cart) < before

    def _update_quantity(self, item_id: str, quantity: int) -> bool:
        for row in self.cart:
            if row["item_id"] == item_id:
                if quantity <= 0:
                    self._remove_from_cart(item_id)
                else:
                    row["quantity"] = quantity
                return True
        return False

    def _cart_total(self) -> float:
        return sum(row["unit_price"] * row["quantity"] for row in self.cart)

    # ---------- Tools ----------

    @function_tool
    async def load_catalog(self, context: RunContext) -> Dict[str, Any]:
        """Load catalog items into memory."""
        self.catalog = load_catalog()
        return {"count": len(self.catalog)}

    @function_tool
    async def search_items(self, context: RunContext, query: str) -> Dict[str, Any]:
        """
        Search for an item in the catalog using a natural language query.
        Returns the best single match.
        """
        if not self.catalog:
            self.catalog = load_catalog()
        item = self._find_best_match(query)
        if item is None:
            return {"found": False, "message": f"No item found matching '{query}'."}
        return {"found": True, "item": item}

    @function_tool
    async def add_item_to_cart(self, context: RunContext, item_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Add a specific catalog item and quantity to the cart."""
        if not self.catalog:
            self.catalog = load_catalog()
        item = self._find_item_by_id(item_id)
        if item is None:
            return {"ok": False, "message": f"Item id {item_id} not found in catalog."}
        if quantity <= 0:
            return {"ok": False, "message": "Quantity must be at least 1."}
        self._add_to_cart(item, quantity)
        return {"ok": True, "item": item, "quantity": quantity, "cart_size": len(self.cart)}

    @function_tool
    async def remove_item_from_cart(self, context: RunContext, item_id: str) -> Dict[str, Any]:
        """Remove an item entirely from the cart."""
        removed = self._remove_from_cart(item_id)
        return {"ok": removed, "cart_size": len(self.cart)}

    @function_tool
    async def update_item_quantity(self, context: RunContext, item_id: str, quantity: int) -> Dict[str, Any]:
        """
        Set a new quantity for an item in the cart.
        If quantity <= 0, the item is removed.
        """
        updated = self._update_quantity(item_id, quantity)
        return {"ok": updated, "cart_size": len(self.cart)}

    @function_tool
    async def list_cart(self, context: RunContext) -> Dict[str, Any]:
        """
        Return current cart contents and total.
        """
        total = self._cart_total()
        return {"items": self.cart, "total": total}

    @function_tool
    async def add_recipe_ingredients(self, context: RunContext, description: str) -> Dict[str, Any]:
        """
        Add multiple items to the cart based on a high-level request like
        'ingredients for a peanut butter sandwich' or 'pasta for two people'.

        This uses a simple hard-coded mapping of recipe keywords to catalog tags.
        """
        if not self.catalog:
            self.catalog = load_catalog()

        desc = (description or "").lower()
        added: List[Dict[str, Any]] = []

        # Simple heuristic for servings
        servings = 1
        if "two" in desc or "2 people" in desc or "for 2" in desc:
            servings = 2
        if "three" in desc or "3 people" in desc or "for 3" in desc:
            servings = 3

        # Hard-coded recipes
        if "peanut butter" in desc and "sandwich" in desc:
            # bread + peanut butter
            needed_tags = ["bread", "peanut_butter"]
        elif "pasta" in desc:
            needed_tags = ["pasta", "sauce"]
        else:
            needed_tags = []

        for tag in needed_tags:
            best = None
            best_score = 0
            for item in self.catalog:
                tags = [t.lower() for t in item.get("tags", [])]
                score = 1 if tag in tags else 0
                if score > best_score:
                    best_score = score
                    best = item
            if best is not None:
                # basic rule: 1 unit per serving
                qty = max(1, servings)
                self._add_to_cart(best, qty)
                added.append({"item": best, "quantity": qty})

        return {
            "ok": True,
            "description": description,
            "added": added,
            "cart_size": len(self.cart),
        }

    @function_tool
    async def place_order(self, context: RunContext, customer_name: str, delivery_note: str = "") -> Dict[str, Any]:
        """
        Finalize the current cart as an order and write it to a JSON orders file.
        After saving, the cart is cleared.
        """
        if not self.cart:
            return {"ok": False, "message": "Cart is empty. Nothing to place."}
        total = self._cart_total()
        order_id = f"QB-{int(datetime.now(timezone.utc).timestamp())}"
        order = {
            "order_id": order_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "customer_name": customer_name.strip() or "Unknown",
            "delivery_note": delivery_note.strip(),
            "items": self.cart,
            "total": total,
        }
        append_order(order)
        # clear cart
        self.cart = []
        logger.info(f"Order placed: {order_id} total={total}")
        return {"ok": True, "order": order}


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = FoodOrderAgent()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-matthew",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # optional preload
    try:
        await agent.load_catalog(None)
        logger.info("Day 7 catalog loaded at startup")
    except Exception:
        logger.exception("Failed to preload catalog")

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
