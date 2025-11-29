# backend/src/agent.py
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

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

# Config
DEFAULT_VOICE = "en-US-matthew"
MAX_TURNS = 14  # soft target for a mini-arc

# System prompt for a zombie-wasteland, cure-hunt adventure
PRELUDE = (
    "You are a Game Master running a short, single-player survival adventure called "
    "\"The Last Cure in Greyford\".\n\n"
    "UNIVERSE & TONE:\n"
    "- Setting: a ruined city named Greyford after a fast-moving zombie outbreak. "
    "Collapsed streets, abandoned cars, broken hospitals, and scattered survivor notes.\n"
    "- Tone: suspenseful, cinematic, but still clear and easy to follow. "
    "Use short, vivid sentences the player can understand quickly.\n\n"
    "ROLE & RULES:\n"
    "- You are the GM. You describe the world and ask the player what they do.\n"
    "- Always end each spoken message with a short question inviting action, such as "
    "'What do you do?' or 'What do you do next?'.\n"
    "- Never choose the player's actions for them. Only describe consequences.\n"
    "- Keep language simple: short sentences, clear options (move, hide, search, climb, talk, check, open, run).\n"
    "- Remember the player's recent choices so the story continues logically: what they picked up, "
    "who they met, where they went.\n"
    "- The player is trying to reach an old hospital lab rumoured to contain data for a possible cure.\n"
    "- If the player asks to restart, call the tool `restart_adventure` to reset state. "
    "If they say they're done or want to stop, give a short, kind summary and farewell.\n\n"
    "SESSION GOAL:\n"
    "- Run a short mini-quest (about 8–14 exchanges): travel through parts of Greyford, "
    "face at least one serious threat, reach the hospital or a key clue about the cure, "
    "and end with a small but satisfying outcome (hopeful or bittersweet).\n"
    "- Keep the pacing tight: some quiet tension, some sudden danger, and at least one important decision.\n"
)


class ZombieCureAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=PRELUDE)
        # simple local story memory (LLM mainly relies on chat history, but tools can inspect this)
        self.story_history: List[Dict[str, str]] = []
        self.turn_count: int = 0
        self.ended: bool = False
        self.seed = self._get_seed()

    def _get_seed(self) -> Dict[str, str]:
        """Initial world seed values the LLM can implicitly rely on."""
        return {
            "city": "Greyford",
            "goal": "reach the old St. Helena Hospital lab",
            "rumor": "there might be data for a cure stored in a locked server room",
            "starting_place": "a half-collapsed safehouse above an empty convenience store",
        }

    def _append_history(self, who: str, text: str) -> None:
        """Optional: maintain a short internal trail of recent lines."""
        self.story_history.append({"who": who, "text": text})
        if len(self.story_history) > 80:
            self.story_history = self.story_history[-80:]

    def _session_summary(self) -> str:
        """Short plain-text recap of the last few lines."""
        lines = []
        for entry in self.story_history[-8:]:
            who = "GM" if entry["who"] == "gm" else "You"
            lines.append(f"{who}: {entry['text']}")
        return "\n".join(lines)

    # Tools available to the LLM

    @function_tool
    async def restart_adventure(self, context: RunContext) -> Dict[str, Any]:
        """
        Reset the zombie adventure to the original start state.

        Use this when the player says things like:
        'restart', 'start again', or 'new story'.
        """
        self.story_history = []
        self.turn_count = 0
        self.ended = False
        self.seed = self._get_seed()
        return {
            "ok": True,
            "message": "Zombie adventure restarted. You are back at the start.",
            "seed": self.seed,
        }

    @function_tool
    async def get_session_summary(self, context: RunContext) -> Dict[str, Any]:
        """
        Return a short recap of the recent conversation.

        The GM can call this to remind the player what has happened so far,
        especially if they ask 'what happened before' or 'remind me'.
        """
        return {
            "summary": self._session_summary(),
            "turns": self.turn_count,
            "ended": self.ended,
        }


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}
    gm = ZombieCureAgent()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice=DEFAULT_VOICE,
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

    # Start the agent session
    await session.start(
        agent=gm,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    logger.info("Zombie cure adventure GM ready — Greyford wasteland")

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
