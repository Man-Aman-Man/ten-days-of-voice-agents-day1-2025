# Day 3 – Health & Wellness Voice Companion  
Built for the **Murf AI Voice Agent Challenge**  
Using **LiveKit Agents + Murf Falcon TTS + Deepgram STT**

## Overview
This project implements a **Health & Wellness Voice Companion** that performs **daily voice-based check-ins**, stores the user's wellbeing data, and references past conversations.

It is powered by:
- **LiveKit Realtime Agents**
- **Murf Falcon (Fastest TTS API)**
- **Deepgram Speech-to-Text**
- A custom **PharmEasy-themed frontend**

---

## Features Implemented (Day 3 Requirements)

### Clear System Persona  
The agent acts as a **supportive, grounded wellness companion**—not a medical advisor.

### Mood & Energy Check-In  
It begins each session with questions like:
- “How are you feeling today?”
- “How’s your energy level?”
- “Anything stressing you out?”

### Daily Goal Setting  
It guides the user to set:
- 1–3 small objectives  
- Personal self-care intentions  

### Realistic & Grounded Advice  
The AI offers small, practical actions:
- Break tasks into smaller steps  
- Take short breaks  
- 5-minute walk suggestions  

No medical or diagnostic claims.

### JSON-Based Persistence  
After each check-in:
- A new entry is written to **wellness_log.json**
- Includes: date, mood, goals, summary

### Reads Past Data  
On the next session, it references history:
> “Yesterday you mentioned feeling low on energy — how does today compare?”

### Frontend Customization  
A custom **PharmEasy wellness UI** with:
- Brand color palette (#10847E, #1BAF92, #DFF5F3)
- Friendly wellness tone
- Clean and simple check-in interface

---

## JSON Storage Format  
Example entry:

```json
{
  "timestamp": "2025-01-23T10:00:00",
  "mood": "Feeling tired but okay",
  "energy": "Low",
  "stress": "Work pressure",
  "goals": ["Complete a presentation", "Go for a walk"],
  "self_care": "Drink more water",
  "summary": "User felt low energy but wants to focus on productivity with small steps."
}
```

## How to Run Locally
Install Requirements

- Backend:

``` bash
uv sync
uv run python agent.py
```

- Frontend:

``` bash
pnpm install
pnpm dev
```

## Tech Stack

- LiveKit Realtime Agents
- Murf Falcon TTS
- Deepgram STT
- Next.js Frontend (PharmEasy Theme)
- Python Backend with State Persistence

## Challenge Notes

This completes Day 3 – Primary Goal of the Murf AI Voice Agent Challenge.
