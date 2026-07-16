# Conviction
### CS50x Final Project — Living Project Brief
**Last Updated:** July 14, 2026 (rev 18)
**Status:** Deployed — Live at https://conviction-20z3.onrender.com/

---

#### Video Demo
`<URL to be added after recording>`

---

## Description

Conviction is a web application that helps people trace the line between what they experience daily — rising costs, poor health, environmental damage, financial precarity — and the systemic mechanisms that produce those outcomes.

Most people see symptoms. This app surfaces the machinery — and the forces operating that machinery.

Users explore five systemic lenses to begin with — **Food**, **Housing**, **Mobility**, **Energy**, and **Healthcare** — which will increase as more users propose new lenses that matters. But the data alone is incomplete. Behind each lens sits a fourth layer: the **underlying forces** — financial capture, regulatory arbitrage, externalised cost, information asymmetry — that operate across all domains simultaneously. The same mechanism that keeps ultra-processed food dominant in dietary policy also keeps housing treated as an investment asset and car dependency entrenched in urban planning. The platform makes that cross-domain pattern visible.

Users take a short diagnostic quiz that personalises which lens they see first, then move through the evidence at their own depth. They register, receive tokens, and spend them on the issues they believe matter most. Their conviction aggregates into a global heatmap showing where collective concern is concentrating.

The platform is designed for people who already sense something is wrong and want to understand the mechanism — and made accessible enough that people who don't yet see the problem can be brought in through the quiz. It names no individual actors. It presents mechanisms, evidence chains, and sourced data and lets users draw their own conclusions.

---

## The Thesis

The systems that govern how people eat, live, and move are optimised for extraction, not human flourishing. The data is global, the pattern is consistent, and most people never see the mechanism — only its consequences.

The root problem is not individual greed or moral failure. It is that certain systems select for and reward short-term extraction, externalised harm, and regulatory capture — and will continue to do so regardless of who occupies positions of power within them. Change the people; the system produces new versions of the same behaviour. Change the rules; the behaviour changes. This platform is about the rules.

The platform classifies mechanisms — financial capture, regulatory arbitrage, externalised cost, information asymmetry — and presents the evidence chains that demonstrate those mechanisms operating. The evidence speaks. Users conclude.

The platform's commitments to truth, transparency, epistemic humility, and non-discrimination are published at https://conviction-20z3.onrender.com/commitments.

---

## Stack

| Layer | Technology | Notes |
|---|---|---|
| Backend | Python / Flask | Routing, business logic, API endpoints |
| Database | SQLite (dev) → PostgreSQL (prod) | PostgreSQL hosted on Render; two separate schema files |
| Compatibility | `Psycopg2Wrapper` in `app.py` | Auto-converts SQLite `?` to PostgreSQL `%s`; `models.py` unchanged |
| Frontend | Vanilla JavaScript | No framework — keeps scope tight |
| Mapping | Leaflet.js | Free, open source, handles global heatmap |
| Charts | Chart.js | Data visualisation per lens |
| Activity | Strava API (free tier) | OAuth 2.0, activity sync for token rewards — post-submission pipeline |
| AI Agent | claude-haiku-4-5-20251001 | Contribution digest generation — runs once per contribution |
| Hosting | Render (free tier) | Live at https://conviction-20z3.onrender.com/ |

**Cost target: Near-zero**
The only ongoing cost is the AI agent call triggered when a user submits a contribution. Using a lightweight model (claude-haiku or gpt-4o-mini), each call costs approximately $0.002–$0.01. At low traffic — say 100 contributions in the first few months — total cost is under $1. Cost scales with contributions submitted, not with page views or users. This is the right scaling relationship. All other components remain free.

---

## Core Features (MVP)

