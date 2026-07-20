# routes_visual.py
from flask import Blueprint, jsonify, render_template, request
from db import get_db
import models
import viz
import json

# Create a Blueprint named 'viz'
visual_bp = Blueprint('visual', __name__)

# Load comprehensive country data from JSON file (shared across viz routes)
with open('countries.json', 'r') as f:
    COUNTRY_DATA = json.load(f)


@visual_bp.route('/heatmap')
def heatmap():
    return render_template('heatmap.html', country_data=COUNTRY_DATA)


# Return aggregate token spend or least-heard data as JSON for Leaflet.js
# Calls models.get_heatmap_data or models.get_least_heard_data depending on mode perimeter
@visual_bp.route('/api/heatmap')
def heatmap_data():
    db = get_db()
    mode = request.args.get('mode', 'conviction')

    if mode == 'least_heard':
        rows = models.get_least_heard_data(db)
        data = [{'country': r['country_code'],
                 'value': r['data_coverage'],
                 'spend': r['total_spend']} for r in rows]
    else:
        # Conviction mode: delegates to the updated models.py function
        rows = models.get_heatmap_data(db)
        data = [{'country': r['country_code'],
                 'value': r['total_spend'],
                 'top_issue': r['top_issue_title']} for r in rows] 
                
    return jsonify({'mode': mode, 'data': data})


# D3 zoomable sunburst
@visual_bp.route('/api/sunburst')
def sunburst_data():
    db = get_db()
    # Return a JSON string 
    json_data = viz.get_sunburst_data(db)
    return json_data, 200, {'Content-Type': 'application/json'}