# Day 10 – Voice Improv Battle

This project implements a fully voice-driven improv game show powered by **LiveKit Agents**, **Gemini 2.5 Flash**, **Deepgram Nova-3**, and **Murf Falcon TTS**.

The agent becomes a high-energy game show host for a fictional show called **“Improv Battle”**, guiding the player through multiple improv scenarios, reacting to their performance, and summarizing the results at the end.

---

## 🎮 Concept

- Single-player improv game
- Player joins from the browser
- AI is the **host** of “Improv Battle”
- Each round:
  1. Host sets a scene
  2. Player improvises in character
  3. Host reacts (praise / neutral / mild critique)
  4. Game advances to the next round
- After a few rounds, the host gives a closing summary and ends the show

This is not a quiz or trivia game — it’s all about performance and creativity.

---

## 🧠 Backend: `ImprovAgent`

### File: `backend/src/agent.py`

The core logic is inside a custom agent class:

```python
class ImprovAgent(Agent):
    ...
```

### Improv State

The agent maintains a simple in-memory game state per session:

```python
improv_state = {
    "player_name": None,
    "current_round": 0,
    "max_rounds": 3,
    "rounds": [],  # each: {"round", "scenario", "host_reaction", "tone", "timestamp"}
    "phase": "intro",  # "intro" | "awaiting_improv" | "reacting" | "done"
}
```

- `player_name`: what the host calls the player (e.g., “Aman”)
- `current_round`: zero-based index of the current round
- `max_rounds`: total number of rounds (default 3)
- `rounds`: log of each scenario + reaction
- `phase`:
  - `intro`: host is welcoming and explaining rules
  - `awaiting_improv`: player should perform the scene
  - `reacting`: host is reacting to the previous scene
  - `done`: game finished

### Tools Exposed to the LLM

The agent exposes multiple tools so the LLM can explicitly manage game flow:

#### `get_improv_state`

Returns the current `improv_state` so the host can decide what to do next.

```python
@function_tool
async def get_improv_state(self, context: RunContext) -> Dict[str, Any]:
    return self.improv_state
```

#### `set_player_name`

Sets the player’s name based on what they say (“Call me Aman”, etc.).

```python
@function_tool
async def set_player_name(self, context: RunContext, name: str) -> Dict[str, Any]:
    ...
```

#### `start_next_round`

Advances to the next improv round and returns the scenario text.

```python
@function_tool
async def start_next_round(self, context: RunContext) -> Dict[str, Any]:
    ...
```

If no rounds remain, it marks the game as done.

#### `record_reaction`

After the player finishes a scene, the host calls this tool with a reaction and tone:

- `host_reaction`: what the host thought
- `tone`: `"positive"`, `"neutral"`, or `"critical"`

The tool:

- Appends a record to `rounds`
- Increments `current_round`
- Updates `phase`

#### `end_show`

Marks the game as finished and stores a final summary:

```python
@function_tool
async def end_show(self, context: RunContext, summary: str) -> Dict[str, Any]:
    ...
```

Used when all rounds are done or the player says “stop game” / “end show”.

---

## 🎭 Scenarios

A small list of pre-written improv scenarios is defined in code, for example:

```python
SCENARIOS = [
    "You are a time-travelling tour guide explaining smartphones to someone from 1820.",
    "You are a sleepy barista who has to calmly tell a customer that their latte is a portal to another dimension.",
    "You are a restaurant waiter whose customer's order has literally escaped the kitchen and is running around the dining room.",
    "You are a customer trying to return a clearly cursed object to a shop owner who refuses to admit it is cursed.",
    "You are an over-enthusiastic fitness instructor who is secretly terrified of exercise."
]
```

The host:

- Announces the scenario
- Tells the player to “act it out now”
- Waits for them to improvise
- Reacts when they say “end scene” or clearly finish

---

## 🗣️ Host Persona (System Prompt)

The system prompt defines:

- Role: TV show host of “Improv Battle”
- Tone: High-energy, witty, playful, but respectful
- Behaviour:
  - Explain rules
  - Use tools to manage rounds and state
  - Sometimes be very supportive
  - Sometimes slightly unimpressed / neutral
  - Sometimes mildly critical but always constructive
- Early exit: When user says “stop game” or “end show”, call `end_show` once and close gracefully

The host **never mentions tools or JSON**. It just sounds like a natural game show host.

---

## 🎧 Voice & Realtime Stack

The backend uses your existing Day 1–Day 9 voice stack:

- **STT**: Deepgram `nova-3`
- **LLM**: Google Gemini `2.5-flash`
- **TTS**: Murf Falcon (e.g. `en-US-matthew`)
- **Turn Detection**: `MultilingualModel`
- **VAD**: Silero
- **Noise Cancellation**: `noise_cancellation.BVC()`

Configured via:

```python
session = AgentSession(
    stt=deepgram.STT(model="nova-3"),
    llm=google.LLM(model="gemini-2.5-flash"),
    tts=murf.TTS(...),
    turn_detection=MultilingualModel(),
    vad=ctx.proc.userdata["vad"],
    preemptive_generation=True,
)
```

---

## 🖥️ Frontend: Join Screen

**File:** `frontend/components/app/welcome-view.tsx`

The welcome screen:

- Shows the show name (“Improv Battle”)
- Has a text field for **Name**
- Button: **“Start Improv Battle”**
- On click → calls `onStartCall()` (which starts the LiveKit session)

The name is mostly for UX; the backend also learns the name from what the user says (“Call me Aman”) using `set_player_name`.

---

## ▶️ How to Run

### 1. LiveKit Server

Make sure LiveKit server is running (in dev mode):

```bash
livekit-server --dev
```

### 2. Backend

From the `backend/` folder:

```bash
uv sync
cp .env.example .env.local   # if not already done
# Fill LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET,
# and keys for Murf, Gemini, Deepgram in .env.local

uv run python src/agent.py dev
```

### 3. Frontend

From the `frontend/` folder:

```bash
pnpm install
cp .env.example .env.local   # ensure LIVEKIT_URL etc. are set
pnpm dev
```

Then open:

```text
http://localhost:3000
```

Enter your name → click **Start Improv Battle** → the host will begin.

---

## 🎙️ Example Things to Say

During the game, try phrases like:

- “Okay, I’m ready. Give me the first scenario.”  
- (Then improvise in character)  
- “End scene.”  
- “Next round.”  
- “Stop game.” / “End show.”  

The host will:

- Introduce scenes  
- React to your performance  
- Track rounds  
- Give a final summary of your improv style (e.g., strong character work, good absurdity, emotional range, etc.)  

---

## ✅ What’s Done (Primary Goal)

- Single-player browser-based improv game ✅  
- Strong improv host persona ✅  
- Multiple scenarios with clear character prompts ✅  
- State tracking in Python ✅  
- Tools for_round progression and reactions ✅  
- Early exit handling ✅  
- Custom frontend join screen with Name input ✅  
- Full voice-only interaction loop ✅  

Day 10 of the Murf AI Voice Agent Challenge: **Complete.** 🎉
