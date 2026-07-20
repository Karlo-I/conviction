# quiz.py
# Conviction: diagnostic quiz questions and lens classification logic
# Rule-based weighted scoring system — no API cost, runs entirely in Python
# AI assistance: Both Claude (Anthropic) and Qwen.ai (3.7-Plus) assisted with query structure and error handling patterns
# Logic, decisions, and direction are the author's own

# Questions and their weighted impact on each lens affinity score
# Each answer option maps to a dictionary of weights: {'lens_slug': score}
# Weights are additive — highest total score determines recommended lens.
# NOTE: This structure is now fully scalable. Add new lenses by simply adding 
# their slug to the weights dictionary below.

QUIZ_QUESTIONS = [
    {
        'id': 'q1',
        'text': 'What is the biggest source of financial stress in your life right now, if any?',
        'options': [
            {'text': 'Food and grocery costs',      'weights': {'food': 3}},
            {'text': 'Rent or mortgage payments',   'weights': {'housing': 3}},
            {'text': 'Transport and fuel costs',    'weights': {'mobility': 3}},
            {'text': 'Medical bills or healthcare costs', 'weights': {'healthcare': 3}},
            {'text': 'Energy bills and heating costs',    'weights': {'energy': 3}},
            {'text': 'All of the above equally',    'weights': {'food': 1, 'housing': 1, 'mobility': 1, 'healthcare': 1, 'energy': 1}},
        ]
    },
    {
        'id': 'q2',
        'text': 'Which of these do you think about most when planning your week?',
        'options': [
            {'text': 'What I can afford to eat',        'weights': {'food': 3}},
            {'text': 'Whether my housing is secure',    'weights': {'housing': 3}},
            {'text': 'How long my commute takes',       'weights': {'mobility': 3}},
            {'text': 'Managing a health condition or care', 'weights': {'healthcare': 3}},
            {'text': 'Keeping the lights on and energy costs', 'weights': {'energy': 3}},
            {'text': 'I think about all of these',      'weights': {'food': 1, 'housing': 1, 'mobility': 1, 'healthcare': 1, 'energy': 1}},
        ]
    },
    {
        'id': 'q3',
        'text': 'Which consequence do you feel most directly in your daily life?',
        'options': [
            {'text': 'Poor nutrition or limited food choices',          'weights': {'food': 3}},
            {'text': 'Overcrowded or unaffordable living conditions',   'weights': {'housing': 3}},
            {'text': 'Time lost to commuting or lack of transport',     'weights': {'mobility': 3}},
            {'text': 'Lack of access to medical care or medicines',     'weights': {'healthcare': 3}},
            {'text': 'Cold homes or unreliable power supply',           'weights': {'energy': 3}},
            {'text': 'I feel all of these',                             'weights': {'food': 1, 'housing': 1, 'mobility': 1, 'healthcare': 1, 'energy': 1}},
        ]
    },
    {
        'id': 'q4',
        'text': 'If you could change one thing about the system you live in, what would it be?',
        'options': [
            {'text': 'Make healthy food affordable for everyone',               'weights': {'food': 3}},
            {'text': 'Make housing a right, not an investment',                 'weights': {'housing': 3}},
            {'text': 'Build cities around people, not cars',                    'weights': {'mobility': 3}},
            {'text': 'Ensure universal access to quality healthcare',           'weights': {'healthcare': 3}},
            {'text': 'Transition to clean, affordable, and reliable energy',    'weights': {'energy': 3}},
            {'text': 'Fix the underlying economic system causing all of it',    'weights': {'food': 1, 'housing': 1, 'mobility': 1, 'healthcare': 1, 'energy': 1}},
        ]
    },
    {
        'id': 'q5',
        'text': 'Where do you see the clearest gap between what exists and what should exist?',
        'options': [
            {'text': 'In what people can afford to eat',        'weights': {'food': 3}},
            {'text': 'In access to decent, stable housing',     'weights': {'housing': 3}},
            {'text': 'In safe, affordable ways to get around',  'weights': {'mobility': 3}},
            {'text': 'In access to quality, affordable healthcare', 'weights': {'healthcare': 3}},
            {'text': 'In access to reliable, clean energy',     'weights': {'energy': 3}},
            {'text': 'The gap exists everywhere simultaneously','weights': {'food': 1, 'housing': 1, 'mobility': 1, 'healthcare': 1, 'energy': 1}},
        ]
    }
]


# Score quiz responses and return the recommended lens slug
# Called by app.py quiz after form POST; returns None if all responses are invalid
def score_response(responses):
    # Dynamic totals dictionary - no need to hardcode lens names anymore!
    totals = {}
    valid_questions_scored = 0

    for question in QUIZ_QUESTIONS:
        qid = question['id']
        if qid not in responses:
            continue
        try:
            option_index = int(responses[qid])
            option = question['options'][option_index]
            
            # Add weights to the totals dynamically
            for lens, weight in option['weights'].items():
                totals[lens] = totals.get(lens, 0) + weight
                
            valid_questions_scored += 1
        except (ValueError, IndexError):
            continue
    
    if valid_questions_scored == 0:
        return None
    
    # Return the lens with the highest score
    return max(totals, key=totals.get)


# Return the full question list for rendering in quiz.html
# Called by app.py quiz route on GET request
def get_questions():
    return QUIZ_QUESTIONS