1. **Diagnostic Quiz** — 5–7 questions classifying the user's lived experience into system impact categories. Designed for people who already sense something is wrong; accessible enough to bring in those who don't yet see it.

   **Onboarding flow:** The quiz is the final step of registration, not a separate visit. Sequence: register (username, password) → complete quiz → land on personalised lens. No email address is collected at any point. This ensures every user has a `quiz_response` stored against their `user_id` from the first interaction and personalisation feels immediate.

   **After the quiz:** The result page shows the user's primary lens and a cross-pollination hook — "people who care about food systems often find the housing lens surprising" with a specific data point as the entry. This is the first echo chamber prevention mechanism: exposure to a secondary lens is built into the onboarding result, not left to chance.

   **Retake policy:** Retakeable once every 90 days, enforced by a Python check on the most recent `quiz_responses` entry for that `user_id`. People's circumstances and concerns change — locking the result permanently is wrong. But unlimited retakes allow gaming the lens routing. The 90-day gate is stored in `platform_config` as `quiz_retake_days` and is adjustable without code changes. When a user retakes and gets a different result, the UI surfaces the shift: "your primary lens has moved from Food to Housing since you joined" — the platform reflecting personal change back to the user.

2. **Five Lenses** — Food, Housing, Mobility, Energy, and Healthcare. Food, Housing, and Mobility are seeded with a few API data from WHO and World Bank. Energy and Healthcare are seeded with structural content (lenses and issues) ready for community data contributions. All lenses present data through the unified contributions table — no distinction between institutional and community data.

3. **Forces Layer** — The fourth layer beneath all lenses. Each force is a cross-domain mechanism classified into these categories, amongst others:
   - **Financial capture** — when financial interests shape policy outcomes in their favour
   - **Regulatory arbitrage** — exploiting gaps between jurisdictions or regulatory frameworks
   - **Externalised cost** — when the real cost of an activity is borne by those who didn't choose it
   - **Information asymmetry** — when one party in a system has access to knowledge the other doesn't

   Each force entry contains: a plain-language mechanism description, sourced evidence chain, and cross-lens links showing where the same force appears across domains. No verdicts. No named actors. Mechanisms and receipts.

4. **Token System** — Users register and immediately receive an opening balance of 10 tokens. This is deliberate — a new user who cannot act immediately will leave immediately. Ten tokens is enough to spend meaningfully across two or three issues and experience the platform's core mechanic, but not so large that scarcity loses its meaning. Tokens are spent on issues within lenses to signal conviction — a deliberate act that forces genuine prioritisation, unlike a like button.

5. **Token Earning** — Users earn additional tokens through two mechanisms:
   - Contributing local data points (pending peer validation and AI digest)
   - Validating other users' contributions (one token per validation cast)

6. **Peer Validation with AI Digest** — When a user submits a contribution, an AI agent (running in `agent.py`) generates a plain-language summary comparing the claim against pre-approved data sources. This digest is stored once and shown to all validators — the AI runs once per contribution, not once per validator. Validators read the digest and cast an approve or reject vote. The AI presents evidence only; it does not make a verdict.

   **User-submitted sources:** Contributors can optionally include their own evidence via two fields: a pasted text excerpt (primary) and a source URL (citation). The pasted text is the reliable input — the agent processes it directly. The URL is a citation for validators to verify manually, not a resource the agent fetches. A "verify source" link on `validate.html` opens the URL in a new tab. This approach is more robust than URL fetching, which can fail on PDFs, paywalled content, and JavaScript-rendered pages.

   **Source conflict as a feature:** Where a user-submitted source conflicts with pre-approved API data, the digest surfaces the conflict explicitly rather than resolving it. Conflict between a local source and an institutional dataset is precisely the kind of information asymmetry the forces layer documents — making it visible is consistent with the platform's thesis.

   **Agent fallback:** If a user provides no pasted text and no URL, the agent falls back to querying pre-approved sources only. If those return nothing, the digest shows `'no data available'` and the UI tells the validator: "No external data found. Evaluate based on the claim alone."

