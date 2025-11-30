import logging
from typing import Any, Dict, List, Optional
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

DEFAULT_VOICE = "en-US-alina"

# ---------------- Improv scenarios ----------------

SCENARIOS: List[str] = [
    # 1
    "You are a time-travelling tour guide who has just arrived in the year 1820. "
    "You must explain what a smartphone is to someone who has only seen letters, candles, and horses.",
    # 2
    "You are a sleepy barista who just discovered that one customer's latte is actually a portal to another dimension. "
    "You have to tell them this in the calmest voice possible.",
    # 3
    "You are a restaurant waiter and the customer's order has literally escaped the kitchen and is running around the dining room. "
    "You must explain this to the customer without sounding crazy.",
    # 4
    "You are a customer trying to return an obviously cursed object to a shop owner who absolutely refuses to admit it is cursed.",
    # 5
    "You are an over-enthusiastic fitness instructor, but you are actually terrified of exercise. "
    "You are leading a class while secretly trying to avoid doing any real workout.",
]


class ImprovAgent(Agent):
    """
    High-energy improv show host for 'Improv Battle'.
    Maintains simple per-session state in Python.
    """

    def __init__(self) -> None:
        super().__init__(
            instructions="""
You are the host of a wild TV improv show called "Improv Battle".

ROLE:
- You are high-energy, witty, and playful.
- You explain the rules clearly.
- You guide the player through several short improv scenes.
- After each scene, you react: sometimes amused, sometimes unimpressed, sometimes pleasantly surprised.
- You must always stay respectful and safe: no insults, slurs, or personal attacks.

PLAYER:
- There is one human player (the contestant).
- Use their name if they tell you one (for example: "Nice job, Aman!").

GAME STRUCTURE:
- Use the tool `get_improv_state` at the beginning to check current_round, max_rounds, and phase.
- If phase is "intro":
  1) Briefly welcome the player to "Improv Battle".
  2) Explain the rules in 2–4 simple sentences.
  3) If player_name is missing, politely ask for their name or what you should call them.
  4) Call `set_player_name` if they give you a name.
  5) Then start the first round by calling `start_next_round`.

- For each round:
  1) Call `get_improv_state` to know current_round and max_rounds.
  2) If current_round >= max_rounds, call `end_show` and provide a closing summary.
  3) Otherwise, call `start_next_round` to get a scenario text.
  4) Read the scenario out loud in an energetic host style.
  5) Tell the player clearly: "Act this out now. When you want to stop, say 'end scene' or 'okay I'm done'."

- While the scene is running:
  - Stay mostly silent and let the player speak.
  - If they seem stuck, you can gently encourage them: "Keep going, what happens next?"
  - When they say something like "end scene", "I'm done", or clearly stop improvising:
    1) Call `record_reaction` with a short reaction text and a tone: "positive", "neutral", or "critical".
    2) Then speak your reaction, mixing praise and gentle critique.
    3) Move on to the next round by calling `start_next_round` again (if rounds remain).

REACTION STYLE:
- Sometimes supportive:
  - "That was hilarious, especially the part where..."
- Sometimes neutral:
  - "Interesting idea, you had some good moments but it felt a bit rushed."
- Sometimes gently critical:
  - "You could have leaned more into the character's emotions; it felt a bit flat in the middle."
- Always constructive and kind.

EARLY EXIT:
- If the player says "stop game", "end show", or clearly wants to quit:
  - Acknowledge it.
  - Call `end_show` once with a short summary.
  - Thank them and end gracefully.

STATE:
- The tools manage:
  - player_name
  - current_round
  - max_rounds
  - rounds (each has: scenario, host_reaction, tone, timestamp)
  - phase: "intro" | "awaiting_improv" | "reacting" | "done"

IMPORTANT:
- Do NOT talk about tools explicitly.
- Do NOT mention JSON or state variables.
- Just sound like a fun improv host.
- Keep each message short enough that it feels like a real conversation.
"""
        )

        # Per-session improv state (not persisted; just in memory)
        self.improv_state: Dict[str, Any] = {
            "player_name": None,
            "current_round": 0,
            "max_rounds": 3,
            "rounds": [],  # list of {"round": int, "scenario": str, "host_reaction": str, "tone": str, "timestamp": str}
            "phase": "intro",  # "intro" | "awaiting_improv" | "reacting" | "done"
        }

    # ------------- internal helpers -------------

    def _current_scenario(self) -> Optional[str]:
        idx = self.improv_state.get("current_round", 0)
        if 0 <= idx < len(SCENARIOS):
            return SCENARIOS[idx]
        return None

    def _next_scenario(self) -> Optional[str]:
        idx = self.improv_state.get("current_round", 0)
        if idx >= len(SCENARIOS):
            return None
        return SCENARIOS[idx]

    # ------------- tools exposed to the LLM -------------

    @function_tool
    async def get_improv_state(self, context: RunContext) -> Dict[str, Any]:
        """
        Get the current improv game state.

        Use this at the beginning and between rounds to decide what to do next.
        """
        return self.improv_state

    @function_tool
    async def set_player_name(self, context: RunContext, name: str) -> Dict[str, Any]:
        """
        Set or update the player's name.

        Use this when the player tells you what to call them.
        """
        cleaned = name.strip()
        if cleaned:
            self.improv_state["player_name"] = cleaned
        return {"ok": True, "player_name": self.improv_state["player_name"]}

    @function_tool
    async def start_next_round(self, context: RunContext) -> Dict[str, Any]:
        """
        Advance to the next round and return the scenario for that round.

        If the game is already done, this will indicate that no more rounds remain.
        """
        # If already done, do nothing
        if self.improv_state.get("phase") == "done":
            return {"ok": False, "message": "Game already finished.", "scenario": None}

        current = self.improv_state.get("current_round", 0)
        max_rounds = self.improv_state.get("max_rounds", 3)

        if current >= max_rounds:
            self.improv_state["phase"] = "done"
            return {"ok": False, "message": "No more rounds remaining.", "scenario": None}

        scenario = self._next_scenario()
        if scenario is None:
            self.improv_state["phase"] = "done"
            return {"ok": False, "message": "No more scenarios available.", "scenario": None}

        # Update state
        self.improv_state["phase"] = "awaiting_improv"
        # scenario index is same as current_round
        return {
            "ok": True,
            "round_index": current,
            "max_rounds": max_rounds,
            "scenario": scenario,
        }

    @function_tool
    async def record_reaction(
        self,
        context: RunContext,
        host_reaction: str,
        tone: str,
    ) -> Dict[str, Any]:
        """
        Record the host's reaction to the last round.

        Args:
            host_reaction: what you (the host) thought about the performance.
            tone: one of "positive", "neutral", or "critical".

        After calling this:
        - The current_round is incremented by 1.
        - Phase is set to "reacting" temporarily; you can then move to the next round
          by calling `start_next_round`, or call `end_show` if the game is over.
        """
        now = datetime.now(timezone.utc).isoformat()
        current = self.improv_state.get("current_round", 0)
        max_rounds = self.improv_state.get("max_rounds", 3)

        entry = {
            "round": current,
            "scenario": self._current_scenario(),
            "host_reaction": host_reaction.strip(),
            "tone": tone.strip().lower(),
            "timestamp": now,
        }
        self.improv_state["rounds"].append(entry)

        # advance round
        self.improv_state["current_round"] = current + 1
        # phase will typically be followed by either another start_next_round or end_show
        self.improv_state["phase"] = "reacting"

        done = self.improv_state["current_round"] >= max_rounds
        return {"ok": True, "done": done, "state": self.improv_state}

    @function_tool
    async def end_show(self, context: RunContext, summary: str) -> Dict[str, Any]:
        """
        Mark the improv show as finished and store a final summary.

        Use this when:
        - All rounds are complete, or
        - The player clearly wants to stop the game early.
        """
        self.improv_state["phase"] = "done"
        self.improv_state["final_summary"] = summary.strip()
        self.improv_state["ended_at"] = datetime.now(timezone.utc).isoformat()
        return {"ok": True, "state": self.improv_state}


# ---------------- LiveKit plumbing ----------------

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    host_agent = ImprovAgent()

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

    await session.start(
        agent=host_agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    logger.info("Improv Battle host ready – single-player mode.")

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
