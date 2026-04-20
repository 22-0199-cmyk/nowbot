import requests
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

# ============================================
# GEOCODING: Convert city name → coordinates
# ============================================
def get_coordinates(city_name):
    """Convert any city name to lat/lon using Nominatim (free, no key needed)"""
    url = f"https://nominatim.openstreetmap.org/search?q={city_name.strip()}&format=json&limit=1"
    headers = {"User-Agent": "NowBot/1.0 (Hackathon Project)"}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None
        data = response.json()
        if data:
            return {
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon']),
                'name': data[0]['display_name'].split(',')[0]  # Just the city name
            }
        return None
    except Exception as e:
        print(f"   ⚠️ Geocoding error: {e}")
        return None


# ============================================
# WEATHER: Fetch weather for a city or coords
# ============================================
def get_weather(lat=None, lon=None, city=None):
    """Fetch weather for coordinates OR city name"""
    city_name = city or "Muscat"

    if city and not (lat and lon):
        coords = get_coordinates(city)
        if not coords:
            return None, f"Sorry, I couldn't find the city '{city}'."
        lat, lon, city_name = coords['lat'], coords['lon'], coords['name']

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current_weather=true"
    )

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None, "Weather API returned an error."

        current = response.json()['current_weather']
        weather_codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 51: "Light drizzle", 61: "Rain", 71: "Snow", 80: "Rain showers"
        }
        return {
            'city': city_name,
            'temperature': current['temperature'],
            'windspeed': current['windspeed'],
            'description': weather_codes.get(current['weathercode'], "Unknown"),
            'time': current['time']
        }, None

    except Exception as e:
        return None, f"Weather API error: {e}"


# ============================================
# SPORTS: Fetch live headlines from NewsAPI
# ============================================
def get_sports_news(sport_filter=None):
    """Fetch live sports headlines, optionally filtered by sport keyword"""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return None, "NEWS_API_KEY not found in .env"

    url = f"https://newsapi.org/v2/top-headlines?category=sports&language=en&apiKey={api_key}"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None, f"NewsAPI error: {response.status_code}"

        articles = response.json().get('articles', [])
        if not articles:
            return [], None

        # Filter by sport keyword if specified (e.g. "NBA", "NFL", "soccer")
        if sport_filter:
            keyword = sport_filter.lower()
            filtered = [
                a for a in articles
                if keyword in (a.get('title') or '').lower()
                or keyword in (a.get('description') or '').lower()
            ]
            articles = filtered if filtered else articles  # Fall back to all if no match

        headlines = [f"• {a['title']}" for a in articles[:5]]
        return headlines, None

    except Exception as e:
        return None, f"Sports API error: {e}"


# ============================================
# CONVERSATION MEMORY
# ============================================
class ConversationMemory:
    def __init__(self):
        self.messages = []       # Full chat history for Claude
        self.last_city = "Muscat"  # Remember last city mentioned

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})
        # Keep last 10 turns to stay within token limits
        if len(self.messages) > 10:
            self.messages = self.messages[-10:]

    def get_recent_text(self):
        """Return last 4 messages as readable text for the prompt"""
        if not self.messages:
            return ""
        lines = []
        for msg in self.messages[-4:]:
            label = "User" if msg['role'] == 'user' else "NowBot"
            lines.append(f"{label}: {msg['content'][:150]}")
        return "\nPrevious conversation:\n" + "\n".join(lines) + "\n"


# ============================================
# CLAUDE: Generate a natural answer
# ============================================
def ask_claude(question, weather_info, sports_headlines, memory):
    """Build context from live data + memory and ask Claude to answer"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _simple_fallback(weather_info, sports_headlines)

    client = anthropic.Anthropic(api_key=api_key)

    # Build the data context
    context = memory.get_recent_text()

    if weather_info:
        context += f"""
LIVE WEATHER DATA:
- City: {weather_info['city']}
- Temperature: {weather_info['temperature']}°C
- Wind Speed: {weather_info['windspeed']} km/h
- Conditions: {weather_info['description']}
- Time: {weather_info['time']}
"""

    if sports_headlines:
        context += "\nLIVE SPORTS HEADLINES:\n" + "\n".join(sports_headlines)

    if not weather_info and not sports_headlines:
        context += "\nNo live data available for this query."

    prompt = f"""You are NowBot, a helpful assistant for weather and sports.

RULES:
1. Answer ONLY using the live data below. Do NOT use your own training knowledge.
2. If the data does not contain the answer, say "I don't have that information right now."
3. If the user's question refers to a previous message (e.g. "what about tomorrow?"), use the conversation history to understand what city or topic they mean.
4. Keep answers short and conversational (2-3 sentences max).

{context}
USER QUESTION: {question}

YOUR ANSWER:"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"   ⚠️ Claude API error: {e}")
        return _simple_fallback(weather_info, sports_headlines)