7. **Global Heatmap** — Aggregate token spend by country renders as a heatmap via Leaflet.js. Users watch their contribution shift the map. Starts as a static render; near-real-time updates (page refresh triggers new data fetch) are the target. True real-time via WebSockets is a post-submission stretch goal.

   **Echo chamber prevention toggle:** The heatmap has two modes — "highest conviction" (where token spend is densest) and "least heard" (countries and issues with real data but low token spend). The second mode actively directs attention toward underrepresented voices rather than amplifying already-loud ones. This is a JavaScript toggle on the frontend, backed by two different query parameters to the heatmap endpoint in `app.py`.

---

## SQL Schema

This is the most important architectural decision. The schema is designed to be flexible — new lenses, new issues, and new indicators are added as data rows, not as new code. Two schema files exist: `schema.sql` for SQLite (local development) and `schema_postgres.sql` for PostgreSQL (production on Render). The `Psycopg2Wrapper` class in `app.py` handles syntax differences transparently so `models.py` uses SQLite syntax throughout.

```sql
-- Core content structure
CREATE TABLE IF NOT EXISTS lenses (
    id SERIAL PRIMARY KEY,                   -- PostgreSQL: SERIAL; SQLite: INTEGER PRIMARY KEY AUTOINCREMENT
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS issues (
    id SERIAL PRIMARY KEY,
    lens_id INTEGER NOT NULL REFERENCES lenses(id),
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS indicators (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES issues(id),
    name TEXT NOT NULL,
    source TEXT,
    unit TEXT,
    UNIQUE(issue_id, name)
);

-- Forces layer (fourth layer — cross-domain mechanisms beneath all lenses)
CREATE TABLE IF NOT EXISTS forces (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,              -- 'financial_capture', 'regulatory_arbitrage',
                                         -- 'externalised_cost', 'information_asymmetry'
    mechanism TEXT NOT NULL,
    evidence_chain JSON,                 -- array of {claim, source_url, data_summary} objects
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS force_issue_links (
    id SERIAL PRIMARY KEY,
    force_id INTEGER NOT NULL REFERENCES forces(id),
    issue_id INTEGER NOT NULL REFERENCES issues(id),
    explanation TEXT,
    UNIQUE(force_id, issue_id)
);

-- Users and authentication
-- No email address is collected — privacy by design decision.
-- Bot prevention handled by hCaptcha at registration (no PII collected).
-- Account recovery is not possible without email — disclosed explicitly at registration.
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    token_balance INTEGER DEFAULT 10,    -- opening balance granted at registration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data sources registry (reference points, not arbiters of truth)
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    methodology_url TEXT,
    limitations TEXT,
    institutional_context TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token economy
CREATE TABLE IF NOT EXISTS token_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,             -- positive = earned, negative = spent
    reason TEXT NOT NULL,                -- 'registration', 'contribution', 'validation', 'spend'
    issue_id INTEGER REFERENCES issues(id),
    force_id INTEGER REFERENCES forces(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- UNIFIED DATA ARCHITECTURE: All data lives here — both seeded institutional data
-- (via 'Data Archive' system user) and user contributions. No distinction between
-- "official" and "community" data — all is peer-validated evidence.
CREATE TABLE IF NOT EXISTS contributions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    indicator_id INTEGER REFERENCES indicators(id),
    country_code TEXT NOT NULL,
    title TEXT,
    category TEXT,
    value REAL,
    note TEXT,
    source_url TEXT,
    source_excerpt TEXT,
    contribution_type TEXT DEFAULT 'data_point', -- 'data_point', 'force_claim', 'lens_proposal'
    status TEXT DEFAULT 'pending',
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contribution_sources (
    id SERIAL PRIMARY KEY,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    note TEXT,
    source_url TEXT,
    source_excerpt TEXT,
    contributor_user_id INTEGER NOT NULL REFERENCES users(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contribution_lens_links (
    id SERIAL PRIMARY KEY,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    issue_id INTEGER NOT NULL REFERENCES issues(id),
    UNIQUE(contribution_id, issue_id)
);

-- Diagnostic quiz
CREATE TABLE IF NOT EXISTS quiz_responses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id TEXT,
    responses JSON NOT NULL,
    recommended_lens_id INTEGER REFERENCES lenses(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI-generated source digest (generated once per contribution, shown to all validators)
CREATE TABLE IF NOT EXISTS contribution_digests (
    id SERIAL PRIMARY KEY,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    summary TEXT NOT NULL,
    sources JSON,
    confidence TEXT NOT NULL,            -- 'evidence found', 'partial evidence', 'no data available'
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extracted_json TEXT
);

-- Peer validation votes
CREATE TABLE IF NOT EXISTS contribution_votes (
    id SERIAL PRIMARY KEY,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    vote TEXT NOT NULL,                  -- 'approve' or 'reject'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contribution_id, user_id)
);

-- Platform configuration (adjust behaviour without code changes)
CREATE TABLE IF NOT EXISTS platform_config (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed data for platform config
INSERT INTO platform_config (key, value, description) VALUES
    ('validation_threshold', '2', 'Peer approvals needed to approve a data_point contribution'),
    ('force_approval_threshold', '3', 'Peer approvals needed to elevate a force_claim into forces layer'),
    ('rejection_threshold_data_point', '3', 'Reject votes needed to reject a data_point contribution'),
    ('rejection_threshold_force_claim', '5', 'Reject votes needed to reject a force_claim contribution'),
    ('minimum_total_votes_data_point', '3', 'Minimum total votes before a data_point can resolve'),
    ('minimum_total_votes_force_claim', '5', 'Minimum total votes before a force_claim can resolve'),
    ('tokens_per_validation', '1', 'Tokens earned for casting a validation vote'),
    ('tokens_per_contribution', '3', 'Tokens earned when contribution is approved'),
    ('agent_model', 'claude-haiku-4-5-20251001', 'AI model used for contribution digests'),
    ('max_contributions_per_day', '5', 'Rate limit per user per day'),
    ('quiz_retake_days', '90', 'Minimum days between quiz retakes per user')
ON CONFLICT (key) DO NOTHING;

-- Share tracking (kept in schema for future use — sharing mechanic not implemented in MVP)
CREATE TABLE IF NOT EXISTS shares (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    content_type TEXT NOT NULL,
    content_id INTEGER,
    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key design decisions:**
- `lenses`, `issues`, `indicators` form a clean hierarchy. Adding a new lens is an INSERT, not a schema change — proven during build when Energy and Healthcare were added with no code changes.
- `Unified data architecture`: The `contributions` table stores ALL data — both seeded institutional data (via the "Data Archive" system user) and user-submitted contributions. There is no separate `data_points` table. This reflects the platform's philosophical commitment: all knowledge is built by the community through peer validation, not handed down from authority.
- `sources` is a registry of reference data sources — not arbiters of truth, but documented reference points with known limitations and institutional context recorded explicitly.
- `forces` sits beneath all lenses simultaneously. A force is not owned by a lens — it connects to issues across lenses via `force_issue_links`.
- `evidence_chain` in `forces` stores a JSON array of sourced claims. Each object contains a claim, a source URL, and a plain-language data summary.
- `users` stores no email address — a deliberate privacy-by-design decision. Bot prevention is handled by hCaptcha at registration. Account recovery is not possible and this is disclosed explicitly to users at registration.
- `token_transactions` is an append-only ledger. `token_balance` on `users` is a derived cache — always recalculable from the ledger. Python always writes to the ledger first; balance is never updated independently.
- `contributions` has a `contribution_type` field — `'data_point'`, `'force_claim'`, or `'lens_proposal'`. Python in `models.py` routes approved force claims into `forces` and `force_issue_links` when the `force_approval_threshold` in `platform_config` is reached.
- `contribution_digests` stores the AI agent's output once per contribution. All validators see the same digest — the agent never runs more than once per contribution.
- `contribution_votes` has a `UNIQUE` constraint on `(contribution_id, user_id)` — the database enforces one vote per user per contribution.
- `confidence` in `contribution_digests` uses plain-language values (`'evidence found'`, `'partial evidence'`, `'no data available'`) — the AI reports what it found, not what it concluded.
- `platform_config` is a key-value config table. Validation thresholds, token rewards, AI model choice, and rate limits are all rows — adjustable without touching Python code.
- `quiz_responses` stores raw JSON so question wording can evolve without a schema migration.
- `shares` table is in the schema for future use. The sharing mechanic was deliberately not implemented in MVP — the platform has no way to verify a share actually happened, making token awards for sharing inconsistent with the platform's integrity principles.

---

## Flask Project Structure

```
project/
├── app.py                  # Application entry point and route definitions. Creates the Flask
                            # app instance, configures the secret key and database path, manages
                            # the database connection lifecycle via Flask's g object and
                            # teardown_appcontext, exposes a CLI command (flask init-db) to
                            # initialise the schema, and defines the top-level routes. All
                            # database interaction is delegated to models.py — app.py only
                            # handles routing and request/response flow.
