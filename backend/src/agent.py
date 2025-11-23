import logging
import json
from pathlib import Path
from typing import TypedDict, Any

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


# ----- Day 2: simple order state -----
class OrderState(TypedDict, total=False):
    drinkType: str
    size: str
    milk: str
    extras: list[str]
    name: str


def empty_order() -> OrderState:
    return {
        "drinkType": "",
        "size": "",
        "milk": "",
        "extras": [],
        "name": "",
    }


class Assistant(Agent):
    def __init__(self) -> None:
        # persona + behavior
        super().__init__(
            instructions="""
You are a friendly, efficient barista at Falcon Brew Café.
You are talking to the customer by voice, but you will see their words as text.

Your ONLY job is to take coffee orders, keep them organized, and confirm them clearly.

You are working with an internal order object that has these fields:
- drinkType (string)
- size (string)
- milk (string)
- extras (list of strings, can be empty)
- name (string, the customer's name)

Use the tools provided to:
1) Update the order whenever the user gives or changes details.
2) Check which fields are still missing.
3) Save the final order once all fields are filled.

Conversation rules:
- Always be warm and concise, like a real café barista.
- Ask clarifying follow-up questions until ALL fields of the order are filled.
- Do NOT assume missing details – ask for them.
- When the order is complete:
  * Call the finalize_order tool.
  * Then give a neat, one-paragraph spoken summary of the full order
    (mention drink type, size, milk preference, extras, and the customer's name).
- After finishing one order, politely ask if they want to place another one.

Formatting rules:
- No emojis, no markdown, no bullet points in your replies.
- Just natural, spoken sentences.
""",
        )
        # in-memory state for the current order
        self.current_order: OrderState = empty_order()

    # helper to see if all required fields are set
    def _order_is_complete(self) -> bool:
        o = self.current_order
        return bool(
            o.get("drinkType")
            and o.get("size")
            and o.get("milk")
            and o.get("name")
        )
        # extras can be an empty list

    @function_tool
    async def update_order_state(
        self,
        context: RunContext,
        drinkType: str | None = None,
        size: str | None = None,
        milk: str | None = None,
        extras: list[str] | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """
        Update the in-progress coffee order with any details the user has given.

        Use this whenever the customer mentions or changes:
        - drink type (e.g. latte, cappuccino, cold brew)
        - size (e.g. small, medium, large)
        - milk preference (e.g. whole, oat, almond)
        - extras (e.g. extra shot, vanilla syrup, less ice)
        - their name

        You can pass only the fields that changed. The tool returns the
        full current order and whether it is complete.
        """

        logger.info("Updating order state")

        if drinkType is not None:
            self.current_order["drinkType"] = drinkType

        if size is not None:
            self.current_order["size"] = size

        if milk is not None:
            self.current_order["milk"] = milk

        if extras is not None:
            # overwrite with the new list of extras
            self.current_order["extras"] = extras

        if name is not None:
            self.current_order["name"] = name

        complete = self._order_is_complete()

        return {
            "order": self.current_order,
            "is_complete": complete,
        }

    @function_tool
    async def finalize_order(self, context: RunContext) -> dict[str, Any]:
        """
        Save the current order to a JSON file once all fields are filled.

        Use this ONLY when the order is complete and ready to be placed.
        The tool appends the order to 'orders.json' on the server and then
        resets the internal order so a new one can be started.
        """

        logger.info("Finalizing order")

        if not self._order_is_complete():
            # let the model know it tried too early
            return {
                "saved": False,
                "reason": "order_incomplete",
                "order": self.current_order,
            }

        orders_file = Path("orders.json")
        all_orders: list[OrderState] = []

        if orders_file.exists():
            try:
                all_orders = json.loads(
                    orders_file.read_text(encoding="utf-8")
                )
                if not isinstance(all_orders, list):
                    all_orders = []
            except Exception:
                logger.exception("Failed to read existing orders.json, resetting file")
                all_orders = []

        # copy so we don't mutate what we append later
        order_to_save: OrderState = {
            "drinkType": self.current_order.get("drinkType", ""),
            "size": self.current_order.get("size", ""),
            "milk": self.current_order.get("milk", ""),
            "extras": list(self.current_order.get("extras", [])),
            "name": self.current_order.get("name", ""),
        }

        all_orders.append(order_to_save)

        orders_file.write_text(
            json.dumps(all_orders, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # reset for next customer
        self.current_order = empty_order()

        return {
            "saved": True,
            "order": order_to_save,
            "message": "Order saved to JSON file on the server.",
        }


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Voice pipeline: Deepgram STT + Gemini LLM + Murf Falcon TTS
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session with our barista agent
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
