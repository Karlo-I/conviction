# agent.py
# Conviction: AI digest agent — runs once per contribution after submission.
# Fetches evidence from pre-approved sources, summarises against the user's claim.
# Never makes a verdict — reports what evidence exists and surfaces divergence.
# AI assistance: Claude (Anthropic) assisted with prompt design and API integration.
# Logic, decisions, and direction are the author's own.

import requests
import json
import os
import re


ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages'
ANTHROPIC_MODEL = 'claude-haiku-4-5-20251001'


def fetch_who_data(indicator_code, country_code):
    url = f'https://ghoapi.azureedge.net/api/{indicator_code}'
    params = {
        '$filter': f"SpatialDim eq '{country_code}' and Dim1 eq 'SEX_BTSX'",
        '$select': 'SpatialDim,TimeDim,NumericValue',
        '$orderby': 'TimeDim desc',
        '$top': 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        records = data.get('value', [])
        if records:
            return {
                'source': 'WHO Global Health Observatory',
                'value': records[0].get('NumericValue'),
                'year': records[0].get('TimeDim')
            }
    except requests.RequestException:
        pass
    return None


def fetch_worldbank_data(indicator_code, country_code):
    url = f'https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}'
    params = {'format': 'json', 'mrv': 1, 'per_page': 1}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list) or len(data) < 2:
            return None
        records = data[1]
        if records and records[0].get('value') is not None:
            return {
                'source': 'World Bank',
                'value': records[0]['value'],
                'year': records[0]['date']
            }
    except requests.RequestException:
        pass
    return None


def fetch_reference_data(country_code):
    reference_data = []

    who_obesity = fetch_who_data('NCD_BMI_30C', country_code)
    if who_obesity:
        who_obesity['indicator'] = 'Adult obesity rate (%)'
        reference_data.append(who_obesity)

    wb_slum = fetch_worldbank_data('EN.POP.SLUM.UR.ZS', country_code)
    if wb_slum:
        wb_slum['indicator'] = 'Urban slum population (% of urban population)'
        reference_data.append(wb_slum)

    wb_traffic = fetch_worldbank_data('SH.STA.TRAF.P5', country_code)
    if wb_traffic:
        wb_traffic['indicator'] = 'Road traffic mortality rate (per 100,000)'
        reference_data.append(wb_traffic)

    return reference_data


def build_prompt(contribution, reference_data):
    if reference_data:
        lines = []
        for d in reference_data:
            lines.append(
                f"- {d['indicator']}: {d['value']} ({d['source']}, {d['year']})"
            )
        reference_text = '\n'.join(lines)
    else:
        reference_text = 'No reference data found for this country and indicator combination'

    source_text = contribution.get('source_excerpt') or 'No source text provided'

    prompt = f"""You are an evidence analyst for a platform that surfaces systemic issues in food, housing, and mobility.

A user has submitted the following contribution:
Country: {contribution['country_code']}
Claim: {contribution['note']}
User-submitted source excerpt: {source_text}

Reference data from pre-approved institutional sources:
{reference_text}

Your task:
1. Summarise what the reference data shows in relation to the user's claim.
2. If the user provided a source excerpt, note whether it aligns with or diverges from the reference data.
3. Surface any divergence explicitly — do not resolve it in favour of either source.
4. Do not make a verdict on whether the claim is true or false.
5. Do not name or imply blame on any individual or organisation.
6. End your summary with exactly one of these confidence signals on its own line:
CONFIDENCE: evidence found
CONFIDENCE: partial evidence
CONFIDENCE: no data available

Use 'evidence found' if reference data directly relates to the claim.
Use 'partial evidence' if reference data is related but not directly comparable.
Use 'no data available' if no reference data was found for this country and indicator.

Keep your summary under 150 words. Write in plain prose without markdown formatting, headers, or bullet points.
"""

    # --- CONDITIONAL PROMPT FOR LENS PROPOSALS ---
    if contribution.get('contribution_type') == 'lens_proposal':
        prompt += """
        
        ADDITIONAL TASK:
        You are a database librarian. Based on the user's proposal above, extract the following into a strict JSON object:
        - "lens_title": A short, single-word or two-word title for this lens (e.g., "Food", "Housing", "Environment"). Maximum 2 words. Keep it simple and broad.
        - "lens_description": A one-sentence, plain-language description of what this lens tracks.
        - "core_issue": A short, punchy title for the primary systemic issue (e.g., "Planetary Boundaries", "Healthcare Access"). Maximum 3 words.
        
        Return ONLY the JSON object at the very end of your response, wrapped in ```json ... ``` tags. Do not add any conversational text outside the tags.
        """
    # -----------------------------------------------

    return prompt


