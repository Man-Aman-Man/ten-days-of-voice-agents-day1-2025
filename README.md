# Day 6 – Fraud Alert Voice Agent 🛡️📞

This is my submission for **Day 6** of the **Murf AI Voice Agents Challenge**.

The goal for today was to build a **Fraud Alert Voice Agent** that behaves like a bank’s fraud department, using only **fake/demo data**, and updates a simple “database” after each call.

---

## 🎯 Objective

Build a voice agent that:

- Loads a suspicious transaction from a small database (JSON file)
- Introduces itself as the fraud department of a fictional bank
- Verifies the user with a basic, non-sensitive security question
- Reads out the suspicious transaction
- Asks if the customer made the transaction (yes/no)
- Marks the case as **safe** or **fraudulent** (or **verification failed**)
- Writes the final status and outcome summary back to the database

Everything runs in the in-app voice environment using the existing LiveKit + Murf frontend.

---

## 🏦 Fictional Bank & Data

I created a fictional bank called **SafeBank** and a JSON “database” of fraud cases:

**File**: `backend/shared_data/day6_fraud_cases.json`

Each case looks like:

```json
{
  "id": "case_001",
  "userName": "John",
  "securityIdentifier": "12345",
  "cardEnding": "4242",
  "transactionAmount": "₹7,999",
  "transactionName": "ABC Online Mart",
  "transactionTime": "2025-02-20 19:42",
  "transactionCategory": "e-commerce",
  "transactionSource": "abc-onlinemart.com",
  "transactionLocation": "Mumbai, India",
  "securityQuestion": "What is your favorite color?",
  "securityAnswer": "blue",
  "status": "pending_review",
  "outcomeNote": ""
}
```

### ⚠️ All data is fake
No real card numbers, PINs, passwords, or sensitive fields are used.

## 🧠 Agent Behavior (Fraud Call Flow)

The FraudAgent runs inside LiveKit’s AgentSession and follows a structured flow:
1. Greeting & Introduction
  - Introduces as SafeBank’s fraud detection department.
  - Explains that a suspicious transaction was detected.
2. Customer Identification
  - Asks for the caller’s first name.
  - Uses a tool to select a case from the JSON DB where:
    - userName matches the name
    - status == pending_review
  - If no case is found, politely informs the user and ends the call.
3. Safe Verification
  - Uses a non-sensitive security question from the case:
    - e.g. “What is your favorite color?”
  - Calls a tool to verify the answer (simple lowercase string match).
  - If verification fails:
    - Explains that the bank cannot proceed further
    - Marks the case as verification_failed
    - Ends the call.

4. Suspicious Transaction Review
  - On successful verification:
    - Calls a tool to fetch transaction details from the case:
    - Merchant name
    - Amount
    - Masked card ending
    - Time
    - Location
  - Reads these details slowly and clearly.
  - Asks: “Did you make this transaction?”

5. Decision (Safe or Fraudulent)
- If user confirms the transaction:
  - Marks case as confirmed_safe
  - Writes an outcome note like:
   - “Customer confirmed the transaction as legitimate.”
- If user denies:
  - Marks case as confirmed_fraud
  - Writes an outcome note like:
   - “Customer denied transaction. Card should be blocked and dispute raised. (demo only)”

6. Wrap-up & Persistence
- Gives a short summary of what happened.
- Thanks the user and ends the call.
- Updated case (status, outcomeNote, timestamp) is written back to:
 - backend/shared_data/day6_fraud_cases.json

### 🛠️ Tools Implemented

The agent uses several function tools:

- load_fraud_cases
 Load all cases from the JSON DB into memory.

- select_case_for_user(first_name)
Find the first case with pending_review for the given userName.

- get_security_question()
Returns the pre-set harmless security question.

- verify_security_answer(answer)
Compares the answer (case-insensitive) with the stored security answer.

- get_transaction_details()
Returns merchant, amount, time, location, and masked card info for TTS readout.

- mark_case_status(status, note)
Updates:
  - status → confirmed_safe / confirmed_fraud / verification_failed
  - outcomeNote
  - lastUpdated
And writes back to the JSON DB.

### 🧬 Tech Stack
- Voice Engine: LiveKit Agents
- LLM: Google Gemini (Flash)
- STT: Deepgram (nova-3)
- TTS: Murf Falcon (en-US-matthew)
- VAD & Turn Detection: Silero + Multilingual turn detector
- Database: Local JSON file (day6_fraud_cases.json)

**▶️ How to Run**

Start LiveKit server (if not already running):
```
livekit-server --dev
```
Backend (Fraud Agent):
```
cd backend
uv run python src/agent.py dev
```
Frontend:
```
cd frontend
pnpm install   # if not installed yet
pnpm dev
```
Open the app in your browser (usually http://localhost:3000) and start a session.

### 🧪 Test Flow

Try saying:
1. “Hi” → Agent introduces as SafeBank fraud department.
2. Give a name matching the fake DB:
 - “John” or “Priya”
3. Answer the security question correctly (e.g. “blue”).
4. Listen to the suspicious transaction read out.

**Answer:**
 - “Yes, that was me.” → case becomes confirmed_safe
 - or “No, I did not.” → case becomes confirmed_fraud
Verify the case update in:
 - backend/shared_data/day6_fraud_cases.json
