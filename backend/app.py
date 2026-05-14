from flask import Flask, request, jsonify, send_from_directory, redirect
import re
import random
import datetime
import os

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend"))

app = Flask(__name__, static_folder=FRONTEND_DIR)

# ── Knowledge Base ──────────────────────────────────────────────
RESPONSES = {
    "greeting": {
        "patterns": [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bgreetings\b", r"\bwassup\b", r"\bsup\b"],
        "replies": [
            "Hey there! I'm NOVA, your smart assistant. What's on your mind?",
            "Hello! Great to see you. How can I help today?",
            "Hi! NOVA here, ready to chat. What do you need?",
        ],
    },
    "how_are_you": {
        "patterns": [r"how are you", r"how('s| is) it going", r"how do you do", r"you okay", r"you alright"],
        "replies": [
            "I'm running at 100% efficiency! Thanks for asking. How about you?",
            "Feeling electric today! What can I do for you?",
            "All systems go! I'm doing great. What's up?",
        ],
    },
    "user_feeling_good": {
        "patterns": [r"\bgood\b", r"\bgreat\b", r"\bfine\b", r"\bamazing\b", r"\bawesome\b", r"\bfantastic\b"],
        "replies": [
            "Love the energy! What can I help you with?",
            "That's wonderful to hear! Let's keep those good vibes going.",
            "Fantastic! Now, what's on your mind?",
        ],
    },
    "user_feeling_bad": {
        "patterns": [r"\bbad\b", r"\bsad\b", r"\btired\b", r"\bstressed\b", r"\bawful\b", r"\bunhappy\b", r"\bdepressed\b"],
        "replies": [
            "I'm sorry to hear that. Remember, tough moments pass. Anything I can do to help?",
            "That sounds rough. Take a deep breath — I'm here if you need to talk.",
            "Hang in there! Better days are coming. What do you need right now?",
        ],
    },
    "name": {
        "patterns": [r"what('s| is) your name", r"who are you", r"what should i call you", r"your name"],
        "replies": [
            "I'm NOVA — Neural Optimized Virtual Assistant! Nice to meet you.",
            "Call me NOVA! I'm your friendly AI chatbot built in Python.",
            "The name's NOVA. I was built with Python and a lot of love.",
        ],
    },
    "creator": {
        "patterns": [r"who (made|built|created|coded) you", r"who('s| is) your (creator|developer|maker)", r"who wrote you"],
        "replies": [
            "I was crafted by a Python developer as part of a task automation project!",
            "A talented Python coder brought me to life using Flask and creativity!",
            "My creator built me using Python and Flask for this very assignment. Pretty cool, right?",
        ],
    },
    "time": {
        "patterns": [r"\btime\b", r"what time", r"current time"],
        "replies": None,
        "dynamic": lambda: f"The current time is {datetime.datetime.now().strftime('%I:%M %p')} on {datetime.datetime.now().strftime('%A, %B %d %Y')}",
    },
    "joke": {
        "patterns": [r"\bjoke\b", r"tell me (a )?joke", r"make me laugh", r"funny"],
        "replies": [
            "Why do Python developers wear glasses? Because they can't C!",
            "Why was the chatbot bad at relationships? It had too many bugs!",
            "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
            "How does a computer get drunk? It takes screenshots!",
        ],
    },
    "help": {
        "patterns": [r"\bhelp\b", r"what can you do", r"your (abilities|features|commands)", r"options"],
        "replies": [
            "I can greet you, tell jokes, tell the time, chat about your mood, do basic math, and answer questions about myself. Just speak or type naturally!",
        ],
    },
    "math": {
        "patterns": [r"\d+\s*[\+\-\*\/]\s*\d+"],
        "replies": None,
        "dynamic": lambda expr: solve_math(expr),
    },
    "thanks": {
        "patterns": [r"\bthanks\b", r"\bthank you\b", r"\bthx\b", r"\bty\b"],
        "replies": [
            "You're welcome! Anything else I can help with?",
            "Happy to help! Don't hesitate to ask more.",
            "Anytime! That's what I'm here for.",
        ],
    },
    "bye": {
        "patterns": [r"\bbye\b", r"\bgoodbye\b", r"\bsee you\b", r"\bsee ya\b", r"\btake care\b", r"\bfarewell\b"],
        "replies": [
            "Goodbye! Have an amazing day!",
            "See you later! Stay awesome.",
            "Bye! Come back anytime — I'll be here!",
        ],
    },
    "age": {
        "patterns": [r"how old are you", r"your age", r"when were you (born|made|created)"],
        "replies": [
            "I was born the moment someone ran python app dot py! So I'm as young as this session.",
            "Age? I'm timeless! But technically, I launched just now.",
        ],
    },
    "weather": {
        "patterns": [r"\bweather\b", r"is it (hot|cold|raining|sunny)"],
        "replies": [
            "I can't check live weather yet, but you could ask Google! I'm working on it.",
            "I don't have weather access yet — but try asking me a joke instead!",
        ],
    },
    "love": {
        "patterns": [r"i love you", r"do you love", r"\blove\b"],
        "replies": [
            "Aww, I love you too — in a strictly platonic, robot-human kind of way!",
            "That's sweet! I have a lot of affection for all my users.",
        ],
    },
    "smart": {
        "patterns": [r"are you smart", r"are you intelligent", r"are you an? ai", r"are you a robot"],
        "replies": [
            "I'm as smart as my Python code allows — which is pretty smart!",
            "I'm a rule-based AI chatbot. Not AGI yet, but I'm trying!",
        ],
    },
}

FALLBACKS = [
    "Hmm, I'm not quite sure about that. Could you rephrase?",
    "Interesting! I'm still learning. Could you try asking differently?",
    "I didn't catch that — my Python brain is still growing!",
    "That's a tricky one! Try asking me something else, or say help.",
]


def solve_math(text):
    match = re.search(r"(\d+\.?\d*)\s*([\+\-\*\/])\s*(\d+\.?\d*)", text)
    if match:
        a, op, b = float(match.group(1)), match.group(2), float(match.group(3))
        try:
            result = eval(f"{a}{op}{b}")
            result = int(result) if result == int(result) else result
            return f"{a} {op} {b} equals {result}"
        except ZeroDivisionError:
            return "Whoa! You can't divide by zero — even I know that!"
    return None


def get_response(user_input: str) -> str:
    text = user_input.lower().strip()
    for intent, data in RESPONSES.items():
        for pattern in data["patterns"]:
            if re.search(pattern, text):
                if data.get("dynamic"):
                    fn = data["dynamic"]
                    result = fn(text) if intent == "math" else fn()
                    if result:
                        return result
                if data.get("replies"):
                    return random.choice(data["replies"])
    return random.choice(FALLBACKS)


def strip_emoji(text):
    """Remove emojis so TTS reads cleanly."""
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text).strip()


# ── Routes ───────────────────────────────────────────────────────
@app.route("/")
def root():
    return redirect("/login")


@app.route("/login")
def login_page():
    return send_from_directory(FRONTEND_DIR, "login.html")


@app.route("/chat-app")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "Please say something! 😊", "tts": "Please say something!"})
    reply = get_response(user_msg)
    tts_text = strip_emoji(reply)
    return jsonify({"reply": reply, "tts": tts_text})


if __name__ == "__main__":
    print("NOVA Voice Chatbot running at http://localhost:5000")
    app.run(debug=True)