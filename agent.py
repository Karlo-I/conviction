# agent.py
# Conviction: AI digest agent — runs once per contribution after submission.
# Analyzes user-submitted evidence, never makes a verdict.
# AI assistance: Both Claude (Anthropic) and Qwen.ai (3.7-Plus) assisted with query structure and error handling patterns.
# Logic, decisions, and direction are the author's own.

import requests
import json
import os
import re


ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages'
ANTHROPIC_MODEL = 'claude-haiku-4-5-20251001'


# Remove markdown formatting from text returned by AI digest
def strip_markdown(text):
    if not text:
        return text
    
    # Remove markdown code blocks
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    
    # Remove bold/italic markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
    
    # Remove headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove bullet points
    text = re.sub(r'^[\-\*]\s*', '', text, flags=re.MULTILINE)
    
    return text.strip()


def build_prompt(contribution, existing_lenses):
    source_text = contribution.get('source_excerpt') or 'No source text provided'
    country = contribution.get('country_code', 'Not specified')
    claim = contribution.get('note', 'No claim provided')

    # Format the existing lenses list for the AI
    if existing_lenses:
        existing_lenses_text = ", ".join([l['title'] for l in existing_lenses])
    else:
        existing_lenses_text = "None"

    prompt = f"""You are an evidence analyst for a platform that surfaces systemic issues through peer-validated contributions.

A user has submitted the following contribution:

**Country/Context:** {country}
**Claim:** {claim}
**Source Excerpt:** {source_text}

**EXISTING LENSES IN DATABASE:** {existing_lenses_text}

---

YOUR TASK:

Analyze the relationship between the user's claim and their provided source excerpt. Do NOT fact-check against external databases or make judgments about truth. Instead:

1. **Assess the evidence:** Does the source excerpt directly support, partially support, or fail to address the specific claim made?

2. **Identify strengths:** What does the source do well? (e.g., provides specific data, cites methodology, includes time period/location)

3. **Identify gaps:** What's missing that would strengthen this claim? (e.g., sample size, date, geographic scope, conflicting evidence)

4. **Note context:** Is this a primary source, news report, academic study, or advocacy document? Does that matter for interpretation?

5. **Suggest improvements:** What additional evidence or clarification would make this claim more robust?

6. **End with exactly one confidence signal on its own line:**
   CONFIDENCE: strong evidence
   CONFIDENCE: partial evidence  
   CONFIDENCE: weak evidence
   CONFIDENCE: no evidence provided

Use 'strong evidence' if the source directly supports the claim with specific data.
Use 'partial evidence' if the source is relevant but incomplete or indirect.
Use 'weak evidence' if the source barely relates to the claim or lacks specifics.
Use 'no evidence provided' if no source excerpt was submitted.

Keep your summary under 150 words. Write in plain prose without markdown formatting, headers, or bullet points. Be constructive, not dismissive.
"""

    # --- CONDITIONAL PROMPT FOR LENS PROPOSALS ---
    if contribution.get('contribution_type') == 'lens_proposal':
        prompt += """
        
        ADDITIONAL TASK:
        You are a database librarian. Based on the user's proposal above, extract the following into a strict JSON object:
        - "lens_title": A short, single-word or two-word title for this lens (e.g., "Food", "Housing", "Environment"). Maximum 2 words. Keep it simple and broad.
        - "lens_description": A one-sentence, plain-language description of what this lens tracks.
        - "core_issue": A short, punchy title for the primary systemic issue (e.g., "Planetary Boundaries", "Healthcare Access"). Maximum 3 words.
        
        CRITICAL INSTRUCTION FOR LENS PROPOSALS: 
        Look at the "EXISTING LENSES IN DATABASE" list above. If the user's proposal is a subset, duplicate, or highly overlapping with one of those existing lenses, you MUST set "lens_title" to the EXACT name of that existing lens. Do not create a new title. Only create a new title if it is a completely distinct systemic domain not covered by the existing list.

        EXAMPLE OF MERGING:
        If Existing Lenses are: "Food, Housing, Mobility"
        And User Proposes: "Agriculture" or "Commuting"
        You MUST output: "lens_title": "Food" (for Agriculture) or "lens_title": "Mobility" (for Commuting).
        Do not output "Agriculture" or "Commuting" as the title. Use the exact existing title.
        
        Return ONLY the JSON object at the very end of your response, wrapped in ```json ... ``` tags. Do not add any conversational text outside the tags.
        """
    # -----------------------------------------------

    return prompt


def parse_confidence(text):
    for line in reversed(text.strip().split('\n')):
        line = line.strip()
        if line.startswith('CONFIDENCE:'):
            value = line.replace('CONFIDENCE:', '').strip().lower()
            if value in ('strong evidence', 'partial evidence', 'weak evidence', 'no evidence provided'):
                return value
    return 'no evidence provided'


