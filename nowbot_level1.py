import requests
import os
from dotenv import load_dotenv
import anthropic

# Load API keys from .env
load_dotenv()

# ============================================
# STEP 1: Weather function (from your working code)
# ============================================
def get_weather(lat, lon):
    """Fetch current weather for any location"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    response = requests.get(url)
    
    if response.status_code != 200:
        return None
    
    weather_data = response.json()
    current = weather_data['current_weather']
    
    weather_codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 51: "Light drizzle", 61: "Rain", 71: "Snow", 80: "Rain showers"
    }
    
    description = weather_codes.get(current['weathercode'], "Unknown")
    
    return {
        'temperature': current['temperature'],
        'windspeed': current['windspeed'],
        'description': description,
        'time': current['time']
    }

# ============================================
# STEP 2: Sports function (from your working code)
# ============================================
def get_sports_news():
    """Fetch live sports headlines"""
    api_key = os.getenv("NEWS_API_KEY")
    
    if not api_key:
        return None
    
    url = f"https://newsapi.org/v2/top-headlines?category=sports&language=en&apiKey={api_key}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return None
    
    news_data = response.json()
    articles = news_data.get('articles', [])
    
    if not articles:
        return []
    
    # Return top 3 headlines as simple text
    headlines = []
    for article in articles[:3]:
        headlines.append(f"- {article['title']}")
    
    return headlines

# ============================================
# STEP 3: Claude-powered answer
# ============================================
def ask_claude(question, weather_data, sports_headlines):
    """Send question + data to Claude for a natural answer"""
    
    # Get Claude API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        return "⚠️ ANTHROPIC_API_KEY not found in .env file. Please add it to use Claude."
    
    # Initialize Claude client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Build the context (data Claude can use)
    context = ""
    
    if weather_data:
        context += f"""
WEATHER DATA:
- Temperature: {weather_data['temperature']}°C
- Wind Speed: {weather_data['windspeed']} km/h
- Conditions: {weather_data['description']}
- Time: {weather_data['time']}
"""
    
    if sports_headlines:
        context += "\nSPORTS NEWS HEADLINES:\n" + "\n".join(sports_headlines)
    
    if not weather_data and not sports_headlines:
        context = "No data available for this query."
    
    # Claude prompt - tells it to ONLY use the data above
    prompt = f"""You are NowBot, a helpful assistant that answers questions about weather and sports.

Answer the user's question using ONLY the data provided below. 
Do NOT use your training knowledge. If the data doesn't contain the answer, say "I don't have that information from the live data."

DATA:
{context}

USER QUESTION: {question}

YOUR ANSWER (natural, conversational, 1-2 sentences):"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",  # Fastest, cheapest model
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ Claude API error: {str(e)[:100]}"

# ============================================
# MAIN BOT: Detect question type and respond
# ============================================
def answer_question(question):
    """Main function - routes question to right API, then to Claude"""
    
    question_lower = question.lower()
    
    # Detect if asking about weather
    weather_keywords = ['weather', 'temperature', 'hot', 'cold', 'rain', 'humid', 'wind']
    is_weather = any(word in question_lower for word in weather_keywords)
    
    # Detect if asking about sports
    sports_keywords = ['sport', 'game', 'match', 'score', 'football', 'basketball', 'nba', 'nfl', 'soccer', 'baseball', 'hockey']
    is_sports = any(word in question_lower for word in sports_keywords)
    
    print(f"\n🔍 Detected: Weather={is_weather}, Sports={is_sports}")
    
    # Get data based on detection
    weather_data = None
    sports_headlines = None
    
    if is_weather:
        print("🌍 Fetching weather data...")
        # Muscat coordinates (hardcoded for Level 1)
        weather_data = get_weather(23.5880, 58.3829)
        if weather_data:
            print(f"   ✅ Got weather: {weather_data['temperature']}°C")
        else:
            print("   ❌ Weather API failed")
    
    if is_sports:
        print("⚽ Fetching sports news...")
        sports_headlines = get_sports_news()
        if sports_headlines:
            print(f"   ✅ Got {len(sports_headlines)} headlines")
        else:
            print("   ❌ Sports API failed")
    
    # If neither detected, ask for clarification
    if not is_weather and not is_sports:
        return "I can answer questions about weather (temperature, rain, wind) or sports (games, scores, headlines). What would you like to know?"
    
    # Send to Claude for natural answer
    print("🤖 Asking Claude to write answer...")
    answer = ask_claude(question, weather_data, sports_headlines)
    
    return answer

# ============================================
# RUN THE BOT (command-line for Level 1/2)
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 NowBot - Your Weather & Sports Assistant")
    print("=" * 50)
    print("\nType 'exit' to quit\n")
    
    while True:
        user_input = input("❓ You: ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("👋 NowBot: Goodbye!")
            break
        
        if user_input.strip():
            print("\n⏳ Thinking...")
            response = answer_question(user_input)
            print(f"\n🤖 NowBot: {response}\n")