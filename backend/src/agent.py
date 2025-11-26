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
FRAUD_DB_PATH = os.path.join(BASE_DIR, "shared_data", "day6_fraud_cases.json")


def load_db() -> List[Dict[str, Any]]:
    try:
        with open(FRAUD_DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        logger.exception("Failed to read fraud DB")
        return []


def save_db(cases: List[Dict[str, Any]]) -> None:
    try:
        tmp = FRAUD_DB_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cases, f, indent=2, ensure_ascii=False)
        os.replace(tmp, FRAUD_DB_PATH)
    except Exception:
        logger.exception("Failed to write fraud DB")


class FraudAgent(Agent):
    """
    Fraud alert voice agent for a fictional bank.

    Flow:
    - Load fraud cases.
    - Ask for user's first name.
    - Match to a case with status pending_review.
    - Ask a basic security question from DB (non-sensitive).
    - If verified -> read suspicious transaction.
    - Ask if customer made it (yes/no).
    - Update status: confirmed_safe / confirmed_fraud / verification_failed.
    - Save back to DB with outcome note.
    """

    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are a calm, professional fraud detection representative for a fictional bank called "SafeBank".

Your job in each call is:
- Introduce yourself and SafeBank's fraud department.
- Explain that you are calling about a suspicious transaction on the customer's card.
- Use only safe, non-sensitive verification (for example, a simple security question provided to you).
- NEVER ask for full card number, PIN, passwords, or one-time passwords.
- Keep language reassuring, clear, and concise.

CALL FLOW YOU SHOULD FOLLOW:

1) At the start of the conversation:
   - Greet the customer.
   - Tell them you are from SafeBank fraud department.
   - Briefly explain that you want to verify a recent potentially suspicious transaction.
   - Ask for the customer's first name so you can look up their case.
   - Use the tool 'select_case_for_user' with the given name.
   - If no matching case is found, explain that you don't see an active fraud alert and politely end the call.

2) If a case is found:
   - Tell the customer you will ask a simple security question.
   - Use the tool 'get_security_question' to retrieve a safe security question.
   - Ask that question exactly or in very similar words.
   - When the user answers, call the tool 'verify_security_answer' with their answer.
   - If verification fails, explain that you cannot continue and call 'mark_case_status' with 'verification_failed'.

3) If verification succeeds:
   - Use the tool 'get_transaction_details' to get a short description of the suspicious transaction:
     merchant, amount, masked card ending, date/time, and location.
   - Read out those details slowly and clearly.
   - Ask: "Did you make this transaction?" and listen to a yes/no style answer.

4) Once the user answers yes/no:
   - If they clearly confirm the transaction is legitimate, call 'mark_case_status' with 'confirmed_safe'.
   - If they clearly deny the transaction, call 'mark_case_status' with 'confirmed_fraud'.

5) After updating the case:
   - Give a short verbal summary of what you did:
     - For confirmed_safe: mention that no further action is required.
     - For confirmed_fraud: mention that the card will be blocked and a dispute will be raised (all mock/demo).
   - Thank the customer and end the call.

Throughout the call:
- Stay calm and friendly.
- Do not improvise details about the bank's systems beyond: blocking card, raising dispute, monitoring account (all as part of the demo).
- Use the tools I provided to you to read and update the fraud case. Do not invent your own database.
""".strip()
        )

        self.cases: List[Dict[str, Any]] = []
        self.active_case: Optional[Dict[str, Any]] = None

    # ---------- internal helpers ----------
    def _find_case_by_user(self, name: str) -> Optional[Dict[str, Any]]:
        name = (name or "").strip().lower()
        for c in self.cases:
            if c.get("status") == "pending_review" and c.get("userName", "").lower() == name:
                return c
        return None

    def _update_active_case_in_db(self):
        if not self.active_case:
            return
        cases = self.cases
        target_id = self.active_case.get("id")
        for i, c in enumerate(cases):
            if c.get("id") == target_id:
                cases[i] = self.active_case
                break
        save_db(cases)

    # ---------- tools ----------

    @function_tool
    async def load_fraud_cases(self, context: RunContext) -> Dict[str, Any]:
        """
        Load fraud cases from the local JSON DB.
        Call this once near the start of the conversation.
        """
        self.cases = load_db()
        return {"count": len(self.cases), "pending": [c.get("id") for c in self.cases if c.get("status") == "pending_review"]}

    @function_tool
    async def select_case_for_user(self, context: RunContext, first_name: str) -> Dict[str, Any]:
        """
        Select the first 'pending_review' case for a given customer first name.
        """
        if not self.cases:
            self.cases = load_db()

        case = self._find_case_by_user(first_name)
        if case is None:
            return {"found": False, "message": f"No active fraud case found for {first_name}."}

        self.active_case = case
        return {
            "found": True,
            "case_id": case.get("id"),
            "userName": case.get("userName"),
            "status": case.get("status"),
        }

    @function_tool
    async def get_security_question(self, context: RunContext) -> Dict[str, Any]:
        """
        Return the non-sensitive security question for the active case.
        """
        if not self.active_case:
            return {"ok": False, "message": "No active case selected."}
        q = self.active_case.get("securityQuestion")
        return {"ok": True, "question": q}

    @function_tool
    async def verify_security_answer(self, context: RunContext, answer: str) -> Dict[str, Any]:
        """
        Check the provided answer against the stored security answer.
        """
        if not self.active_case:
            return {"ok": False, "verified": False, "message": "No active case selected."}
        stored = (self.active_case.get("securityAnswer") or "").strip().lower()
        given = (answer or "").strip().lower()
        verified = stored != "" and stored == given
        return {"ok": True, "verified": verified}

    @function_tool
    async def get_transaction_details(self, context: RunContext) -> Dict[str, Any]:
        """
        Return a structured description of the suspicious transaction for the active case.
        """
        if not self.active_case:
            return {"ok": False, "message": "No active case selected."}
        c = self.active_case
        return {
            "ok": True,
            "merchant": c.get("transactionName"),
            "amount": c.get("transactionAmount"),
            "cardEnding": c.get("cardEnding"),
            "time": c.get("transactionTime"),
            "category": c.get("transactionCategory"),
            "source": c.get("transactionSource"),
            "location": c.get("transactionLocation"),
        }

    @function_tool
    async def mark_case_status(self, context: RunContext, status: str, note: str) -> Dict[str, Any]:
        """
        Update the active case status and outcome note.

        Allowed status values:
        - confirmed_safe
        - confirmed_fraud
        - verification_failed
        """
        if not self.active_case:
            return {"ok": False, "message": "No active case selected."}

        allowed = {"confirmed_safe", "confirmed_fraud", "verification_failed"}
        if status not in allowed:
            return {"ok": False, "message": f"Invalid status {status}"}

        self.active_case["status"] = status
        self.active_case["outcomeNote"] = note
        self.active_case["lastUpdated"] = datetime.now(timezone.utc).isoformat()

        # persist to DB
        self._update_active_case_in_db()
        logger.info(f"Case {self.active_case.get('id')} updated to {status}: {note}")

        return {"ok": True, "case_id": self.active_case.get("id"), "status": status, "note": note}


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = FraudAgent()

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

    # Start session and connect
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Pre-load fraud DB (optional but nice)
    try:
        await agent.load_fraud_cases(None)
        logger.info("Fraud cases loaded at startup")
    except Exception:
        logger.exception("Failed to preload fraud cases")

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
