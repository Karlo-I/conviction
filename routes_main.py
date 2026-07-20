# routes_main.py
from flask import Blueprint, render_template, session
from db import get_db
import models

# Create a Blueprint named 'main'
main_bp = Blueprint('main', __name__)


# Renders the landing page and quiz during a certain timeframe
# Passes no data to the template - index.html extends layout.html directly
@main_bp.route('/')
def index():
    db = get_db()

    # Fetch all lenses dynamically
    lenses = models.get_all_lenses(db)
    
    show_quiz_prompt = False
    quiz_button_text = "Take the Diagnostic Quiz"
    
    if 'user_id' in session:
        user_id = session['user_id']
        last_quiz = models.get_last_quiz_response(db, user_id)
        
        if last_quiz is None:
            show_quiz_prompt = True
            quiz_button_text = "Take the Diagnostic Quiz"
        else:
            if models.can_retake_quiz(db, user_id):
                show_quiz_prompt = True
                quiz_button_text = "Retake the Diagnostic Quiz"
    
    return render_template('index.html',
        lenses=lenses,
        show_quiz_prompt=show_quiz_prompt,
        quiz_button_text=quiz_button_text)