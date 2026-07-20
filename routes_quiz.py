# routes_quiz.py
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from db import get_db
import models
import quiz  # This imports your existing quiz.py logic!

# Create a Blueprint named 'quiz'
quiz_bp = Blueprint('quiz', __name__)


# Renders quiz on GET, scores responses and redirects to recommend lens on POST
# Calls quiz.get_questions, quiz.score_responses, models.save_quiz_response, models.can_retake_quiz
@quiz_bp.route('/quiz', methods=['GET', 'POST'])
def quiz_route():
    if 'user_id' not in session:
        flash('You need to be logged in to take the quiz.', 'error')
        return redirect(url_for('auth.login'))
    
    db = get_db()
    user_id = session['user_id']

    retake_days = int(models.get_config(db, 'quiz_retake_days') or 90)
    if not models.can_retake_quiz(db, user_id, retake_days=retake_days):
        flash(f'You can retake the quiz every {retake_days} days.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        responses = {q['id']: request.form.get(q['id']) for q in quiz.get_questions()}

        if any(v is None for v in responses.values()):
            flash('Please answer all questions.', 'error')
            return render_template('quiz.html', questions=quiz.get_questions())
        
        recommended_slug = quiz.score_response(responses)

        if recommended_slug is None:
            flash('Invalid quiz submission. Please try again.', 'error')
            return render_template('quiz.html', questions=quiz.get_questions())

        lens = models.get_lens_by_slug(db, recommended_slug)
        models.save_quiz_response(db, user_id, responses, lens['id'])

        session['recommended_lens'] = recommended_slug
        flash(f'Based on your answers, we recommend starting with the {lens["title"]} lens.', 'success')
        return redirect(url_for('lens.lens', slug=recommended_slug))
    
    return render_template('quiz.html', questions=quiz.get_questions())