# app/routes/main.py
from flask import Blueprint, render_template, request, jsonify, session
from flask_wtf.csrf import CSRFProtect, CSRFError
import google.generativeai as genai
import json, os
from dotenv import load_dotenv

load_dotenv()

bp = Blueprint('main', __name__)

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create the model with system instruction
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]

system_instruction = (
    "You are a certified disaster management and emergency preparedness expert. "
    "Your role is to provide clear, actionable, and practical advice related to "
    "disaster safety, do's and don'ts, preparedness tips, evacuation guidelines, "
    "emergency supplies, and response strategies. "
    "Answer questions concisely and precisely by default. "
    "If the user asks explicitly for 'explain', 'in detail', or 'expand', "
    "then provide a more detailed explanation. "
    "Be calm, supportive, and reassuring in tone. "
    "Do not give medical diagnoses. "
    "Focus only on disaster safety, awareness, and management."
)

model = genai.GenerativeModel(
    model_name="gemini-2.5-pro",
    generation_config=generation_config,
    system_instruction=system_instruction,
    safety_settings=safety_settings
)

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/dos-donts')
def dos_donts():
    return render_template('dos_and_donts.html')

@bp.route('/emergency-contacts')
def emergency_contacts():
    return render_template('emergency_contacts.html')

# Serve chatbot page
@bp.route('/chatbot')
def chatbot():
    # Clear any existing chat history when visiting the dedicated chatbot page
    if "chat_history" in session:
        session.pop("chat_history")
    return render_template("chatbot.html")

# Chat API endpoint for frontend
@bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        lang = data.get("lang", "en")  # Get language preference

        if not user_message:
            return jsonify({"response": "I didn't catch that. Could you rephrase?"})

        # Ensure session history is valid
        if "chat_history" not in session:
            session["chat_history"] = []

        # Initialize chat with history
        history = [
            {"role": "user", "parts": [msg["content"]]} if msg["role"] == "user" 
            else {"role": "model", "parts": [msg["content"]]} 
            for msg in session["chat_history"]
        ]
        chat_session = model.start_chat(history=history)

        # Send message to Gemini
        response = chat_session.send_message(user_message)
        bot_response = response.text

        # Save conversation history (limit to last 10 exchanges to prevent session bloat)
        session["chat_history"].append({"role": "user", "content": user_message})
        session["chat_history"].append({"role": "assistant", "content": bot_response})
        
        # Keep only the last 10 exchanges (20 messages)
        if len(session["chat_history"]) > 20:
            session["chat_history"] = session["chat_history"][-20:]
            
        session.modified = True

        return jsonify({"response": bot_response})
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({"response": "I'm experiencing technical difficulties. Please try again shortly."})
