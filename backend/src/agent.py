# backend/src/agent.py
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
FAQ_PATH = os.path.join(BASE_DIR, "shared_data", "day5_freshworks_faq.json")
LEADS_DIR = os.path.join(BASE_DIR, "leads")
LEADS_FILE = os.path.join(LEADS_DIR, "freshworks_leads.json")


# ---------- helper functions ----------
def _load_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _append_lead(record: Dict[str, Any]):
    os.makedirs(LEADS_DIR, exist_ok=True)
    data = []
    if os.path.exists(LEADS_FILE):
        try:
            data = json.load(open(LEADS_FILE, encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except Exception:
            data = []
    data.append(record)
    tmp = LEADS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LEADS_FILE)


# ---------- Simple FAQ search ----------
def find_faq_answer(faq_list: List[Dict[str, Any]], question_text: str) -> Optional[Dict[str, Any]]:
    q = (question_text or "").lower()
    # simple keyword match: find FAQ with the highest overlap of words
    best = None
    best_score = 0
    qwords = set(w for w in q.split() if len(w) > 3)
    for item in faq_list:
        txt = (item.get("question", "") + " " + item.get("answer", "")).lower()
        twords = set(w for w in txt.split() if len(w) > 3)
        score = len(qwords & twords)
        if score > best_score:
            best_score = score
            best = item
    # threshold: require at least 1 overlapping word
    return best if best_score > 0 else None


# ---------- Agent ----------
class SDRAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are an SDR for Freshworks. Greet visitors warmly and ask what brought them here.
Focus on understanding their needs. Use the provided FAQ content to answer product/pricing questions and do NOT invent details not in the FAQ.
Collect lead fields: name, company, email, role, use_case, team_size, timeline.
Speak naturally and be concise. When the user indicates they are done (for example: "that's all", "thanks", "I'm done"), call the tool `finalize_call` with the user's last message. If the tool reports `need_email`, ask the user for their email, gather it via `gather_lead_field`, then call `finalize_call` again to save and close.
Speak Politely and Professionally at all times.

""".strip()
        )
        self.faq: List[Dict[str, Any]] = []
        self.lead: Dict[str, Any] = {}
        # default lead collection fields and friendly prompts
        self.lead_schema = {
            "name": "Can I have your full name, please?",
            "company": "What company do you work at?",
            "role": "What's your role there?",
            "use_case": "What would you like to use Freshworks for?",
            "team_size": "How big is your team?",
            "timeline": "What's your expected timeline to start? (now / soon / later)",
            "email": "What's the best email to reach you at?"
        }

    # ---------- Tools ----------
    @function_tool
    async def load_faq(self, context: RunContext) -> Dict[str, Any]:
        """Load FAQ content from shared_data and return basic metadata."""
        faq = _load_json(FAQ_PATH)
        if not isinstance(faq, list):
            self.faq = []
            return {"ok": False, "message": "FAQ not found or invalid"}
        self.faq = faq
        return {"ok": True, "count": len(faq)}

    @function_tool
    async def answer_from_faq(self, context: RunContext, question: str) -> Dict[str, Any]:
        """Return an exact or best-match FAQ answer. If none, say not found."""
        if not self.faq:
            return {"found": False, "answer": "I don't have the FAQ loaded."}
        found = find_faq_answer(self.faq, question)
        if not found:
            return {"found": False, "answer": "I don't see that detail in the FAQ. Would you like me to connect you to sales?"}
        return {"found": True, "answer": found.get("answer")}

    @function_tool
    async def gather_lead_field(self, context: RunContext, field: str, value: str) -> Dict[str, Any]:
        """Store a single lead field as the user provides it."""
        key = (field or "").strip().lower()
        if key not in self.lead_schema:
            return {"ok": False, "message": f"Unknown field {field}"}
        self.lead[key] = value.strip()
        return {"ok": True, "lead": self.lead}

    @function_tool
    async def get_lead_summary(self, context: RunContext) -> Dict[str, Any]:
        """Return a short one-line summary for the current lead in memory."""
        if not self.lead:
            return {"ok": False, "message": "No lead captured yet"}
        name = self.lead.get("name", "Unknown")
        company = self.lead.get("company", "Unknown")
        use_case = self.lead.get("use_case", "Not provided")
        timeline = self.lead.get("timeline", "Not provided")
        summary = f"{name} from {company}, interested in {use_case}. Timeline: {timeline}."
        return {"ok": True, "summary": summary}

    @function_tool
    async def save_lead(self, context: RunContext) -> Dict[str, Any]:
        """Persist the current lead to disk and return the saved record."""
        if not self.lead:
            return {"ok": False, "message": "No lead to save"}
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **self.lead
        }
        _append_lead(record)
        # clear current lead
        self.lead = {}
        return {"ok": True, "saved": record}
    
    @function_tool
    async def finalize_call(self, context: RunContext, user_text: str) -> Dict[str, Any]:
        """
        Called when the user says they are done (e.g. "that's all", "thanks", "I'm done").
        If email is missing, ask for it. Otherwise, save lead and return summary.
        """
        text = (user_text or "").lower()
        end_phrases = ["that's all", "that is all", "i'm done", "im done", "thanks", "thank you", "goodbye"]
        is_end = any(p in text for p in end_phrases)

        if not is_end:
            return {"ok": False, "message": "Not an end phrase."}

        # If we have no lead fields yet, nothing to save
        if not self.lead:
            return {"ok": False, "message": "No lead data captured."}

        # If email missing, ask for it before saving
        if not self.lead.get("email"):
            prompt = self.lead_schema.get("email", "What's the best email to reach you at?")
            return {"ok": False, "need_email": True, "prompt": prompt}

        # All required fields present: save the lead
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **self.lead
        }
        try:
            _append_lead(record)
            # clear current lead in memory
            self.lead = {}
            summary = f"Saved lead: {record.get('name','Unknown')} from {record.get('company','Unknown')} - {record.get('use_case','No use case')} (timeline: {record.get('timeline','N/A')})."
            return {"ok": True, "saved": record, "summary": summary}
        except Exception:
            logger.exception("Failed to save lead in finalize_call")
            return {"ok": False, "message": "Failed to save lead."}
    

    @function_tool
    async def check_missing_fields(self, context: RunContext) -> Dict[str, Any]:
        """Return a list of missing lead fields (keys)."""
        missing = [k for k in self.lead_schema.keys() if not str(self.lead.get(k, "")).strip()]
        return {"missing": missing}

    # Helper to ask missing fields; LLM can call this tool to prompt for the next missing field
    @function_tool
    async def next_lead_question(self, context: RunContext) -> Dict[str, Any]:
        for k, prompt in self.lead_schema.items():
            if k not in self.lead or not str(self.lead.get(k)).strip():
                return {"field": k, "prompt": prompt}
        return {"field": None, "prompt": "All done"}


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = SDRAgent()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(voice="en-US-matthew",
                     tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                     text_pacing=True),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    # Start session and connect
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
    )

    # Pre-load the FAQ at startup so the agent can use it quickly
    try:
        await agent.load_faq(None)
        logger.info("FAQ loaded for SDR agent")
    except Exception:
        logger.exception("Failed to load FAQ at startup")

    # Very small helper: if STT provides a final transcript, detect end call
    # (some platforms use 'user_input_transcribed' event; here we skip event wiring
    #  because the LLM / tools will check for phrases to finish the call)
    # Connect
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
