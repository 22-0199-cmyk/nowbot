# NowBot — Real-Time Weather & Sports Chatbot

**Author:** Rawan AL-manthri 
**Hackathon:** GUTECH Career Fair 2026  
**Challenge:** NowBot (AI / Real-Time Data)  
**link:** https://github.com/22-0199-cmyk/nowbot/

---

## 🎯 Overview

A conversational assistant that answers questions about **live weather** and **sports news** using real APIs and Claude as the AI brain.

---

## 🚀 How to Run

### Option 1: Docker (Recommended)

```
# Build the Docker image
docker build -t nowbot .

# Run the container (create .env file first - see below)
docker run -p 5000:5000 --env-file .env nowbot
Then open: http://localhost:5000
```
Option 2: Python (Local)
```
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
Then open: http://localhost:5000
```
API Keys Required (Free)


|API|Purpose|Key needed?|
|-|-|-|
|[Open-Meteo](https://open-meteo.com)|Live weather worldwide|No|
|[NewsAPI](https://newsapi.org)|Live sports headlines|Yes (free tier)|
|[Nominatim](https://nominatim.openstreetmap.org)|City name → coordinates|No|
|[Anthropic Claude](https://anthropic.com)|Natural language answers|Yes|

\---


Set up your .env file (LOCAL only)
Create a file named .env in the project folder with:
NEWS_API_KEY=your_newsapi_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

|Question|What happens|
|-|-|
|`What's the weather in Tokyo?`|Fetches live Tokyo weather via Open-Meteo|
|`Is it hot in Muscat?`|Gets Muscat weather, Claude answers naturally|
|`Any NBA news?`|Fetches NewsAPI headlines filtered to NBA|
|`What about tomorrow?`|Remembers last city, handles follow-ups|
|`Should I bring an umbrella to London?`|Weather lookup + LLM interpretation|
|`Latest NFL scores?`|Sports headlines filtered to NFL|
---
Project Structure
```
nowbot/
├── app.py                # Level 3 — Flask server + /chat endpoint
├── nowbot.py             # Level 1 — CLI chatbot
├── nowbot\_level2.py      # Level 2 — CLI chatbot with memory + city detection
├── templates/
│   └── index.html        # Chat UI
├── weather\_demo.py       # Standalone weather API test
├── sports\_demo.py        # Standalone NewsAPI test
├── Dockerfile
├── requirements.txt
├── .gitignore
└── README.md
----------
```
## Features by level

\---

## Features by level

**Level 1** — both APIs connected, keyword routing, Claude answers using only live data

**Level 2** — any city worldwide via geocoding, sport filtering (NBA/NFL/soccer/etc.), conversation memory, follow-up questions

**Level 3** — full web chat UI, animated loading indicator, source attribution on every answer, session memory, graceful error handling


\---

## Features by level

**Level 1** — both APIs connected, keyword routing, Claude answers using only live data

**Level 2** — any city worldwide via geocoding, sport filtering (NBA/NFL/soccer/etc.), conversation memory, follow-up questions

**Level 3** — full web chat UI, animated loading indicator, source attribution on every answer, session memory, graceful error 

