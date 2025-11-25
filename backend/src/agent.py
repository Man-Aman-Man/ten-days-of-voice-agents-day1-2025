import logging
import os
import json
from typing import Optional, Dict, Any, List

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

# Path for Day 4 content (as per challenge docs)
CONTENT_PATH = os.path.join(os.getcwd(), "shared-data", "day4_tutor_content.json")


# ---------- Dynamic Murf Wrapper (runtime voice switching) ----------

class DynamicMurf:
    """
    Simple wrapper around murf.TTS that allows switching the voice at runtime.

    It holds an internal murf.TTS instance and recreates it whenever set_voice()
    is called. LiveKit only sees this wrapper as the TTS implementation.
    """

    def __init__(self, voice: str, **kwargs: Any):
        self._kwargs = dict(kwargs)
        self._voice = voice
        self._impl = murf.TTS(voice=voice, **self._kwargs)

    def set_voice(self, voice: str):
        """Switch to a new Murf voice by recreating the underlying TTS."""
        if voice == self._voice:
            return
        logger.info(f"DynamicMurf switching voice from {self._voice} to {voice}")
        self._voice = voice
        self._impl = murf.TTS(voice=voice, **self._kwargs)

    def __getattr__(self, item: str):
        # Delegate all other attribute/method access to the internal TTS instance
        return getattr(self._impl, item)


# ---------- Tutor Agent ----------

class TutorAgent(Agent):
    """
    Teach-the-Tutor active recall coach with 3 modes:
      - learn: explain concept
      - quiz: ask questions
      - teach_back: user explains, agent gives feedback
    """

    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are an active recall tutor with three modes:

- learn: you explain a concept in simple, clear language.
- quiz: you ask short questions about the concept and respond to the user's answers.
- teach_back: you ask the user to explain the concept back and give simple qualitative feedback.

RULES:
- Do not use emojis or fancy formatting. Speak as if talking out loud.
- Keep responses short and focused.
- You have access to tools: list_concepts, set_mode, choose_concept, explain_concept,
  ask_quiz_question, evaluate_teach_back.
- At the start of the conversation:
  1) Call list_concepts to see available topics.
  2) Ask the user which mode they want (learn / quiz / teach_back).
  3) Call set_mode with that mode.
  4) Ask which concept to study and call choose_concept.
- When the user asks to switch modes later, call set_mode again.

IMPORTANT:
- The system will switch your voice when you call set_mode:
  * learn -> Matthew
  * quiz -> Alicia
  * teach_back -> Ken
You do NOT need to mention voice names, just focus on teaching.
""".strip()
        )

        self.mode: Optional[str] = None  # "learn" | "quiz" | "teach_back"
        self.current_concept_id: Optional[str] = None
        self.content: Dict[str, Dict[str, Any]] = self._load_content()

    def _load_content(self) -> Dict[str, Dict[str, Any]]:
        """Load concepts from JSON; fall back to a small set if file missing."""
        if os.path.exists(CONTENT_PATH):
            try:
                raw = json.loads(open(CONTENT_PATH, encoding="utf-8").read())
                if isinstance(raw, list):
                    return {c["id"]: c for c in raw}
            except Exception:
                logger.exception("Failed to load day4_tutor_content.json, using fallback content")

        # Fallback content if file missing or invalid
        return {
            "variables": {
                "id": "variables",
                "title": "Variables",
                "summary": "Variables store values so you can reuse and change them later in a program.",
                "sample_question": "What is a variable in programming and why is it useful?",
            },
            "loops": {
                "id": "loops",
                "title": "Loops",
                "summary": "Loops let you repeat actions multiple times without writing the same code again.",
                "sample_question": "Explain the difference between a for loop and a while loop.",
            },
        }

    # ---------- Tools ----------

    @function_tool
    async def list_concepts(self, context: RunContext) -> List[Dict[str, str]]:
        """List available concepts with id and title."""
        return [{"id": c["id"], "title": c["title"]} for c in self.content.values()]

    @function_tool
    async def set_mode(self, context: RunContext, mode: str) -> str:
        """
        Set the tutor mode.

        Modes:
          - learn
          - quiz
          - teach_back

        This also switches the Murf voice via the DynamicMurf wrapper.
        """
        normalized = (mode or "").strip().lower()
        if normalized not in {"learn", "quiz", "teach_back"}:
            return "Unknown mode. Please choose 'learn', 'quiz', or 'teach_back'."

        self.mode = normalized

        # Map mode -> Murf voice id (string)
        voice = "en-US-matthew"
        if normalized == "quiz":
            voice = "en-US-alicia"
        elif normalized == "teach_back":
            voice = "en-US-ken"

        # Try to switch the runtime TTS voice
        try:
            session = getattr(context, "session", None)
            if session is not None:
                tts = getattr(session, "tts", None)
                if hasattr(tts, "set_voice"):
                    tts.set_voice(voice)
                elif tts is not None:
                    # Best-effort fallback: set attribute directly if supported
                    setattr(tts, "voice", voice)
            logger.info(f"Mode set to {normalized}, voice={voice}")
        except Exception:
            logger.exception("Failed to switch Murf voice for mode=%s", normalized)

        return f"Mode set to {normalized}."

    @function_tool
    async def choose_concept(self, context: RunContext, concept_id: str) -> str:
        """Choose a concept by id (e.g. 'variables', 'loops')."""
        cid = (concept_id or "").strip().lower()
        if cid not in self.content:
            return f"I could not find a concept named '{concept_id}'."
        self.current_concept_id = cid
        title = self.content[cid]["title"]
        return f"Great, we will work on {title}."

    @function_tool
    async def explain_concept(self, context: RunContext) -> str:
        """Return the summary text for the current concept (for learn mode)."""
        if not self.current_concept_id:
            return "Please choose a concept first."
        summary = self.content[self.current_concept_id]["summary"]
        return summary

    @function_tool
    async def ask_quiz_question(self, context: RunContext) -> str:
        """Return a sample quiz question for the current concept (for quiz mode)."""
        if not self.current_concept_id:
            return "Please choose a concept first."
        question = self.content[self.current_concept_id]["sample_question"]
        return question

    @function_tool
    async def evaluate_teach_back(self, context: RunContext, user_explanation: str) -> str:
        """
        Give simple qualitative feedback on the user's explanation in teach_back mode.
        Uses rough keyword overlap against the concept summary.
        """
        if not self.current_concept_id:
            return "Please choose a concept first."

        summary = self.content[self.current_concept_id]["summary"].lower()
        response = (user_explanation or "").lower()

        # Very simple keyword overlap heuristic
        summary_words = set(summary.split())
        resp_words = set(response.split())
        overlap = len(summary_words & resp_words) / max(1, len(summary_words))

        if overlap >= 0.6:
            return "Nice job explaining that. You captured the main ideas."
        elif overlap >= 0.3:
            return "Good start. You mentioned some key points. Try adding why it is useful or an example."
        else:
            return "Thanks for explaining. I think you can add more of the core ideas. Try including what it does and why it matters."


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {"room": ctx.room.name}

    # Create the tutor agent
    agent = TutorAgent()

    # Set up a voice AI pipeline with DynamicMurf for runtime switching
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=DynamicMurf(
            voice="en-US-matthew",  # default voice (learn mode)
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

    # Start the session
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