├── models.py               # Database interaction functions — the only file that writes SQL
                            # directly. Organised into four sections: user functions (create,
                            # fetch by username or id), token functions (ledger append, balance
                            # reconciliation), contribution functions (insert, fetch pending queue,
                            # fetch by id), and quiz functions (save response, retake eligibility
                            # check). Also exposes get_config() for reading platform_config rows.
                            # app.py calls these functions; it never writes SQL directly.
├── quiz.py                 # Quiz classification logic (the AI component)
├── agent.py                # AI agent — fetches sources, generates contribution digests
├── forces.py               # Forces layer logic — cross-lens mechanism queries
├── strava.py               # Strava OAuth flow and activity reward logic (post-submission)
├── schema.sql              # SQLite schema — local development only
├── schema_postgres.sql     # PostgreSQL schema — production on Render. Key differences from
                            # schema.sql: SERIAL PRIMARY KEY instead of AUTOINCREMENT,
                            # ON CONFLICT DO NOTHING instead of INSERT OR IGNORE, no PRAGMA.
├── Procfile                # Tells Render to serve via gunicorn: 'web: gunicorn app:app'
├── seed.py                 # Seeds the database with real global data. Creates a "Data Archive"
                            # system user, then seeds five lenses: Food,
                            # Housing, Mobility, Energy, and Healthcare. Also seeds the forces
                            # layer with four pre-approved systemic mechanisms and cross-lens
                            # links. Dual-mode: detects PostgreSQL vs SQLite via DATABASE_URL.
                            # Triggered via web route /seed-data in production.
