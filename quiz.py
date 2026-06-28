# quiz.py
# Conviction: diagnostic quiz questions and lens classification logic
# Rule-based weighted scoring system — no API cost, runs entirely in Python
# AI assistance: Claude (Anthropic) assisted with scoring structure and weight design
# Logic, decisions, and direction are the author's own

# Questions and their weighted impact on each lens affinity score
# Each answer option maps to {'food': x, 'housing': y, 'mobility': z}
# Weights are additive — highest total score determines recommended lens

QUIZ_QUESTIONS = [
    {
        'id': 'q1',
        'text': 'What is the biggest source of financial stress in your life right now, if any?',
        'options': [
            {'text': 'Food and grocery costs',      'weights': {'food': 3, 'housing': 0, 'mobility': 0}},
            {'text': 'Rent or mortgage payments',   'weights': {'food': 0, 'housing': 3, 'mobility': 0}},
            {'text': 'Transport and fuel costs',    'weights': {'food': 0, 'housing': 0, 'mobility': 3}},
            {'text': 'All of the above equally',    'weights': {'food': 1, 'housing': 1, 'mobility': 1}},
        ]
    },
    {
        'id': 'q2',
        'text': 'Which of these do you think about most when planning your week?',
        'options': [
            {'text': 'What I can afford to eat',        'weights': {'food': 3, 'housing': 0, 'mobility': 0}},
            {'text': 'Whether my housing is secure',    'weights': {'food': 0, 'housing': 3, 'mobility': 0}},
            {'text': 'How long my commute takes',       'weights': {'food': 0, 'housing': 0, 'mobility': 3}},
            {'text': 'I think about all of these',      'weights': {'food': 1, 'housing': 1, 'mobility': 1}},
        ]
    },
    {
        'id': 'q3',
        'text': 'Which consequence do you feel most directly in your daily life?',
        'options': [
            {'text': 'Poor nutrition or limited food choices',          'weights': {'food': 3, 'housing': 0, 'mobility': 0}},
            {'text': 'Overcrowded or unaffordable living conditions',   'weights': {'food': 0, 'housing': 3, 'mobility': 0}},
            {'text': 'Time lost to commuting or lack of transport',     'weights': {'food': 0, 'housing': 0, 'mobility': 3}},
            {'text': 'I feel all of these',                             'weights': {'food': 1, 'housing': 1, 'mobility': 1}},
        ]
    },
    {
        'id': 'q4',
        'text': 'If you could change one thing about the system you live in, what would it be?',
        'options': [
            {'text': 'Make healthy food affordable for everyone',               'weights': {'food': 3, 'housing': 1, 'mobility': 0}},
            {'text': 'Make housing a right, not an investment',                 'weights': {'food': 0, 'housing': 3, 'mobility': 1}},
            {'text': 'Build cities around people, not cars',                    'weights': {'food': 0, 'housing': 1, 'mobility': 3}},
            {'text': 'Fix the underlying economic system causing all of it',    'weights': {'food': 1, 'housing': 1, 'mobility': 1}},
        ]
    },
    {
        'id': 'q5',
        'text': 'Where do you see the clearest gap between what exists and what should exists?',
        'options': [
            {'text': 'In what people can afford to eat',        'weights': {'food': 3, 'housing': 0, 'mobility': 0}},
            {'text': 'In access to decent, stable housing',     'weights': {'food': 0, 'housing': 3, 'mobility': 0}},
            {'text': 'In safe, affordable ways to get around',  'weights': {'food': 0, 'housing': 0, 'mobility': 3}},
            {'text': 'The gap exists everywhere simultaneously','weights': {'food': 1, 'housing': 1, 'mobility': 1}},
        ]
    }
]


# Score quiz responses and return the recommended lens slug
# Called by app.py quiz after form POST; responses is a dict of {question_id: option_index}
def score_response(responses):
    totals = {'food': 0, 'housing': 0, 'mobility': 0}

    for question in QUIZ_QUESTIONS:
        qid = question['id']
        if qid not in responses:
            continue
        try:
            option_index = int(responses[qid])
            option = question['options'][option_index]
            for lens, weight in option['weights'].items():
                totals[lens] += weight
        except (ValueError, IndexError):
            continue

    return max(totals, key=totals.get)


# Return the full question list for rendering in quiz.html
# Called by app.py quiz route on GET request
def get_questions():
    return QUIZ_QUESTIONS
