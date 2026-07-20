# routes_forces.py
from flask import Blueprint, redirect, render_template, url_for
from db import get_db
import models

# Create a Blueprint named 'forces'
forces_bp = Blueprint('forces', __name__)


@forces_bp.route('/forces')
def forces():
    db = get_db()
    all_forces = models.get_all_forces(db)

    grouped = {}
    for f in all_forces:
        grouped.setdefault(f['category'], []).append(f)

    return render_template('forces.html', grouped_forces=grouped)


@forces_bp.route('/force/<slug>')
def force_detail(slug):
    db = get_db()
    force = models.get_force_by_slug(db, slug)

    if force is None:
        return redirect(url_for('forces.forces'))
    
    return render_template('force.html', force=force)