def run_agent(db, contribution_id, existing_lenses):
    contribution = db.execute(
        'SELECT * FROM contributions WHERE id = ?', (contribution_id,)
    ).fetchone()

    if not contribution:
        return

    # NO REFERENCE DATA FETCHING - we analyze what the user provides
    prompt = build_prompt(dict(contribution), existing_lenses)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        summary = 'AI digest unavailable - API key not configured.'
        confidence = 'no evidence provided'
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
                    'max_tokens': 400, 
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

            # Strip markdown formatting
            summary = strip_markdown(summary)

            # Remove common AI-generated headers (case-insensitive)
            lines = summary.split('\n')
            skip_first_line = False
            
            if lines:
                line_lower = lines[0].strip().lower()
                # Skip lines that are just headers
                if line_lower in ['analysis', 'evidence analysis', 'summary', 'assessment', 'ai analysis', 'evidence assessment']:
                    skip_first_line = True
                # Also skip if it starts with these headers followed by a colon
                elif any(line_lower.startswith(prefix) for prefix in ['analysis:', 'evidence analysis:', 'summary:', 'assessment:', 'ai analysis:', 'evidence assessment:']):
                    skip_first_line = True
                    
            if skip_first_line and len(lines) > 1:
                summary = '\n'.join(lines[1:]).strip()
            
        except Exception as e:
            summary = f'AI digest failed: {str(e)}'
            confidence = 'no evidence provided'

    # --- PARSE THE JSON IF IT'S A LENS PROPOSAL ---
    extracted_json = None
    if contribution['contribution_type'] == 'lens_proposal':
        match = re.search(r'```json\s*(.*?)\s*```', summary, re.DOTALL)
        if match:
            try:
                extracted_json = match.group(1)
                json.loads(extracted_json) 
                summary = summary.replace(match.group(0), '').strip()
            except json.JSONDecodeError:
                extracted_json = None
    # -----------------------------------------------

    # --- PREPARE THE SOURCES PAYLOAD ---
    # No reference_data anymore - just the lens proposal if applicable
    sources_payload = {}
    if extracted_json:
        try:
            sources_payload["lens_proposal"] = json.loads(extracted_json)
        except json.JSONDecodeError:
            pass
    # -----------------------------------

    # --- INSERT INTO DATABASE ---
    db.execute(
        '''
        INSERT INTO contribution_digests (contribution_id, summary, sources, confidence)
        VALUES (?, ?, ?, ?)
        ''',
        (
            contribution_id,
            summary,
            json.dumps(sources_payload),
            confidence
        )
    )
    db.commit()


def check_force_claim_match_and_clean(new_note, new_excerpt, candidates):
    if not candidates:
        return None, None, None

    candidate_lines = '\n'.join(
        f"ID {c['id']}: {c['note']}" for c in candidates
    )

    prompt = f"""You are a data quality controller.

New claim: {new_note}
New source excerpt: {new_excerpt}

Existing claims (same category):
{candidate_lines}

Task 1: Does the new claim describe the EXACT SAME underlying mechanism as any existing claim?
- Rule: Same mechanism in a different country = MATCH. Different mechanism = NO MATCH.

Task 2: If there is a MATCH, you MUST fix ALL typos and erratic capitalization in BOTH the new claim and the source excerpt. 
- Example: Change "ecONnoMy" to "economy", "ALGORIthmic" to "algorithmic".
- Do NOT change the meaning. Only fix errors.

Respond in JSON format ONLY:
{{
    "match_id": <number or null>,
    "cleaned_note": "<fixed claim text or null>",
    "cleaned_excerpt": "<fixed excerpt text or null>"
}}"""

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None, None, None

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
                'max_tokens': 250,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        answer = data['content'][0]['text'].strip()
        
        match = re.search(r'\{.*\}', answer, re.DOTALL)
        if match:
            result = json.loads(match.group())
            return result.get('match_id'), result.get('cleaned_note'), result.get('cleaned_excerpt')
            
        return None, None, None
    except Exception as e:
        print(f"Error in check_force_claim_match_and_clean: {e}")
        return None, None, None
    

# Synthesize multiple contributor-submitted mechanism descriptions into one
# country-agnostic sentence. Called by elevate_force_claim in models.py at elevation time
# Returns a dictionary with 'mechanism' and 'strategic_implication' on success, None on failure.
def refine_mechanism(claims):
    if not claims:
        return None

    claims_text = '\n'.join(f"- {c}" for c in claims)

    prompt = f"""You are refining force claims on a platform that tracks systemic mechanisms across food, housing, and mobility.

Multiple contributors independently described the same underlying mechanism, in different countries:
{claims_text}

Task: 
1. Write ONE sentence describing the shared mechanism itself, generalized across all the claims above.
2. Write ONE sentence explaining the strategic implication — what systemic consequence does this mechanism create?

Rules:
- Do not name any country, region, or specific place.
- Do not name any individual or organisation.
- Do not copy any single claim verbatim — synthesize the pattern they share.
- Use standard sentence capitalization and correct spelling.
- One sentence only for each output, maximum 25 words each.

Return ONLY a JSON object with exactly these two fields:
{{
    "mechanism": "<the synthesized mechanism sentence>",
    "strategic_implication": "<the systemic consequence sentence>"
}}"""

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
                'max_tokens': 150,  # Increased from 60 to accommodate JSON output
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        result = data['content'][0]['text'].strip()

        # Strip markdown formatting (handles code blocks, bold, etc.)
        result = strip_markdown(result)
        
        # Parse the JSON response
        result_json = json.loads(result)
        return {
            'mechanism': result_json.get('mechanism'),
            'strategic_implication': result_json.get('strategic_implication')
        }
    except Exception as e:
        print(f"Error in refine_mechanism: {e}")
        return None
    

# Fix obvious typos and formatting for display purposes only
def clean_display_text(text):
    if not text:
        return text
    
    prompt = f"""Fix obvious typos, capitalization errors, and formatting issues in this text. 
    Preserve the original meaning and technical terms. Return ONLY the cleaned text.

    Text: {text}"""
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return text
    
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
                'max_tokens': 100,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data['content'][0]['text'].strip()
    except Exception:
        return text  # Return original on error
    

# Clean typos in a new submission before saving
def clean_submission_text(text):
    if not text:
        return text
    
    prompt = f"""Fix ALL typos and erratic capitalization in this text. 
    Example: Change "ecONnoMy" to "economy". Do NOT change the meaning.
    Return ONLY the fixed text.
    
    Text: {text}"""
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return text
    
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
                'max_tokens': 150,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data['content'][0]['text'].strip()
    except Exception:
        return text