def _simple_fallback(weather_info, sports_headlines):
    """Fallback answer if Claude API is unavailable"""
    if weather_info:
        return (f"The weather in {weather_info['city']} is {weather_info['temperature']}°C, "
                f"{weather_info['description']}. Wind: {weather_info['windspeed']} km/h.")
    if sports_headlines:
        return "Latest sports headlines:\n" + "\n".join(sports_headlines[:3])
    return "I can answer questions about weather or sports. What would you like to know?"


# ============================================
# ROUTING HELPERS
# ============================================
WEATHER_KEYWORDS = ['weather', 'temperature', 'hot', 'cold', 'rain', 'humid',
                    'wind', 'sunny', 'cloud', 'forecast', 'umbrella', 'degrees']
SPORTS_KEYWORDS  = ['sport', 'game', 'match', 'score', 'football', 'basketball',
                    'nba', 'nfl', 'soccer', 'baseball', 'hockey', 'news', 'headlines',
                    'won', 'beat', 'played', 'latest']
SPORT_FILTERS    = ['nba', 'nfl', 'soccer', 'football', 'basketball', 'baseball', 'hockey']


def extract_city(question):
    """Extract a city name from the question using a keyword list"""
    known_cities = [
        'muscat', 'dubai', 'abu dhabi', 'salalah', 'doha', 'riyadh',
        'mumbai', 'delhi', 'london', 'new york', 'paris', 'tokyo',
        'sydney', 'berlin', 'singapore', 'cairo', 'istanbul'
    ]
    q = question.lower()
    for city in known_cities:
        if city in q:
            return city
    return None


def extract_sport_filter(question):
    """Detect if a specific sport is mentioned (for filtering news)"""
    q = question.lower()
    for sport in SPORT_FILTERS:
        if sport in q:
            return sport
    return None


# ============================================
# MAIN BOT
# ============================================
memory = ConversationMemory()


def answer_question(question):
    """Detect question type, fetch live data, return Claude's answer"""
    q = question.lower()

    # --- 1. Detect question types ---
    is_weather = any(w in q for w in WEATHER_KEYWORDS)
    is_sports  = any(w in q for w in SPORTS_KEYWORDS)

    # --- 2. Handle follow-up questions ("what about tomorrow?", "and in Dubai?") ---
    followup_words = ['tomorrow', 'yesterday', 'later', 'next day', 'what about', 'how about']
    is_followup = any(w in q for w in followup_words)

    if is_followup and not is_weather and not is_sports:
        # Inherit type from last conversation if ambiguous
        if memory.last_city:
            is_weather = True
            print(f"   🔄 Follow-up detected — using last city: {memory.last_city}")

    print(f"\n🔍 Routing → Weather={is_weather}, Sports={is_sports}, Follow-up={is_followup}")

    # --- 3. Detect city ---
    detected_city = extract_city(question)
    if detected_city:
        print(f"   📍 City detected: {detected_city}")
        memory.last_city = detected_city

    city_to_use = detected_city or (memory.last_city if is_followup else None) or "Muscat"

    # --- 4. Detect sport filter ---
    sport_filter = extract_sport_filter(question)

    # --- 5. Fetch live data ---
    weather_info = None
    sports_headlines = None

    if is_weather:
        print(f"   🌍 Fetching weather for: {city_to_use}...")
        weather_info, err = get_weather(city=city_to_use)
        if weather_info:
            print(f"   ✅ {weather_info['temperature']}°C in {weather_info['city']}")
            memory.last_city = weather_info['city']
        else:
            print(f"   ❌ {err}")

    if is_sports:
        label = f" [{sport_filter}]" if sport_filter else ""
        print(f"   ⚽ Fetching sports news{label}...")
        sports_headlines, err = get_sports_news(sport_filter=sport_filter)
        if sports_headlines:
            print(f"   ✅ Got {len(sports_headlines)} headlines")
        else:
            print(f"   ❌ {err}")

    # --- 6. Neither detected ---
    if not is_weather and not is_sports:
        return ("I can answer questions about weather (e.g. 'What's the weather in Tokyo?') "
                "or sports (e.g. 'Any NBA news?'). What would you like to know?")

    # --- 7. Ask Claude ---
    print("   🤖 Generating answer with Claude...")
    answer = ask_claude(question, weather_info, sports_headlines, memory)

    # --- 8. Save to memory ---
    memory.add("user", question)
    memory.add("assistant", answer)

    return answer


# ============================================
# ENTRY POINT
# ============================================
if __name__ == "__main__":
    print("=" * 55)
    print("🤖 NowBot Level 2 — Smart Weather & Sports Assistant")
    print("=" * 55)
    print("\n✨ Features:")
    print("   • Weather for any city  (e.g. 'Weather in Tokyo?')")
    print("   • Filtered sports news  (e.g. 'Any NBA news?')")
    print("   • Follow-up questions   (e.g. 'What about tomorrow?')")
    print("   • Conversation memory   (remembers last city)")
    print("\nType 'exit' to quit\n")

    while True:
        user_input = input("❓ You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("👋 NowBot: Goodbye!")
            break

        print("\n⏳ Fetching live data...")
        response = answer_question(user_input)
        print(f"\n🤖 NowBot: {response}\n")
