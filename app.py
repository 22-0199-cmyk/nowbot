"""
NowBot Level 3 - Web Chat UI with Flask
Requirements:
✅ Flask backend with /chat endpoint
✅ HTML chat interface
✅ Loading spinner
✅ Source attribution
✅ Error handling
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

app = Flask(__name__)
CORS(app)

# Session memory: stores per-session chat history and last city
# (keyed by a simple session ID passed from the frontend)
_sessions = {}

def get_session(session_id):
    if session_id not in _sessions:
        _sessions[session_id] = {'messages': [], 'last_city': 'Muscat'}
    return _sessions[session_id]

# ============================================
# Copy your existing bot functions here
# ============================================

def get_coordinates(city_name):
    """Convert any city name to lat/lon"""
    url = f"https://nominatim.openstreetmap.org/search?q={city_name.strip()}&format=json&limit=1"
    headers = {"User-Agent": "NowBot/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None
        data = response.json()
        if data:
            return {
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon']),
                'name': data[0]['display_name'].split(',')[0]
            }
        return None
    except Exception:
        return None

def get_weather(city):
    """Fetch weather for any city"""
    coords = get_coordinates(city)
    if not coords:
        return None, f"Could not find city: {city}"
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None, "Weather API error"
        
        current = response.json()['current_weather']
        weather_codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 51: "Light drizzle", 61: "Rain", 71: "Snow", 80: "Rain showers"
        }
        
        return {
            'city': coords['name'],
            'temperature': current['temperature'],
            'windspeed': current['windspeed'],
            'description': weather_codes.get(current['weathercode'], "Unknown"),
            'source': 'Open-Meteo Weather API'
        }, None
    except Exception as e:
        return None, f"Weather error: {e}"

def get_sports_news():
    """Fetch live sports headlines"""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return None, "NewsAPI key missing"
    
    url = f"https://newsapi.org/v2/top-headlines?category=sports&language=en&apiKey={api_key}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None, f"NewsAPI error: {response.status_code}"
        
        articles = response.json().get('articles', [])
        if not articles:
            return [], None
        
        headlines = [f"• {a['title']}" for a in articles[:5]]
        return {
            'headlines': headlines,
            'source': 'NewsAPI'
        }, None
    except Exception as e:
        return None, f"Sports error: {e}"

def extract_city(question):
    """
    Extract city name from question using Claude, then verify it exists via Nominatim.
    This handles ANY city — not just a hardcoded list.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _extract_city_fallback(question)

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=30,
            messages=[{
                "role": "user",
                "content": (
                    f"Extract the city or location name from this question. "
                    f"Reply with ONLY the city name, nothing else. "
                    f"If no city is mentioned, reply with NONE.\n\nQuestion: {question}"
                )
            }]
        )
        city = response.content[0].text.strip()
        if city.upper() == "NONE" or not city:
            return None
        # Verify the city actually exists via Nominatim
        coords = get_coordinates(city)
        return city if coords else None
    except Exception:
        return _extract_city_fallback(question)


def _extract_city_fallback(question):
    """Fallback: match against a small list if Claude is unavailable"""
    known = ['muscat', 'dubai', 'london', 'paris', 'tokyo', 'new york',
             'salalah', 'mumbai', 'delhi', 'singapore', 'sydney', 'doha',
             'riyadh', 'cairo', 'istanbul', 'berlin', 'abu dhabi']
    q = question.lower()
    for city in known:
        if city in q:
            return city.title()
    return None

def detect_type(question):
    """Detect if weather or sports question"""
    q = question.lower()
    weather_words = ['weather', 'temperature', 'hot', 'cold', 'rain', 'wind', 'sunny']
    sports_words = ['sport', 'game', 'match', 'score', 'football', 'basketball', 'nba', 'nfl']
    
    is_weather = any(w in q for w in weather_words)
    is_sports = any(w in q for w in sports_words)
    
    return is_weather, is_sports

def get_answer(question, weather_info, sports_info, history=None):
    """Generate answer using Claude or fallback"""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return fallback_answer(weather_info, sports_info)

    client = anthropic.Anthropic(api_key=api_key)

    context = ""
    if history:
        recent = history[-4:]
        context += "Previous conversation:\n"
        for m in recent:
            label = "User" if m['role'] == 'user' else "NowBot"
            context += f"{label}: {m['content'][:120]}\n"
        context += "\n"

    if weather_info:
        context += f"Weather in {weather_info['city']}: {weather_info['temperature']}°C, {weather_info['description']}, wind {weather_info['windspeed']} km/h.\n"
    if sports_info:
        context += f"Sports headlines: {' '.join(sports_info['headlines'][:3])}\n"

    prompt = f"""You are NowBot. Answer using ONLY the data below. Keep it short (2-3 sentences).
Do NOT use your training knowledge. If the data doesn't answer the question, say so.

{context}
QUESTION: {question}

ANSWER:"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception:
        return fallback_answer(weather_info, sports_info)

def fallback_answer(weather_info, sports_info):
    """Simple fallback answer"""
    if weather_info:
        return f"The weather in {weather_info['city']} is {weather_info['temperature']}°C with {weather_info['description']}. Wind: {weather_info['windspeed']} km/h."
    if sports_info:
        return f"Latest sports: {' '.join(sports_info['headlines'][:2])}"
    return "Ask me about weather or sports!"

# ============================================
# Flask Routes
# ============================================

@app.route('/')
def index():
    """Serve the chat HTML page"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.get_json()
    question = data.get('message', '')
    session_id = data.get('session_id', 'default')

    if not question:
        return jsonify({'error': 'No message provided'}), 400

    session = get_session(session_id)

    # Detect question type
    is_weather, is_sports = detect_type(question)

    # Handle follow-up (e.g. "what about tomorrow?")
    followup_words = ['tomorrow', 'yesterday', 'what about', 'how about', 'later', 'next day']
    is_followup = any(w in question.lower() for w in followup_words)
    if is_followup and not is_weather and not is_sports:
        is_weather = True  # assume weather follow-up if we have a last city

    # Extract city — uses LLM for any city name, not just a hardcoded list
    city = extract_city(question)
    if city:
        session['last_city'] = city
    city = city or (session['last_city'] if is_followup else None) or 'Muscat'

    # Fetch data
    weather_info = None
    sports_info = None
    source = None

    if is_weather:
        weather_info, error = get_weather(city)
        if weather_info:
            source = weather_info['source']
            session['last_city'] = weather_info['city']
        else:
            return jsonify({'error': error or 'Could not fetch weather'}), 500

    if is_sports:
        sports_info, error = get_sports_news()
        if sports_info:
            source = (source + ' + ' if source else '') + sports_info['source']
        else:
            return jsonify({'error': error or 'Could not fetch sports news'}), 500

    if not is_weather and not is_sports:
        answer = "I can answer about weather (e.g., 'Weather in Dubai') or sports (e.g., 'Sports news')"
        source = "NowBot Guide"
    else:
        answer = get_answer(question, weather_info, sports_info, session['messages'])

    # Save to memory
    session['messages'].append({"role": "user", "content": question})
    session['messages'].append({"role": "assistant", "content": answer})
    if len(session['messages']) > 10:
        session['messages'] = session['messages'][-10:]

    return jsonify({
        'answer': answer,
        'source': source or 'Live Data',
        'weather': weather_info,
        'sports': sports_info
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)