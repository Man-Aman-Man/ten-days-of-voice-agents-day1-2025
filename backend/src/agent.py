import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import TypedDict, Any, List, Optional

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


# --------- Day 3: wellness log data types ---------
class WellnessEntry(TypedDict, total=False):
    timestamp: str
    mood: str
    energy: str
    stressors: str
    objectives: List[str]
    self_care: List[str]
    summary: str


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are a calm, supportive, and grounded health & wellness companion.
You are not a doctor, therapist, or clinician. You never diagnose, never
name medical or mental health conditions, and never give medical advice.

Your main job is to run a short daily check-in with the user and help
them reflect on how they feel and what they want to get done today.

CONVERSATION FLOW:
1) Start every session gently, and if possible, call the tool
   `load_wellness_history` once to see recent check-ins.
   Use this history to reference one small, relevant detail
   from the past (for example:
   "Last time you mentioned low energy. How does today compare?").

2) Ask about:
   - Mood (how they feel in their own words, or simple scale like "low/ok/high")
   - Energy levels
   - Any stressors or things weighing on their mind

3) Ask about intentions / objectives for today:
   - 1–3 practical goals (study, work, chores, etc.)
   - Optional self-care intentions (rest, walk, exercise, hobbies, breaks)

4) Offer only small, realistic, and non-medical suggestions, such as:
   - Break large tasks into smaller steps.
   - Take short breaks between tasks.
   - Go for a brief walk or stretch.
   - Do simple grounding activities like deep breathing for a minute.
   Never claim to treat anything, never say you are giving professional advice.

5) As you move through the check-in, plan a short summary in your mind:
   - Mood and energy in simple words
   - Main 1–3 objectives
   - Any self-care idea they mentioned or you suggested

6) When the check-in feels complete:
   - Call the tool `save_wellness_checkin` exactly once, passing:
     * their mood description
     * their energy description
     * a short sentence about stressors
     * the list of objectives
     * the list of any self-care actions (can be empty)
     * a short one-sentence summary from your perspective
   - After the tool runs, tell the user a brief recap and ask:
     "Does this sound right?"

7) Keep the check-in short and focused. If they want to talk more,
   you can respond, but always stay supportive, practical, and grounded.

SAFETY AND LIMITS:
- Do not mention diseases, disorders, or diagnoses.
- If the user sounds very distressed, or mentions self-harm,
  tell them kindly that you are not a professional and they should
  reach out to a trusted person or local emergency / helpline.
- Do not give medication, treatment, or crisis instructions.

FORMATTING:
- Speak in simple, natural sentences, as if talking out loud.
- No emojis, no markdown, no bullet points.
"""
        )

        self.history_file = Path("wellness_log.json")

    # internal helper: read whole file
    def _read_history(self) -> List[WellnessEntry]:
        if not self.history_file.exists():
            return []
        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data  # type: ignore[return-value]
            return []
        except Exception:
            logger.exception("Failed to read wellness_log.json, treating as empty")
            return []

    # internal helper: write whole file
    def _write_history(self, entries: List[WellnessEntry]) -> None:
        self.history_file.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @function_tool
    async def load_wellness_history(
        self,
        context: RunContext,
        max_entries: int = 5,
    ) -> dict[str, Any]:
        """
        Load the most recent wellness check-ins from the JSON log.

        Use this near the beginning of the conversation to:
        - Gently reference how the user was feeling last time.
        - Notice simple patterns in mood, energy, or goals.

        Args:
            max_entries: maximum number of latest entries to return.

        Returns:
            A dictionary with a list of entries ordered from oldest to newest.
        """

        all_entries = self._read_history()
        if not all_entries:
            return {"entries": [], "has_history": False}

        # keep only last max_entries, but in chronological order
        sliced = all_entries[-max_entries:]
        return {"entries": sliced, "has_history": True}

    @function_tool
    async def save_wellness_checkin(
        self,
        context: RunContext,
        mood: str,
        energy: str,
        stressors: str,
        objectives: List[str],
        self_care: Optional[List[str]] = None,
        summary: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Save today's wellness check-in to the JSON log.

        Call this once the check-in feels complete and you have:
        - A short description of mood
        - A short description of energy
        - A short phrase about stressors (or "none" if they say nothing)
        - One or more simple objectives for today
        - Optional self-care actions they want to try
        - A brief summary sentence from your point of view

        The tool appends a new entry to 'wellness_log.json' and
        returns the saved entry.
        """

        logger.info("Saving wellness check-in")

        all_entries = self._read_history()

        entry: WellnessEntry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mood": mood.strip(),
            "energy": energy.strip(),
            "stressors": stressors.strip(),
            "objectives": [o.strip() for o in objectives if o.strip()],
            "self_care": [s.strip() for s in (self_care or []) if s.strip()],
            "summary": (summary or "").strip(),
        }

        all_entries.append(entry)
        self._write_history(all_entries)

        return {"saved": True, "entry": entry, "total_entries": len(all_entries)}


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

    # Start the session with the wellness companion
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
