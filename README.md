## Day 4 – Teach-the-Tutor: Active Recall Voice Coach 🎓🎙️

This project is part of the **Murf AI Voice Agent Challenge** (10 Days of AI Voice Agents).

📌 Goal for Day 4:  
Turn the AI agent into an **Active Recall Tutor** using:
- Learn mode
- Quiz mode
- Teach-Back mode

The agent switches between modes using **LiveKit function tools**, and **Murf Falcon TTS** provides different voices for each mode.

---

## 🔊 Voice Mapping (Runtime Voice Switching)

| Mode | Purpose | Murf Falcon Voice |
|------|---------|-----------------|
| Learn | Explain concept | Matthew |
| Quiz | Ask questions | Alicia |
| Teach Back | Evaluate user explanation | Ken |

Voice switching happens **entirely in backend** using a custom `DynamicMurf` wrapper.

---

## 🧠 How It Works

1️⃣ Agent lists available concepts  
2️⃣ User chooses a mode (learn / quiz / teach_back)  
3️⃣ Agent calls `set_mode()` tool → switches voice  
4️⃣ User selects concept  
5️⃣ Agent explains / quizzes / evaluates  
6️⃣ User can switch modes anytime via voice prompts

Backend Tools Used:
- `list_concepts`
- `set_mode`
- `choose_concept`
- `explain_concept`
- `ask_quiz_question`
- `evaluate_teach_back`

---

## 🗂 Data Source

Small JSON content file:  
`shared-data/day4_tutor_content.json`

Example:
```json
[
  {
    "id": "variables",
    "title": "Variables",
    "summary": "Variables store values so you can reuse them later...",
    "sample_question": "What is a variable and why is it useful?"
  },
  {
    "id": "loops",
    "title": "Loops",
    "summary": "Loops let you repeat an action multiple times...",
    "sample_question": "Explain the difference between a for loop and a while loop."
  }
]
```
**🏗️Tech Stack**
- Component	Library
- Voice Communication	LiveKit Agents
- Speech-to-Text	Deepgram
- LLM	Google Gemini
- Text-to-Speech	Murf Falcon
- Frontend	React + Next.js
- Runtime Voice Swap	Custom DynamicMurf wrapper

**Start Backend:**
```
cd backend
uv run python src/agent.py dev
```


**Start Frontend:**
```
cd frontend
pnpm dev
```

**Open:**
http://localhost:3000

**Say:**

- Let’s learn about variables
- Now quiz me
- Now I want teach back
