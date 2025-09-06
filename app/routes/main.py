# app/routes/main.py
from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return render_template('homepage.html')

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/dos-donts')
def dos_donts():
    return render_template('dos_and_donts.html')

@bp.route('/emergency-contacts')
def emergency_contacts():
    return render_template('emergency_contacts.html')

@bp.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')