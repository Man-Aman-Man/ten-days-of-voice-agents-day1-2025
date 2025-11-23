## AI Voice Barista Agent – Day 2

This repository contains my implementation for Day 2 of the Murf AI Voice Agent Challenge.
The goal for this stage was to transform the starter voice agent into a fully conversational Coffee Shop Barista capable of taking voice-based orders.

**Day 2 Features Implemented:**

**1. Barista Persona**

The agent now has a friendly, welcoming barista-style personality. All responses are crafted to sound like a real coffee shop employee.

**2. Order State Management**

The agent maintains and updates a structured order object while speaking with the user:

```
json 
{
  "drinkType": "string",
  "size": "string",
  "milk": "string",
  "extras": ["string"],
  "name": "string"
}
```

The agent asks clarifying questions until all fields are collected.

**3. Voice-Driven Ordering Flow**


- Takes the user’s order through voice.
- Asks follow-up questions if details are missing.
- Confirms the full order before finalizing.


**4. Order Persistence (Saved as JSON)**


Whenever an order is completed, it is saved inside:
/orders/<timestamp>.json

Example:

```
json
{
  "name": "Aarav",
  "drinkType": "Latte",
  "size": "Medium",
  "milk": "Oat Milk",
  "extras": ["Extra Shot"]
}
```

**Frontend Customization**

For Day 2, the frontend has been visually rebranded to match Café Coffee Day styling:

- Updated color palette
- Updated welcome screen
- Custom start button & UI elements
- Cleaner layout for the call interface
- Tech Stack
- LiveKit Agents
- Murf Falcon TTS
- Deepgram ASR
- Next.js (Frontend)
- Node.js (Backend Tools)

**Branch Information**

All Day 2 work has been pushed to:
- day-2-barista-agent

## Challenge

This work is a part of the **Murf AI Voice Agent Challenge – Day 2**, where participants build and evolve a fully functional AI voice agent over 10 days.