├── seed_forces.py          # Original standalone forces seed script — superseded by seed.py
                            # which now handles forces seeding as part of seed_all()
├── requirements.txt        # Python dependencies
├── CHANGELOG.md            # Keeps record of any corrections
├── README.md               # This file
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── heatmap.js      # Leaflet.js heatmap logic
│       └── charts.js       # Chart.js data visualisations
└── templates/
    ├── layout.html         # Base template
    ├── index.html          # Landing page
    ├── quiz.html           # Diagnostic quiz
    ├── lens.html           # Lens view (reused for all three lenses)
    ├── force.html          # Force detail view — mechanism, evidence chain, cross-lens links
    ├── forces.html         # Forces index — all four categories listed
    ├── heatmap.html        # Global conviction map
    ├── contribute.html     # User data contribution form
    ├── validate.html       # Peer validation queue — shows digest, approve/reject buttons
    ├── register.html
    ├── login.html
    ├── commitments.html    # Our commitments - to truth, transparency, epistemic humility, and non-discrimination
    ├── privacy.html        # Privacy policy — data collected, retention, deletion request
    ├── terms.html          # Terms of use — contribution liability, content policy
    └── how_it_works.html   # AI disclosure — agent role, model used, limitations
```

---

## AI Component

There are two distinct AI components in this project, each doing a different job.

**1. Diagnostic Quiz Classifier (`quiz.py`)**

A weighted scoring system that classifies user responses to 5–7 questions into lens affinity scores. The lens with the highest score becomes the user's entry point. This runs locally in Python with no API cost. Honest note: this is rule-based classification, not machine learning. It qualifies as AI in the CS50 sense but is closer to a decision tree than a neural network. If time allows post-submission, quiz responses stored in `quiz_responses` could train a simple scikit-learn classifier as a genuine ML upgrade.

**2. Contribution Digest Agent (`agent.py`)**

When a user submits a contribution, `agent.py` is called once. It does the following in sequence:

1. Extracts the user's claim, country, and the source excerpt they provided.
2. Sends this information to a lightweight LLM (claude-haiku) with a tightly constrained prompt.
3. The prompt instructs the model to act as an evidence analyst: it assesses the quality, strengths, and gaps of the user's provided source relative to their claim, without making a final verdict on whether the claim is true or false.
4. Returns a confidence signal based on the quality of the provided evidence: `strong evidence`, `partial evidence`, `weak evidence`, or `no evidence provided`.
5. Writes the analytical summary and confidence signal to the `contribution_digests` table.
6. Additionally, the AI cleans obvious typos and erratic capitalization from the user's submission before it is saved to the database, improving readability without altering the original meaning or context."

The digest is then displayed to all peer validators on `validate.html`. The AI runs once; all validators see the same output. This keeps API cost proportional to contributions submitted, not to user count or page views.

**Design principle:** The AI presents evidence. Humans decide. User-submitted sources are analyzed for context, methodology, and internal consistency — not judged against privileged institutional databases. Where a source lacks specificity or presents a unique local perspective, the digest surfaces those details explicitly. The friction between different community perspectives is the insight. This is consistent with the platform's thesis that information asymmetry is itself a force worth documenting."

**Cost estimate:** ~$0.002–$0.01 per contribution at current model pricing. Under $1 for the first 100 contributions.

**Known limitation:** Source coverage may be uneven globally as many institutional sources available appears more complete for OECD countries. Where data is absent, the agent returns `'no data available'` and the digest says so explicitly. The UI flags this rather than hiding it.

---

## Action Plan

| Week | Dates | Goal | Done? |
|---|---|---|---|
| 1 | June 19–25 | Schema init, Flask skeleton, auth (register/login), first dataset seeded | ✓ |
| 2 | June 26–Jul 2 | Three lenses with real data, token spend system, diagnostic quiz | ✓ |
| 3 | Jul 3–9 | Heatmap, contribution flow, agent.py digest, peer validation, token earning | ✓ |
| 4 | Jul 10–16 | Polish: conditional fields in contribute.html, legal pages, CSS polish, PostgreSQL migration, deployment to Render | ✓ |
| Post-submission | Jul 17+ | real-time heatmap via WebSockets, ML quiz upgrade | ☐ |

---

**Note on lenses:** The 5 lenses are seeded with structure (lens, issues) but no institutional API data. They are designed to be community-built — users contribute data points through the contribution flow. This is a deliberate design choice: it demonstrates the platform's architecture can support new domains without code changes, and it invites community participation from day one.

**Food lens thesis:** The argument is not about raw price comparison across countries — everyone already knows food costs more in Oslo than Nairobi. The argument is about affordability relative to income, and what that affordability gap does to food choices. In many lower-income countries, ultra-processed food has become cheaper relative to local wages than fresh whole food — not because it is inherently cheap, but because it has been made artificially cheap through agricultural subsidies, supply chain consolidation, and regulatory environments shaped by the food industry. The result is that poor nutrition has become the economically rational choice for billions of people. That is not individual failure. It is a designed outcome. The health consequences — obesity, diabetes, cardiovascular disease — are measurable and global. The food lens surfaces the mechanism behind the affordability gap, not just the gap itself.

**Mobility lens thesis:** Car dependency is not a natural outcome of human preference. It is an engineered outcome produced by decades of infrastructure investment decisions, zoning laws, suburban planning models, and the systematic defunding of public transit — many of which were actively shaped by automotive and oil industry interests. The person driving two hours a day in traffic is not expressing a preference; they are trapped in a system that left them no viable alternative. The measurable consequences include cardiovascular disease from sedentary commuting, respiratory illness from vehicle emissions, financial stress from car ownership costs, urban heat islands, pedestrian death rates, and social isolation from built environments designed around vehicles rather than people. Counter-evidence is built into the lens: cycling infrastructure investment in Amsterdam, Copenhagen, Bogotá, and Nairobi demonstrates that modal shift happens when the infrastructure exists. The data shows both the damage and the proof that alternatives work.

**Note on forces data:** The forces layer is seeded with four pre-approved mechanisms during setup, establishing the quality bar. The community then builds the layer through the contribution flow — force claims go through an elevated peer validation threshold before elevation into the `forces` and `force_issue_links` tables.

---

## Known Risks — RESOLVED

✅ **Force claim elevation logic** Fully implemented with dual-threshold requirements (3 approvals + 5 minimum votes) and structural quality checks (2+ sources, 2+ lenses).
✅ **Reject threshold** Implemented via `platform_config` keys `rejection_threshold_data_point` and `rejection_threshold_force_claim`.
✅ **Flash message accuracy** — RESOLVED: `is_triggering_vote` logic accurately distinguishes between approving and late-reject voters.
✅ **Validate queue duplicates** Single-digest fetch with `ORDER BY id DESC LIMIT 1`.
✅ **Multi-contributor rewards** — All contributors (original + merged sources) receive token rewards on elevation.
✅ **Token balance sync** `reconcile_token_balance()` called after all token transactions for instant UI updates.
✅ **Unified data architecture** All data in unified `contributions` table via "Data Archive" system user.
✅ **Heatmap rendering** Mode-specific scaling, dynamic country loading from `countries.json`.
✅ **PostgreSQL migration** `Psycopg2Wrapper` in `app.py` handles compatibility transparently — `models.py` unchanged.
✅ **AI digest CONFIDENCE line** Stripped from digest display in Week 4 polish.
✅ **Conditional fields in contribute.html** JavaScript show/hide based on contribution type selection.
✅ **Force claim form** Fields now conditionally displayed based on contribution type.

### Remaining Known Risks (Accepted):
- **Multiple accounts:** No email collected, making duplicate account detection impossible by design. Token economy limits damage — opening balance requires genuine participation to grow.
- **No account recovery:** Without email, users who lose their password cannot recover their account. Disclosed explicitly at registration.
- **Quiz AI credibility:** The weighted scoring classifier in `quiz.py` is rule-based logic, not machine learning. Accurately described as a classification system, not AI in the neural network sense.
- **Agent data coverage bias:** WHO and World Bank data covers OECD countries more completely. UI surfaces gaps explicitly.
- **Validator read-only limitation:** Validators cannot add evidence of their own. Documented in `how_it_works.html`. `contribution_comments` table scoped for post-submission.
- **Sharing mechanic deliberately dropped:** Unverifiable mechanic inconsistent with platform's integrity principles. `shares` table retained in schema for potential future implementation with proper verification.
- **Render free tier spin-down:** 50-second cold start after inactivity. Mitigated by UptimeRobot ping every 5 minutes.

---

## Legal and Ethical Framework

No email address is collected at any point — a deliberate privacy-by-design decision. The platform collects only username, password hash, quiz responses, token transactions, contributions, validation votes, and share activity. Users consent explicitly at registration and can request full account deletion at any time. Full details are in privacy.html.

The platform operates under Render's standard data processing terms, which function as a GDPR-compliant Data Processing Agreement. No third-party email delivery service is used. Bot prevention uses hCaptcha — a privacy-respecting alternative to reCAPTCHA that collects no persistent identifier.

User-submitted content liability, AI use disclosure, and community editorial standards are documented in terms.html and how_it_works.html.

---

## Echo Chamber Prevention

A platform built around systemic critique will attract users who already agree. The following design decisions actively counter confirmation bias — they are architectural choices, not content moderation.

**Quiz cross-pollination (onboarding)**
After routing a user to their primary lens, the quiz result page surfaces a secondary lens with a specific data point as the hook. Exposure to a different domain is built into the first experience, not left to chance.

**Heatmap "least heard" mode**
The heatmap toggle between "highest conviction" and "least heard" actively directs attention toward underrepresented countries and issues. Amplifying the already-loud is the default failure mode of conviction platforms — this toggle is the deliberate counter.

**Forces layer as ideological bridge**
The cross-lens links in `force_issue_links` are the strongest echo chamber prevention in the architecture. A user deep in the food lens who sees that the same financial capture force also drives the housing crisis is pulled out of their silo by the evidence itself — not by a recommendation algorithm, but by the structure of the data.

**Forces layer community standards**
The forces layer is built by the community through an elevated validation threshold (`force_approval_threshold` in `platform_config`, default 5 votes, at least 3 approvals). For a force claim to be elevated, it must meet three criteria enforced by validators, not a platform editor: the mechanism is described in plain language without characterising intent; at least two independent sources are cited in the evidence chain; and the cross-lens links span at least two different lenses. Single-lens forces are issues, not forces — the distinction matters.

---

### PostgreSQL migration:
- `schema_postgres.sql` created as a dedicated production schema (`SERIAL PRIMARY KEY`, `ON CONFLICT DO NOTHING`, no `PRAGMA` statements)
- `Psycopg2Wrapper` class added to `app.py` — auto-converts `?` placeholders to `%s` and `datetime('now')` to `NOW()`, allowing `models.py` to remain in SQLite syntax throughout
- `seed.py` updated to dual-mode operation — detects `DATABASE_URL` and uses PostgreSQL or SQLite syntax accordingly
- `Procfile` added for gunicorn on Render

### Deployment:
- Live at: https://conviction-20z3.onrender.com/
- Hosted on Render free tier (web service + managed PostgreSQL)
- UptimeRobot configured to ping every 5 minutes — prevents the 50-second cold start on the free tier

Features deferred to after CS50 submission. Schema already supports all of these — they require Python and template work only.

- **Admin moderation interface** — Simple dashboard for reviewing flagged contributions, adjusting `platform_config` values, and monitoring token economy health.
- **Forces content dispute mechanism** — Flagging flow for challenging a force entry's evidence chain, with a documented review process.

**AI Attribution:** Every Python and JavaScript file in this project includes a header comment attributing Claude (Anthropic) as a development aid, describing what it assisted with in that specific file, and confirming that logic, decisions, and direction were the author's own.

---

## Submission Checklist
- [ ] Step 1: Record 3-minute video (title, name, GitHub username, edX username, city/country, date) → upload to YouTube unlisted
- [ ] Step 2: Finalise README.md (750+ words) → run `submit50 cs50/problems/2026/x/project`
- [x] Step 3 prep: Visit https://conviction-20z3.onrender.com/ to confirm live deployment
- [ ] Step 3: Visit cs50.me/cs50x to trigger certificate generation
- [ ] Deadline: Thursday, December 31, 2026 at 4:59 PM PDT