def parse_confidence(text):
    for line in reversed(text.strip().split('\n')):
        line = line.strip()
        if line.startswith('CONFIDENCE:'):
            value = line.replace('CONFIDENCE:', '').strip().lower()
            if value in ('evidence found', 'partial evidence', 'no data available'):
                return value
    return 'no data available'


def run_agent(db, contribution_id):
    contribution = db.execute(
        'SELECT * FROM contributions WHERE id = ?', (contribution_id,)
    ).fetchone()

    if not contribution:
        return

    country_code = contribution['country_code']
    reference_data = fetch_reference_data(country_code)

    prompt = build_prompt(dict(contribution), reference_data)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        summary = 'AI digest unavailable - API key not configured.'
        confidence = 'no data available'
    else:
        try:
            response = requests.post(
                ANTHROPIC_API_URL,
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                },
                json={
                    'model': ANTHROPIC_MODEL,
                    'max_tokens': 400, # Increased to allow for JSON output
                    'messages': [{'role': 'user', 'content': prompt}]
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            summary = data['content'][0]['text']
            confidence = parse_confidence(summary)

            # Strip the raw CONFIDENCE line from the summary text before saving
            lines = summary.strip().split('\n')
            clean_lines = [line for line in lines if not line.strip().startswith('CONFIDENCE:')]
            summary = '\n'.join(clean_lines).strip()
            
        except Exception as e:
            summary = f'AI digest failed: {str(e)}'
            confidence = 'no data available'

    # --- PARSE THE JSON IF IT'S A LENS PROPOSAL ---
    extracted_json = None
    if contribution['contribution_type'] == 'lens_proposal':
        # Use regex to find the JSON block wrapped in ```json ... ```
        match = re.search(r'```json\s*(.*?)\s*```', summary, re.DOTALL)
        if match:
            try:
                extracted_json = match.group(1)

                # Validate it's actual JSON
                json.loads(extracted_json) 

                # Remove the JSON block from the summary text 
                # so validators only see the plain English summary
                summary = summary.replace(match.group(0), '').strip()
            
            except json.JSONDecodeError:
                extracted_json = None
    # -----------------------------------------------

    db.execute(
        '''
        INSERT INTO contribution_digests (contribution_id, summary, sources, confidence, extracted_json)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (
            contribution_id,
            summary,
            json.dumps(reference_data),
            confidence,
            extracted_json # <-- NEW: Passing the extracted JSON to the database
        )
    )
    db.commit()


def check_force_claim_match(new_note, candidates):
    if not candidates:
        return None

    candidate_lines = '\n'.join(
        f"ID {c['id']}: {c['note']}" for c in candidates
    )

    prompt = f"""You are comparing force claims on a platform that tracks systemic mechanisms across food, housing, and mobility.

New claim: {new_note}

Existing pending claims (same category):
{candidate_lines}

Task: Determine if the new claim describes the SAME underlying mechanism as any existing claim.

Rule: The same mechanism appearing in a different country still counts as a match — mechanisms are not country-specific. A different mechanism, even with similar wording or the same country, is NOT a match.

Answer with only the matching ID number, or NONE if there is no match. No other text."""

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None

    try:
        response = requests.post(
            ANTHROPIC_API_URL,
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            json={
                'model': ANTHROPIC_MODEL,
                'max_tokens': 20,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        answer = data['content'][0]['text'].strip()
        match = re.search(r'\d+', answer)
        if match:
            return int(match.group())
        return None
    except Exception:
        return None
    

# Synthesize multiple contributor-submitted mechanism descriptions into one
# country-agnostic sentence. Called by elevate_force_claim in models.py at elevation time
# Returns None on any failure — caller must not elevate without a valid result
def refine_mechanism(claims):
    if not claims:
        return None

    claims_text = '\n'.join(f"- {c}" for c in claims)

    prompt = f"""You are refining force claims on a platform that tracks systemic mechanisms across food, housing, and mobility.

Multiple contributors independently described the same underlying mechanism, in different countries:
{claims_text}

Task: Write ONE sentence describing the shared mechanism itself, generalized across all the claims above.

Rules:
- Do not name any country, region, or specific place.
- Do not name any individual or organisation.
- Do not copy any single claim verbatim — synthesize the pattern they share.
- One sentence only, maximum 25 words.

Answer with only the sentence. No other text."""

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None

    try:
        response = requests.post(
            ANTHROPIC_API_URL,
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            json={
                'model': ANTHROPIC_MODEL,
                'max_tokens': 60,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        result = data['content'][0]['text'].strip()
        return result if result else None
    except Exception:
        return None