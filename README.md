# ✅ Day 5 – SDR Voice Agent (Sales Development Representative)
## Murf AI Voice Agents Challenge — Day 5 Submission
### 📌 Overview

**On Day 5, the task was to build a Voice-based SDR (Sales Development Representative) capable of:**

- Answering product and company FAQs
- Guiding users through basic information
- Asking natural follow-up questions
- Capturing potential customer leads
- Saving the structured lead details in a JSON file
- Detecting end-of-call to provide a final summary

**This project uses:**

- LiveKit Agents
- Murf Falcon TTS (ultra-fast voice generation)
- Deepgram STT
- Gemini Flash (LLM)
- Custom persona + tool functions

### 🧠 What This SDR Agent Does
**1. Behaves like a real SDR
The agent has a custom-designed persona for a company (Freshworks in my version).**

It can:

- Greet professionally
- Ask what the user is looking for
- Redirect the discussion to product needs
- Build understanding of the user’s requirements

**2. Answers FAQs using a JSON file
A day5_freshworks_faq.json file contains:**

- Company intro
- Product features
- Pricing basics
- Target customers

### Benefits

- The agent performs simple keyword matching to choose the best FAQ answer.
- No hallucinations — only responses based on actual content.

**3. Lead Capture Flow
During conversation, the agent collects:**

```
Name
Company
Email
Role
Use case
Team size
Buying timeline (now / soon / later)
```

**All captured data is stored in:**

```
backend/leads/day5_leads.json
```

Well-structured and append-based.

**4. End-of-call Detection
When user says:**

```
“That’s all”
“I’m done”
“Thanks, that’s it”
```

**The agent:**
- Generates a verbal lead summary
- Saves the final lead to JSON
- Ends the session gracefully

📂 Project Structure

```
backend/
 ├── src/
 │   ├── agent.py                 # Main SDR agent logic
 │   ├── faq_loader.py            # Preprocessing + keyword matching
 │   └── lead_storage.py          # Lead capture + JSON persistence
 ├── leads/
 │   └── day5_leads.json          # Generated automatically
 └── shared-data/
     └── day5_freshworks_faq.json # FAQ Knowledge Base
```

```
frontend/
 ├── components/
 │   └── welcome-view.tsx         # Custom SDR UI (Freshworks theme)
 └── app/
     └── view-controller.tsx      # Session + mode initialization
```

### 🎯 SDR Persona (Prompt Summary)

**The assistant:**

- Sounds like a professional sales teammate
- Avoids long answers
- Never gives medical/legal claims
- Stays aligned with Freshworks’ actual content
- Redirects user to product-fit questions
- Slowly collects lead info in natural conversation
- Confirms details before saving

**🔍 Inside the FAQ Engine**

- A lightweight keyword-matching system:
- Splits user question
- Ranks FAQ paragraphs by keyword overlap
- Returns the most relevant match
- Used for "what do you do", “pricing?”, “who is this for”, “features?”, etc.
- No embedding/semantic search needed for Day 5.

## 📝 Lead JSON Structure

Each completed lead is stored as:
```
{
  "timestamp": "2025-02-21T14:12:22Z",
  "name": "John Doe",
  "company": "Acme Ltd",
  "email": "john@example.com",
  "role": "Product Manager",
  "use_case": "CRM automation",
  "team_size": "15",
  "timeline": "soon",
  "notes": "User asked about pricing and integrations."
}
```

### 🗣 Voices & Technical Stack
-Component	Tech Used
- TTS	Murf Falcon (Matthew – SDR tone)
- STT	Deepgram Nova-3
- LLM	Google Gemini Flash
- VAD	Silero
- Turn Detection	Multilingual Turn Detector
- Orchestration	LiveKit AgentSession

### 🚀 How to Run Locally
1. Start Backend
```
cd backend
uv run src/agent.py
```

2. Start Frontend
```
cd frontend
npm install
npm run dev
```

3. Set your .env.local
```
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```
