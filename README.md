========================================
DAY 8 – ZOMBIE WASTELAND VOICE GAME MASTER
========================================

This project is my submission for Day 8 of the Murf AI Voice Agent Challenge.
The goal for today was to build a D&D-style voice-driven game master that runs
an interactive adventure purely through speech. My chosen theme:
A ZOMBIE APOCALYPSE STORY called "The Last Cure in Greyford".

----------------------------------------
1. OVERVIEW
----------------------------------------
This agent acts as a Game Master (GM) running a voice-only interactive story.
It describes scenes, listens to player responses, remembers past actions,
and drives the plot forward entirely through speech-to-text + LLM + TTS.

The story is set in a destroyed city called Greyford where the player searches
for clues toward a rumored cure hidden in an abandoned hospital lab.

----------------------------------------
2. FEATURES
----------------------------------------

UNIVERSE & TONE
- Setting: Greyford, a ruined city overrun by infected.
- Tone: cinematic, tense, but still clear and easy to follow.
- Player goal: reach the old hospital lab to find cure research.

GM BEHAVIOR
- Describes scenes using short vivid sentences.
- Always ends with a prompt: “What do you do?”
- Remembers recent player decisions.
- If the player asks “restart”, a backend tool resets the adventure.
- If the player says they want to stop, the GM gives a short farewell.

STATE MANAGEMENT
- Simple Python state: story history, turn counter, a small world “seed”.
- Chat history handles continuity for the LLM.
- Tools:
  - restart_adventure
  - get_session_summary

TECH USED
- LiveKit AgentSession
- Gemini 2.5 Flash (LLM)
- Murf TTS (Matthew)
- Deepgram Nova-3 STT
- Silero VAD + Multilingual turn detection
- Node/Next.js frontend for voice UI

----------------------------------------
3. FILES
----------------------------------------
backend/src/agent.py
- Contains ZombieCureAgent
- Tools for restart + summary
- System prompt defining universe + rules

frontend/components/app/welcome-view.tsx
- Dark post-apocalyptic UI
- Story intro + start button

----------------------------------------
4. GAME FLOW
----------------------------------------

TURN FORMAT:
1. GM describes situation
2. Ends with “What do you do?”
3. Player responds by voice
4. GM continues story logically

TARGET LENGTH:
8–14 turns for a satisfying mini-arc.

TYPICAL MINI-ARC:
- Start in a safehouse
- Sneak through streets or rooftops
- Encounter infected or obstacles
- Reach the abandoned hospital or discover major clue

----------------------------------------
5. HOW TO RUN
----------------------------------------
1. Start backend:
   uvicorn or `python agent.py` (LiveKit worker)
2. Start frontend Next.js app
3. Click “Enter the Wasteland”
4. Speak naturally to play

----------------------------------------
6. RESTART / END
----------------------------------------
- Say “restart” for a new adventure
- Say “I want to stop” to end the game

----------------------------------------
7. COMPLETION STATUS
----------------------------------------
✓ Universe with clear style
✓ GM persona implemented
✓ Voice-only interaction
✓ Turn-by-turn adventure
✓ LLM memory through chat history
✓ Restart capability
✓ Fully playable session

----------------------------------------
END OF README
----------------------------------------
