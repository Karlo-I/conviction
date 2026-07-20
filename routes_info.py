# routes_info.py
from flask import Blueprint, render_template

# Create a Blueprint named 'info'
info_bp = Blueprint('info', __name__)

@info_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@info_bp.route('/terms')
def terms():
    return render_template('terms.html')

@info_bp.route('/how_it_works')
def how_it_works():
    return render_template('how_it_works.html')

@info_bp.route('/commitments')
def commitments():
    return render_template('commitments.html')