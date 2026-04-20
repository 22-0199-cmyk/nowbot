# NowBot — Real-Time Weather \& Sports Chatbot
**Author:** Rawan Al-Manthri 
**Hackathon:** GUTECH Career Fair 2026  
**Challenge:** NowBot (AI / Real-Time Data)  
**GitHub:** https://github.com/22-0199-cmyk/nowbot
##overview
A conversational assistant that answers questions about **live weather** and **sports news** using real APIs and Claude as the AI brain.

### Option 1: Docker (Recommended)

```bash
# Build the Docker image
docker build -t nowbot .

# Create a .env file with your API keys (see below)
# Then run the container
docker run -p 5000:5000 --env-file .env nowbot


// go to the browser and open : http://localhost:5000

```
###option 2: Python (local)
# Install dependencies
pip install -r requirements.txt

# Create .env file with your keys
echo "NEWS_API_KEY=your_key_here" > .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env

# Run the app
python app.py

## Example questions

|Question|What happens|
|-|-|
|`What's the weather in Tokyo?`|Fetches live Tokyo weather via Open-Meteo|
|`Is it hot in Muscat?`|Gets Muscat weather, Claude answers naturally|
|`Any NBA news?`|Fetches NewsAPI headlines filtered to NBA|
|`What about tomorrow?`|Remembers last city, handles follow-ups|
|`Should I bring an umbrella to London?`|Weather lookup + LLM interpretation|
|`Latest NFL scores?`|Sports headlines filtered to NFL|

\---

## Project structure

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

## APIs used

|API|Purpose|Key needed?|
|-|-|-|
|[Open-Meteo](https://open-meteo.com)|Live weather worldwide|No|
|[NewsAPI](https://newsapi.org)|Live sports headlines|Yes (free tier)|
|[Nominatim](https://nominatim.openstreetmap.org)|City name → coordinates|No|
|[Anthropic Claude](https://anthropic.com)|Natural language answers|Yes|

\---

## Features by level

**Level 1** — both APIs connected, keyword routing, Claude answers using only live data

**Level 2** — any city worldwide via geocoding, sport filtering (NBA/NFL/soccer/etc.), conversation memory, follow-up questions

**Level 3** — full web chat UI, animated loading indicator, source attribution on every answer, session memory, graceful error handling

