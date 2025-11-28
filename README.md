# Day 7 – Food & Grocery Ordering Voice Agent  
**Murf AI Voice Agent Challenge – Day 7 Submission**

## ✅ Overview
For Day 7, I built a **Food & Grocery Ordering Voice Assistant** that can understand what a user wants to buy, manage a cart, and finally place the order by writing it into a JSON file.

The goal was to design a natural, conversational ordering experience powered by:

- **Murf Falcon TTS** (Ultra-fast voice generation)
- **LiveKit Agents** (Voice pipeline)
- **Deepgram STT**
- **Google Gemini LLM**
- JSON-based catalog + order storage

---

## 📦 Features Implemented (MVP Requirements)

### **1. Catalog JSON**
Created a catalog file containing food & grocery items across categories:

- Groceries (bread, milk, eggs)
- Snacks (chips, biscuits)
- Meals (pizzas, sandwiches, pasta)
- Condiments (butter, peanut butter, sauces)

Each item includes:
- `name`
- `category`
- `price`
- `tags`
- `brand` (optional)
- `size` (optional)

---

### **2. Voice Ordering Assistant Persona**
The agent introduces itself as a friendly ordering assistant:

- Greets the user  
- Explains what it can do  
- Helps choose items and quantities  
- Clarifies brand, category, size when needed  
- Keeps the conversation natural and simple  

---

## 🛒 Cart Management
The agent maintains a persistent **cart**:

Supports:
- Adding items  
- Removing items  
- Updating quantity  
- Listing cart items  
- Confirming changes verbally  

Example commands:
```
Add two packs of milk
Remove bread
What’s in my cart?
Add chips
```

---

## 🥪 Intelligent Recipe Assistant
Agent can handle **recipe-based** or **ingredient-based** requests:

Examples:
- “Ingredients for a peanut butter sandwich”
- “Give me ingredients for pasta for two”
- “I want to make maggi”

Recipe mapping:
```json
{
  "peanut_butter_sandwich": ["bread", "peanut butter"],
  "pasta_two_people": ["pasta", "pasta sauce"],
  "maggi": ["maggi masala noodles"]
}
```

Agent automatically:
- Detects the intent  
- Adds all needed items to cart  
- Confirms verbally  

---

## 📄 Order Placement & JSON Storage
When user says:
- “Place my order”
- “That’s all”
- “I’m done”

The agent:
1. Reads the final cart  
2. Calculates total  
3. Creates an order JSON file  
4. Saves it to disk  
5. Confirms order placement  

Example:
```json
{
  "order_id": "order_001",
  "timestamp": "2025-02-19T14:28:11Z",
  "items": [
    { "name": "bread", "qty": 1, "price": 40 },
    { "name": "peanut butter", "qty": 1, "price": 160 }
  ],
  "total": 200
}
```

---

## 🗂 File Structure
```
backend/
  ├── catalog/
  │     └── day7_catalog.json
  ├── orders/
  │     └── order_001.json
  ├── src/
        └── agent.py

frontend/
  └── components/
        └── welcome-view.tsx
```

---

## 🛠 Tools Used
- Murf Falcon TTS  
- LiveKit Agents  
- Deepgram STT  
- Google Gemini 2.5 Flash  
- Next.js frontend  
- JSON for catalog + orders  

---

## ✅ MVP Checklist (Completed)
✔ Catalog JSON created  
✔ Adds/removes/updates cart items  
✔ Lists cart  
✔ Handles “ingredients for X”  
✔ Saves final order to JSON  
✔ Fully voice-controlled  

---

## 🎉 Conclusion
This ordering agent simulates a real quick-commerce workflow using natural conversation.  
Excited for Day 8!

#MurfAIVoiceAgentsChallenge  
#10DaysofAIVoiceAgents  
