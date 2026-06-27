# Conviction
### CS50x Final Project — Living Project Brief
**Last Updated:** June 25, 2026 (rev 12)
**Status:** Planning / Pre-build

---

#### Video Demo
`<URL to be added after recording>`

---

## Description

Conviction is a web application that helps people trace the line between what they experience daily — rising costs, poor health, environmental damage, financial precarity — and the systemic mechanisms that produce those outcomes.

Most people see symptoms. This app surfaces the machinery — and the forces operating that machinery.

Users explore three systemic lenses — **Food**, **Housing**, and **Mobility** — through real global data drawn from sources including the WHO, World Bank, FAO, and Our World in Data. But the data alone is incomplete. Behind each lens sits a fourth layer: the **underlying forces** — financial capture, regulatory arbitrage, externalised cost, information asymmetry — that operate across all three domains simultaneously. The same mechanism that keeps ultra-processed food dominant in dietary policy also keeps housing treated as an investment asset and car dependency entrenched in urban planning. The platform makes that cross-domain pattern visible.

Users take a short diagnostic quiz that personalises which lens they see first, then move through the evidence at their own depth. They register, receive tokens, and spend them on the issues they believe matter most. Their conviction aggregates into a global heatmap showing where collective concern is concentrating.

The platform is designed for people who already sense something is wrong and want to understand the mechanism — and made accessible enough that people who don't yet see the problem can be brought in through the quiz. It names no individual actors. It presents mechanisms, evidence chains, and sourced data and lets users draw their own conclusions.

---

## The Thesis

The systems that govern how people eat, live, and move are optimised for extraction, not human flourishing. The data is global, the pattern is consistent, and most people never see the mechanism — only its consequences.

The root problem is not individual greed or moral failure. It is that certain systems select for and reward short-term extraction, externalised harm, and regulatory capture — and will continue to do so regardless of who occupies positions of power within them. Change the people; the system produces new versions of the same behaviour. Change the rules; the behaviour changes. This platform is about the rules.

The platform classifies mechanisms — financial capture, regulatory arbitrage, externalised cost, information asymmetry — and presents the evidence chains that demonstrate those mechanisms operating. The evidence speaks. Users conclude.

---

## Guiding Principles

These principles are the moral foundation of the platform. They govern every decision — technical, editorial, and strategic — now and as the platform grows. They are not implementation rules; they are commitments that remain true regardless of how the technology changes.

**1. Truth is non-negotiable**
The platform pursues what the evidence actually shows, not what confirms its thesis. If the data leads somewhere uncomfortable, that is the data. The standard is universal truth — meaning truth that does not belong to any one culture, ideology, or interest group. No pressure, incentive, or reputational consideration overrides this commitment.

**2. Epistemic humility**
The platform acknowledges it can be wrong. When it is, it corrects itself publicly, transparently, and without delay. Certainty is the enemy of honest inquiry. Every methodology is visible and auditable precisely because the platform does not claim infallibility.

**3. No discrimination, no ideological gatekeeping**
Disagreement with the platform's thesis is not grounds for exclusion. The platform holds its argument openly and allows it to be challenged. Moderation exists only where content causes harm by universal moral and ethical standards — not where it challenges the platform's worldview. All voices, all geographies, all perspectives are welcome as long as they engage in good faith.

**4. Do no harm**
The platform will not surface or publish information in a way that causes direct harm to individuals or communities, even in the service of truth. How truth is told matters as much as what is told. The pursuit of systemic accountability must never become an instrument of personal destruction.

**5. The platform serves the user, not the other way around**
Every feature — the token economy, the heatmap, the quiz, the peer validation system — exists to help users understand and act. None of these mechanisms will ever be designed to manipulate user behaviour for the platform's benefit, to inflate engagement metrics, or to serve undisclosed interests. Users are participants, not products.

**6. Stewardship, not ownership**
The data contributed by communities around the world belongs to those communities in spirit. The platform is a custodian of that knowledge, not a proprietor. This means data is never sold, never used for purposes beyond the platform's stated mission, and communities always retain the right to withdraw their contributions.

**7. Transparency over neutrality**
The platform has a thesis and does not pretend otherwise. What it offers instead of neutrality is full transparency: every data point sourced and cited, every editorial decision documented, every methodology open to scrutiny. A platform that hides its assumptions is less honest than one that states them clearly and shows its working.

---

## Stack

| Layer | Technology | Notes |
|---|---|---|
| Backend | Python / Flask | Routing, business logic, API endpoints |
| Database | SQLite (dev) → PostgreSQL (prod) | Hosted free on Render |
| Frontend | Vanilla JavaScript | No framework — keeps scope tight |
| Mapping | Leaflet.js | Free, open source, handles global heatmap |
| Charts | Chart.js | Data visualisation per lens |
| Activity | Strava API (free tier) | OAuth 2.0, activity sync for token rewards — post-submission pipeline |
| AI Agent | claude-haiku / gpt-4o-mini | Contribution digest generation — runs once per contribution |
| Hosting | Render (free tier) | Zero cost deployment |
| Data Sources | WHO, World Bank, FAO, Our World in Data | Free APIs and downloadable datasets |

**Cost target: Near-zero**
The only ongoing cost is the AI agent call triggered when a user submits a contribution. Using a lightweight model (claude-haiku or gpt-4o-mini), each call costs approximately $0.002–$0.01. At low traffic — say 100 contributions in the first few months — total cost is under $1. Cost scales with contributions submitted, not with page views or users. This is the right scaling relationship. All other components remain free.

---

## Core Features (MVP)

1. **Diagnostic Quiz** — 5–7 questions classifying the user's lived experience into system impact categories. Designed for people who already sense something is wrong; accessible enough to bring in those who don't yet see it.

   **Onboarding flow:** The quiz is the final step of registration, not a separate visit. Sequence: register (username, password) → complete quiz → land on personalised lens. No email address is collected at any point. This ensures every user has a `quiz_response` stored against their `user_id` from the first interaction and personalisation feels immediate.

   **After the quiz:** The result page shows the user's primary lens and a cross-pollination hook — "people who care about food systems often find the housing lens surprising" with a specific data point as the entry. This is the first echo chamber prevention mechanism: exposure to a secondary lens is built into the onboarding result, not left to chance.

   **Retake policy:** Retakeable once every 90 days, enforced by a Python check on the most recent `quiz_responses` entry for that `user_id`. People's circumstances and concerns change — locking the result permanently is wrong. But unlimited retakes allow gaming the lens routing. The 90-day gate is stored in `platform_config` as `quiz_retake_days` and is adjustable without code changes. When a user retakes and gets a different result, the UI surfaces the shift: "your primary lens has moved from Food to Housing since you joined" — the platform reflecting personal change back to the user.

2. **Three Lenses** — Food, Housing, Mobility. Each lens presents real global data for that systemic domain, with country-level filtering. Data is pre-processed by Python at build time and stored in SQL — no per-query AI cost.

   *Why three lenses:* Scope and timeline — one person, one month, tight and polished over broad and shallow. Three lenses is sufficient to demonstrate the cross-domain pattern the platform argues. Expanding to a fourth lens (Finance, Health, Environment, or others) requires only an INSERT into the `lenses` table — no code changes. This is an explicit design goal, not a limitation.

3. **Forces Layer** — The fourth layer beneath all three lenses. Each force is a cross-domain mechanism that appears in food, housing, and mobility simultaneously. Forces are classified into four categories:
   - **Financial capture** — when financial interests shape policy outcomes in their favour
   - **Regulatory arbitrage** — exploiting gaps between jurisdictions or regulatory frameworks
   - **Externalised cost** — when the real cost of an activity is borne by those who didn't choose it
   - **Information asymmetry** — when one party in a system has access to knowledge the other doesn't

   Each force entry contains: a plain-language mechanism description, sourced evidence chain, and cross-lens links showing where the same force appears across domains. No verdicts. No named actors. Mechanisms and receipts.

4. **Token System** — Users register and immediately receive an opening balance of 10 tokens. This is deliberate — a new user who cannot act immediately will leave immediately. Ten tokens is enough to spend meaningfully across two or three issues and experience the platform's core mechanic, but not so large that scarcity loses its meaning. Tokens are spent on issues within lenses to signal conviction — a deliberate act that forces genuine prioritisation, unlike a like button.

5. **Token Earning** — Users earn additional tokens through three mechanisms:
   - Contributing local data points (pending peer validation and AI digest)
   - Validating other users' contributions (one token per validation cast)
   - Sharing content (rate-limited to prevent gaming — once per unique share per day)

6. **Peer Validation with AI Digest** — When a user submits a contribution, an AI agent (running in `agent.py`) generates a plain-language summary comparing the claim against pre-approved data sources. This digest is stored once and shown to all validators — the AI runs once per contribution, not once per validator. Validators read the digest and cast an approve or reject vote. The AI presents evidence only; it does not make a verdict.

   **User-submitted sources:** Contributors can optionally include their own evidence via two fields: a pasted text excerpt (primary) and a source URL (citation). The pasted text is the reliable input — the agent processes it directly. The URL is a citation for validators to verify manually, not a resource the agent fetches. A "verify source" link on `validate.html` opens the URL in a new tab. This approach is more robust than URL fetching, which can fail on PDFs, paywalled content, and JavaScript-rendered pages.

   **Source conflict as a feature:** Where a user-submitted source conflicts with pre-approved API data, the digest surfaces the conflict explicitly rather than resolving it. Conflict between a local source and an institutional dataset is precisely the kind of information asymmetry the forces layer documents — making it visible is consistent with the platform's thesis.

   **Agent fallback:** If a user provides no pasted text and no URL, the agent falls back to querying pre-approved sources only. If those return nothing, the digest shows `'no data available'` and the UI tells the validator: "No external data found. Evaluate based on the claim alone."

7. **Global Heatmap** — Aggregate token spend by country renders as a heatmap via Leaflet.js. Users watch their contribution shift the map. Starts as a static render; near-real-time updates (page refresh triggers new data fetch) are the target. True real-time via WebSockets is a post-submission stretch goal.

   **Echo chamber prevention toggle:** The heatmap has two modes — "highest conviction" (where token spend is densest) and "least heard" (countries and issues with real data but low token spend). The second mode actively directs attention toward underrepresented voices rather than amplifying already-loud ones. This is a JavaScript toggle on the frontend, backed by two different query parameters to the heatmap endpoint in `app.py`.

---

## SQL Schema

This is the most important architectural decision. The schema is designed to be flexible — new lenses, new issues, and new indicators are added as data rows, not as new code.

```sql
-- Core content structure
CREATE TABLE lenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,           -- e.g. 'food', 'housing', 'mobility'
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lens_id INTEGER NOT NULL REFERENCES lenses(id),
    slug TEXT UNIQUE NOT NULL,           -- e.g. 'ultra-processed-food'
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER NOT NULL REFERENCES issues(id),
    name TEXT NOT NULL,                  -- e.g. 'Obesity rate (%)'
    source TEXT,                         -- e.g. 'WHO Global Health Observatory'
    unit TEXT                            -- e.g. '%', 'USD', 'kg CO2'
);

CREATE TABLE data_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id INTEGER NOT NULL REFERENCES indicators(id),
    country_code TEXT NOT NULL,          -- ISO 3166-1 alpha-2
    year INTEGER NOT NULL,
    value REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Forces layer (fourth layer — cross-domain mechanisms beneath all lenses)
CREATE TABLE forces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,           -- e.g. 'financial-capture', 'externalised-cost'
    title TEXT NOT NULL,                 -- plain-language name
    category TEXT NOT NULL,             -- 'financial_capture', 'regulatory_arbitrage',
                                        -- 'externalised_cost', 'information_asymmetry'
    mechanism TEXT NOT NULL,            -- how it works, in plain language, sourced
    evidence_chain JSON,                -- array of {claim, source_url, data_summary} objects
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Links forces to the issues they drive (many-to-many)
-- e.g. 'financial-capture' links to 'ultra-processed-food' AND 'housing-as-asset' AND 'car-dependency'
CREATE TABLE force_issue_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    force_id INTEGER NOT NULL REFERENCES forces(id),
    issue_id INTEGER NOT NULL REFERENCES issues(id),
    explanation TEXT,                   -- how this force manifests in this specific issue
    UNIQUE(force_id, issue_id)          -- prevent duplicate links
);

-- Users and authentication
-- No email address is collected — privacy by design decision.
-- Bot prevention handled by hCaptcha at registration (no PII collected).
-- Account recovery is not possible without email — disclosed explicitly at registration.
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,         -- never store plain text passwords
    token_balance INTEGER DEFAULT 10,    -- opening balance granted at registration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data sources registry (reference points, not arbiters of truth)
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                  -- e.g. 'WHO Global Health Observatory'
    url TEXT NOT NULL,                   -- root URL
    methodology_url TEXT,                -- link to their methodology documentation
    limitations TEXT,                    -- known biases, coverage gaps, or data quality issues
    institutional_context TEXT,          -- who funds it, who governs it
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token economy
CREATE TABLE token_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,             -- positive = earned, negative = spent
    reason TEXT NOT NULL,                -- 'registration', 'contribution', 'share', 'spend', 'strava_activity'
    issue_id INTEGER REFERENCES issues(id),  -- populated when reason = 'spend'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User contributions (moderated via peer validation)
CREATE TABLE contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    indicator_id INTEGER REFERENCES indicators(id),
    country_code TEXT NOT NULL,
    value REAL,
    note TEXT,                           -- free text claim or observation
    source_url TEXT,                     -- citation URL — shown to validators as a manual check link
    source_excerpt TEXT,                 -- pasted text from source — primary input for AI agent
    contribution_type TEXT DEFAULT 'data_point', -- 'data_point' or 'force_claim'
    status TEXT DEFAULT 'pending',       -- 'pending', 'approved', 'rejected'
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Diagnostic quiz
CREATE TABLE quiz_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),  -- NULL if anonymous
    session_id TEXT,                       -- for anonymous users
    responses JSON NOT NULL,               -- stores question/answer pairs
    recommended_lens_id INTEGER REFERENCES lenses(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strava OAuth connections
CREATE TABLE strava_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    strava_athlete_id INTEGER UNIQUE NOT NULL,  -- Strava's own user ID
    access_token TEXT NOT NULL,                 -- expires every 6 hours
    refresh_token TEXT NOT NULL,                -- used to get a new access_token
    token_expires_at TIMESTAMP NOT NULL,        -- checked before every API call
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strava activities already rewarded (prevents double-earning)
CREATE TABLE strava_activities_rewarded (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    strava_activity_id INTEGER UNIQUE NOT NULL,  -- UNIQUE enforces one reward per activity
    activity_type TEXT NOT NULL,                 -- 'ride', 'run', 'walk'
    distance_meters REAL NOT NULL,               -- raw value from Strava API
    tokens_awarded INTEGER NOT NULL,
    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strava reward milestones (config table — adjust rewards without touching Python)
CREATE TABLE strava_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_type TEXT NOT NULL,    -- 'ride', 'run', 'walk'
    threshold_meters REAL NOT NULL, -- e.g. 100000 for 100km, 8000 for 8km
    tokens_awarded INTEGER NOT NULL -- e.g. 5 for cycling, 1 for run/walk
);

-- Seed data for milestones (insert once at setup)
-- INSERT INTO strava_milestones (activity_type, threshold_meters, tokens_awarded)
-- VALUES ('ride', 100000, 5), ('run', 8000, 1), ('walk', 8000, 1);

-- AI-generated source digest for each contribution (generated once, shown to all validators)
CREATE TABLE contribution_digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    summary TEXT NOT NULL,          -- plain-language summary of evidence found
    sources JSON,                   -- URLs and snippets the agent used
    confidence TEXT NOT NULL,       -- 'evidence found', 'partial evidence', 'no data available'
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Peer validation votes
CREATE TABLE contribution_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    vote TEXT NOT NULL,             -- 'approve' or 'reject'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contribution_id, user_id) -- one vote per user per contribution
);

-- Platform configuration (adjust behaviour without code changes)
CREATE TABLE platform_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed data for platform config (insert once at setup)
-- INSERT INTO platform_config (key, value, description) VALUES
-- ('validation_threshold', '2', 'Peer approvals needed to approve a data_point contribution'),
-- ('force_approval_threshold', '5', 'Peer approvals needed to elevate a force_claim into forces layer'),
-- ('tokens_per_validation', '1', 'Tokens earned for casting a validation vote'),
-- ('tokens_per_contribution', '3', 'Tokens earned when contribution is approved'),
-- ('agent_model', 'claude-haiku-4-5-20251001', 'AI model used for contribution digests'),
-- ('max_contributions_per_day', '5', 'Rate limit per user per day'),
-- ('max_shares_per_day', '3', 'Max token-earning shares per user per day'),
-- ('quiz_retake_days', '90', 'Minimum days between quiz retakes per user');

-- Share tracking (prevents gaming the sharing mechanic)
CREATE TABLE shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    content_type TEXT NOT NULL,     -- 'issue', 'lens', 'heatmap'
    content_id INTEGER,             -- references the shared item
    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key design decisions:**
- `lenses`, `issues`, `indicators`, `data_points` form a clean hierarchy. Adding a fourth lens (e.g. Finance) is an INSERT, not a schema change.
- `sources` is a registry of reference data sources — not arbiters of truth, but documented reference points with known limitations and institutional context recorded explicitly.
- `forces` sits beneath all lenses simultaneously. A force is not owned by a lens — it connects to issues across lenses via `force_issue_links`. This is the architectural expression of the platform's core argument: the same mechanism operates across domains.
- `force_issue_links` is a many-to-many join table. One force links to many issues; one issue can be linked to many forces. The `explanation` column holds the specific description of how that force manifests in that issue — not generic, but precise.
- `evidence_chain` in `forces` stores a JSON array of sourced claims. Each object contains a claim, a source URL, and a plain-language data summary. This is the "receipts" layer — the mechanism is not asserted, it is demonstrated.
- `users` stores no email address — a deliberate privacy-by-design decision. Bot prevention is handled by hCaptcha at registration. Account recovery is not possible and this is disclosed explicitly to users at registration.
- `token_transactions` is an append-only ledger. `token_balance` on `users` is a derived cache — always recalculable from the ledger. Python always writes to the ledger first; balance is never updated independently.
- `contributions` has a `contribution_type` field — `'data_point'` for regular contributions, `'force_claim'` for forces layer nominations. Python in `models.py` routes approved force claims into `forces` and `force_issue_links` when the `force_approval_threshold` in `platform_config` is reached.
- `contribution_digests` stores the AI agent's output once per contribution. All validators see the same digest — the agent never runs more than once per contribution regardless of how many validators review it.
- `contribution_votes` has a `UNIQUE` constraint on `(contribution_id, user_id)` — the database enforces one vote per user per contribution.
- `confidence` in `contribution_digests` uses plain-language values (`'evidence found'`, `'partial evidence'`, `'no data available'`) — the AI reports what it found, not what it concluded.
- `platform_config` is a key-value config table. Validation thresholds, token rewards, AI model choice, and rate limits are all rows — adjustable without touching Python code.
- `shares` table rate-limits the sharing mechanic. Python checks daily share count against `platform_config.max_shares_per_day` before awarding tokens.
- `quiz_responses` stores raw JSON so question wording can evolve without a schema migration.
- `strava_activities_rewarded` has a `UNIQUE` constraint on `strava_activity_id` — hard guard against double-rewarding the same activity.
- `strava_milestones` is a config table. Reward values are rows, not hardcoded logic.
- `strava_connections` stores both `access_token` and `refresh_token`. Flask checks `token_expires_at` before every Strava API call and uses the refresh token to obtain a new access token when stale.

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
├── schema.sql              # SQL schema (run once to initialise DB)
├── seed.py                 # Seeds the database with real global data. Runs outside Flask's
                            # request context with its own SQLite connection — independent of
                            # app.py's get_db. Currently seeds the food lens with one issue
                            # (ultra-processed-food), one indicator (adult obesity rate), and
                            # real WHO GHO API data points for 15 countries across Africa, Asia,
                            # Latin America, and Western regions. WHO API returns ISO 3166-1
                            # alpha-3 country codes — conversion to alpha-2 for Leaflet.js
                            # handled at the heatmap endpoint in Week 3, not here.
├── seed_forces.py          # Script to seed forces and force_issue_links data
├── requirements.txt        # Python dependencies
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
    ├── privacy.html        # Privacy policy — data collected, retention, deletion request
    ├── terms.html          # Terms of use — contribution liability, content policy
    ├── how_it_works.html   # AI disclosure — agent role, model used, limitations
    └── strava.html         # Strava connection and activity summary (post-submission)
```

---

## AI Component

There are two distinct AI components in this project, each doing a different job.

**1. Diagnostic Quiz Classifier (`quiz.py`)**

A weighted scoring system that classifies user responses to 5–7 questions into lens affinity scores. The lens with the highest score becomes the user's entry point. This runs locally in Python with no API cost. Honest note: this is rule-based classification, not machine learning. It qualifies as AI in the CS50 sense but is closer to a decision tree than a neural network. If time allows post-submission, quiz responses stored in `quiz_responses` could train a simple scikit-learn classifier as a genuine ML upgrade.

**2. Contribution Digest Agent (`agent.py`)**

When a user submits a contribution, `agent.py` is called once. It does the following in sequence:

1. Constructs a search query from the contribution's claim, country, and indicator
2. Fetches relevant data from pre-approved free sources (WHO API, World Bank API, Our World in Data CSVs)
3. Sends the retrieved data plus the original claim to a lightweight LLM (claude-haiku or gpt-4o-mini) with a tightly constrained prompt
4. The prompt instructs the model to summarise what the evidence says relative to the claim — not to make a verdict
5. Returns a `confidence` signal: `'evidence found'`, `'partial evidence'`, or `'no data available'`
6. Writes the summary and sources to `contribution_digests`

The digest is then displayed to all peer validators on `validate.html`. The AI runs once; all validators see the same output. This keeps API cost proportional to contributions submitted, not to user count or page views.

**Design principle:** The AI presents evidence. Humans decide. Pre-approved sources — WHO, World Bank, FAO, Our World in Data — are reference points for comparison, not arbiters of truth. Where a user-submitted source diverges from institutional data, the digest surfaces that divergence explicitly. The conflict is the insight. This is consistent with the platform's thesis that information asymmetry is itself a force worth documenting.

**Cost estimate:** ~$0.002–$0.01 per contribution at current model pricing. Under $1 for the first 100 contributions.

**Known limitation:** Source coverage is uneven globally. WHO and World Bank data is more complete for OECD countries. Where data is absent, the agent returns `'no data available'` and the digest says so explicitly. The UI flags this rather than hiding it.

---

## Action Plan

| Week | Dates | Goal | Done? |
|---|---|---|---|
| 1 | June 19–25 | Schema init, Flask skeleton, auth (register/login), first dataset seeded | ✓ |
| 2 | June 26–Jul 2 | Three lenses with real data, token spend system, diagnostic quiz | ☐ |
| 3 | Jul 3–9 | Heatmap, contribution flow, agent.py digest, peer validation, token earning | ☐ |
| 4 | Jul 10–16 | Polish, sharing mechanic, README finalise, video, deploy to Render, submit | ☐ |
| Post-submission | Jul 17+ | Strava OAuth integration, real-time heatmap via WebSockets, ML quiz upgrade | ☐ |

---

## Data Sources

| Layer | Dataset | Source | Format |
|---|---|---|---|
| Food lens | Global dietary data, obesity rates, food security index | WHO / FAO | API / CSV |
| Housing lens | Housing cost-to-income ratio, homelessness rates | World Bank | API |
| Mobility lens | Car dependency index, cycling infrastructure, transit access | Our World in Data | CSV |
| Forces layer | Lobbying expenditure, regulatory change timelines, industry funding of research | investigative journalism databases, academic papers, government disclosure records | Manual curation → JSON seed data |

**Note on reference sources:** WHO, World Bank, FAO, and Our World in Data are used as reference points for comparison — not as golden sources or arbiters of truth. Each has documented institutional context, funding relationships, and coverage limitations recorded in the `sources` table. Where user-contributed evidence diverges from these sources, the divergence is surfaced explicitly in the AI digest rather than resolved in favour of the institutional source.

**Food lens thesis:** The argument is not about raw price comparison across countries — everyone already knows food costs more in Oslo than Nairobi. The argument is about affordability relative to income, and what that affordability gap does to food choices. In many lower-income countries, ultra-processed food has become cheaper relative to local wages than fresh whole food — not because it is inherently cheap, but because it has been made artificially cheap through agricultural subsidies, supply chain consolidation, and regulatory environments shaped by the food industry. The result is that poor nutrition has become the economically rational choice for billions of people. That is not individual failure. It is a designed outcome. The health consequences — obesity, diabetes, cardiovascular disease — are measurable and global. The food lens surfaces the mechanism behind the affordability gap, not just the gap itself.

**Mobility lens thesis:** Car dependency is not a natural outcome of human preference. It is an engineered outcome produced by decades of infrastructure investment decisions, zoning laws, suburban planning models, and the systematic defunding of public transit — many of which were actively shaped by automotive and oil industry interests. The person driving two hours a day in traffic is not expressing a preference; they are trapped in a system that left them no viable alternative. The measurable consequences include cardiovascular disease from sedentary commuting, respiratory illness from vehicle emissions, financial stress from car ownership costs, urban heat islands, pedestrian death rates, and social isolation from built environments designed around vehicles rather than people. Counter-evidence is built into the lens: cycling infrastructure investment in Amsterdam, Copenhagen, Bogotá, and Nairobi demonstrates that modal shift happens when the infrastructure exists. The data shows both the damage and the proof that alternatives work.

**Note on forces data:** The forces layer is community-built, not editor-curated. Users submit force claims via the contribution flow — these go through an elevated peer validation threshold (`force_approval_threshold` in `platform_config`) before being elevated into the `forces` and `force_issue_links` tables. The platform founder seeds two or three initial force entries during user testing to establish the quality bar. After that, the community builds the layer. `seed_forces.py` handles the initial seed only.

---

## Known Risks

- **Forces layer editorial burden:** Addressed — forces layer is community-built via elevated peer validation threshold, not manually curated by the platform founder. Initial seed entries establish the quality bar during user testing. See Data Sources section.
- **Multiple accounts:** No email address is collected, making duplicate account detection impossible by design. Mitigation: the token economy limits the damage — opening balance of 10 tokens requires genuine participation to grow, and peer validation requires coordination across fake accounts to manipulate. Acknowledged as a known limitation in `privacy.html`.
- **No account recovery:** Without email, users who lose their password cannot recover their account. Disclosed explicitly at registration. Acceptable trade-off given the privacy benefit.
- **Echo chamber risk:** Addressed — see Echo Chamber Prevention section. Key mechanisms: quiz cross-pollination, heatmap "least heard" toggle, forces cross-lens links, contribution diversity signal, dissenting data shown explicitly.
- **Legal exposure:** Addressed — see Legal and Ethical Framework section. Key mitigations: privacy policy page, consent checkbox at registration, terms of use, AI disclosure page, data deletion mechanism.
- **Heatmap "real-time" expectation:** True real-time requires WebSockets — outside CS50 scope. Target is near-real-time: map refreshes on page load. WebSockets are post-submission.
- **Quiz AI credibility:** The weighted scoring classifier in `quiz.py` is rule-based logic, not machine learning. Call it a "classification system" in the README unless upgraded to scikit-learn post-submission.
- **Agent.py data coverage bias:** WHO and World Bank data covers OECD countries more completely. Where data is absent, the UI says so explicitly: "No global data found for this region. Your contribution may be filling a real gap."
- **Peer validation cold start:** Set `validation_threshold` to 1 in `platform_config` for MVP. Admin acts as first validator. Threshold increases as user base grows.
- **Sharing mechanic gaming:** `shares` table tracks daily count per user. Python checks against `platform_config.max_shares_per_day` before awarding tokens.
- **Token balance drift:** Ledger is always written first inside a database transaction. Balance derived from ledger on any discrepancy.
- **AI agent cost at scale:** Negligible at low traffic. `platform_config.max_contributions_per_day` rate-limits submissions without a code deploy.
- **Validator read-only limitation:** Validators can read the AI digest and the contributor's submitted evidence, but cannot add, annotate, or counter-submit evidence of their own. A validator who knows of a relevant source has no mechanism to surface it. This is a deliberate scope decision for MVP. Acknowledged explicitly in `how_it_works.html` — "validators evaluate evidence submitted with the contribution; they cannot add new evidence at this stage." A `contribution_comments` table is scoped for post-submission.
- **Alpha-3 vs alpha-2 country codes:** WHO API returns ISO 3166-1 alpha-3 codes (e.g. `KEN`, `PHL`). `data_points` stores these natively. Leaflet.js requires alpha-2 (e.g. `KE`, `PH`) for map rendering. Conversion handled via a lookup dictionary in the heatmap endpoint in `app.py` during Week 3 — no schema change required.
- **Strava OAuth complexity:** Deferred to post-submission. Schema ready; `strava.py` not built.

---

## Legal and Ethical Framework

**Data privacy and user consent**
No email address is collected at any point — a deliberate privacy-by-design decision that eliminates the most significant PII liability. The platform collects only: username, password hash, quiz responses, token transactions, contributions, validation votes, and share activity. All of this is disclosed in `privacy.html`. Users consent explicitly at registration via a checkbox. Users can request full account deletion at any time — a Python function anonymises or removes all rows linked to their `user_id`. Contributions and votes are retained in anonymised form to preserve evidence integrity; all other personal data is deleted within 30 days of request.

The platform operates under Render's standard data processing terms, which function as a GDPR-compliant Data Processing Agreement for infrastructure. No third-party email delivery service is used, eliminating the most common source of DPA obligation for small platforms.

**Bot prevention**
hCaptcha is used at registration — a privacy-respecting alternative to Google's reCAPTCHA that does not send user behaviour data to third parties. No persistent identifier is collected from this process.

**Account recovery**
Not possible without email. This is disclosed clearly at registration: "Choose a username and password you will remember. We cannot recover your account if you lose access." This is an intentional trade-off in favour of user privacy.

**User-submitted content liability**
Terms of use (`terms.html`) state clearly: contributions represent the submitter's own research; the AI digest is an evidence summary, not an endorsement; the platform reserves the right to remove content that cannot be sourced; the forces layer is community-built and the platform does not guarantee its accuracy. A reporting mechanism for disputed contributions is required.

**AI use disclosure**
`how_it_works.html` — visible to all users, registered or not — explains that an AI agent generates contribution digests, which model is used, what its limitations are, that pre-approved sources are reference points not arbiters of truth, and that the AI presents evidence only without making moderation decisions.

**Community editorial responsibility**
The forces layer is built and maintained by the community through the peer validation system, not by a platform editor. The platform's responsibility is to maintain the validation standards defined in `platform_config`, correct systemic errors when identified, and ensure the methodology remains visible and auditable. These obligations flow directly from Guiding Principles 1, 2, and 7.

---

## Echo Chamber Prevention

A platform built around systemic critique will attract users who already agree. The following design decisions actively counter confirmation bias — they are architectural choices, not content moderation.

**Quiz cross-pollination (onboarding)**
After routing a user to their primary lens, the quiz result page surfaces a secondary lens with a specific data point as the hook. Exposure to a different domain is built into the first experience, not left to chance.

**Heatmap "least heard" mode**
The heatmap toggle between "highest conviction" and "least heard" actively directs attention toward underrepresented countries and issues. Amplifying the already-loud is the default failure mode of conviction platforms — this toggle is the deliberate counter.

**Forces layer as ideological bridge**
The cross-lens links in `force_issue_links` are the strongest echo chamber prevention in the architecture. A user deep in the food lens who sees that the same financial capture force also drives the housing crisis is pulled out of their silo by the evidence itself — not by a recommendation algorithm, but by the structure of the data.

**Contribution diversity signal**
On `validate.html`, validators see a geographic diversity indicator for existing approved contributions on that issue — e.g. "14 contributions, 12 from North America." This gives validators context for whether approving another contribution from the same region adds genuine diversity or reinforces existing concentration.

**Dissenting data shown explicitly**
Where pre-approved API data complicates or contradicts the platform's thesis on a specific issue, that data is displayed on the lens page — not hidden. A lens that only shows confirming evidence is propaganda. One that shows the full picture including inconvenient data is analysis. The platform's credibility depends on the latter.

**Forces layer community standards**
The forces layer is built by the community through an elevated validation threshold (`force_approval_threshold` in `platform_config`, default 5 approvals). For a force claim to be elevated, it must meet three criteria enforced by validators, not a platform editor: the mechanism is described in plain language without characterising intent; at least two independent sources are cited in the evidence chain; and the cross-lens links span at least two different lenses. Single-lens forces are issues, not forces — the distinction matters. These criteria are published openly so validators know the standard they are applying.

---

## Pending Design Decisions

- **Forces content disputes** — what happens when a user challenges a force entry's evidence chain. Needs a flagging mechanism and a documented review process. Deferred to post-submission.

---

## Post-Submission Pipeline

Features deferred to after CS50 submission. Schema already supports all of these — they require Python and template work only.

- **Strava integration** — `strava.py` and `strava.html`. OAuth 2.0 flow, activity sync, milestone rewards. Tables already in schema.
- **Real-time heatmap** — WebSockets via Flask-SocketIO. Map updates pushed to all connected clients when a token is spent.
- **Quiz ML upgrade** — Replace weighted scoring in `quiz.py` with a scikit-learn classifier trained on accumulated `quiz_responses` data.
- **Reputation-weighted validation** — Validator votes weighted by account age and token history. Reduces gaming risk as user base grows.
- **Admin moderation interface** — Simple dashboard for reviewing flagged contributions, adjusting `platform_config` values, and monitoring token economy health.
- **Forces content dispute mechanism** — Flagging flow for challenging a force entry's evidence chain, with a documented review process.

**AI Attribution:** Every Python and JavaScript file in this project includes a header comment attributing Claude (Anthropic) as a development aid, describing what it assisted with in that specific file, and confirming that logic, decisions, and direction were the author's own. This satisfies CS50's AI citation requirement and documents the collaboration honestly.

---

## Conversation Context (for new Claude sessions)

Paste this section at the start of any new conversation:

> I am building a CS50x final project called Conviction — a Flask/Python/JS/SQLite web app where users explore global systemic issues through three lenses (food, housing, mobility) and a fourth forces layer surfacing cross-domain mechanisms. Users spend tokens to signal conviction, earn tokens by contributing and validating data, and watch a global heatmap with a "least heard" toggle. The quiz is the final onboarding step, retakeable every 90 days. User contributions include pasted source text and a citation URL — the AI agent processes the text, validators check the URL manually. Pre-approved data sources (WHO, World Bank, FAO) are reference points not arbiters of truth — divergence between user sources and institutional data is surfaced as insight. The forces layer is community-built via elevated peer validation threshold, not editor-curated. No email address is collected — privacy by design, hCaptcha for bot prevention, no account recovery. Registration grants 10 opening tokens immediately. The platform has seven guiding principles, documented legal/ethical framework, and echo chamber prevention architecture. Strava is post-submission; schema is ready. All code files will include AI attribution comments. Full schema, stack, file structure, and action plan are in README.md. I am a technical PM with mid-level engineering knowledge — explain concepts clearly, don't oversimplify, flag syntax connecting to other functions or files. We are currently on: **[INSERT CURRENT WEEK/TASK]**.

---

## Glossary

Plain-language definitions of every technology and concept used in this project. Written for reference during the build — not academic definitions, but working ones.

---

**Backend**
The part of the application the user never sees directly. It runs on a server, processes logic, talks to the database, and returns data to the frontend. In this project, the backend is Flask running in Python. When a user spends a token, the backend is what records the transaction, checks the balance, and updates the heatmap data.

**Frontend**
The part of the application the user sees and interacts with — buttons, charts, maps, forms. In this project, the frontend is HTML templates rendered by Flask, styled with CSS, and made interactive with vanilla JavaScript. The frontend asks the backend for data; the backend provides it.

**Flask**
A lightweight Python web framework. It handles incoming HTTP requests (someone visiting a URL), runs the appropriate Python function, and returns a response (usually an HTML page or JSON data). Think of it as the traffic controller between the user's browser and your Python logic.

**Python**
The programming language the backend is written in. Chosen for this project because it is readable, well-documented, and has strong libraries for data processing, API calls, and AI integration.

**SQL (Structured Query Language)**
The language used to communicate with a database. You write SQL to ask questions ("give me all contributions from this country") or make changes ("insert this new token transaction"). The database understands SQL regardless of what programming language your application is written in.

**SQLite**
A database that lives entirely in a single file on your computer. No server required, no configuration, no installation beyond a Python library. Ideal for development because it is simple and fast to set up. Not suitable for production because only one process can write to it at a time — which breaks when multiple users or servers try to write simultaneously.

**PostgreSQL**
A full database server — a separate running process that your application connects to over a network. Handles multiple simultaneous connections cleanly, has better performance under load, and is the industry standard for production web applications. In this project, SQLite is used during development on your laptop; PostgreSQL is used when the app is deployed to Render. The switch requires only a configuration change — the SQL schema itself is the same.

**Render**
A cloud hosting platform — the "landlord" that provides the server your application runs on. Render receives incoming web requests, runs your Flask app, and manages environment variables, HTTPS certificates, and deployment. Also offers a managed PostgreSQL service, meaning both the app and the database can live on Render with no additional providers needed.

**Database**
An organised system for storing and retrieving data persistently. Unlike a variable in Python that disappears when the program stops, a database retains data between sessions, server restarts, and deployments. In this project, the database stores users, tokens, contributions, heatmap data, and everything else the platform needs to remember.

**Schema**
The blueprint of a database — it defines what tables exist, what columns each table has, what data types those columns accept, and what relationships exist between tables. In this project, `schema.sql` is run once when the database is first created. It is the most important architectural document in the project.

**Table**
A database structure that holds rows of related data — like a spreadsheet with defined columns. In this project, `users` is a table, `contributions` is a table, `token_transactions` is a table. Each row in a table is one record.

**Primary Key**
A column in a table that uniquely identifies each row. In this project, every table has an `id` column that is the primary key — no two rows in the same table can have the same `id`. SQLite and PostgreSQL generate these automatically with `AUTOINCREMENT`.

**Foreign Key**
A column in one table that references the primary key of another table. In this project, `contributions.user_id` is a foreign key — it references `users.id`, linking each contribution to the user who submitted it. Foreign keys are how relationships between tables are expressed.

**UNIQUE Constraint**
A rule enforced by the database that prevents two rows from having the same value in a specified column. In this project, `contribution_votes` has a UNIQUE constraint on `(contribution_id, user_id)` — meaning the database itself prevents a user from voting twice on the same contribution, regardless of what the Python code does.

**JSON (JavaScript Object Notation)**
A text format for storing structured data. Looks like `{"key": "value", "numbers": [1, 2, 3]}`. In this project, `quiz_responses` stores question-answer pairs as JSON, and `evidence_chain` in `forces` stores an array of sourced claims as JSON. Useful when the structure of the data might change over time — you can add new fields without changing the database schema.

**API (Application Programming Interface)**
A defined way for two pieces of software to talk to each other. In this project, WHO, World Bank, and Our World in Data expose APIs — you send a structured request to their server and receive structured data back. Flask also exposes its own internal API endpoints — URLs that return JSON data to the JavaScript frontend rather than HTML pages.

**HTTP / HTTPS**
HTTP is the protocol browsers use to request web pages and data. HTTPS is the encrypted version — the S stands for Secure. All communication between users' browsers and your server should use HTTPS. Render enforces this automatically. Without HTTPS, data in transit — including passwords — is readable to anyone intercepting the connection.

**Environment Variable**
A configuration value stored outside your code — on the server, not in a file that gets committed to version control. In this project, your Anthropic API key, database connection string, and hCaptcha secret key are stored as environment variables on Render. This prevents sensitive credentials from appearing in your codebase or on GitHub.

**OAuth 2.0**
A standard protocol for letting users grant your application limited access to another service without sharing their password. In this project, Strava integration (post-submission) uses OAuth 2.0 — users click "connect Strava," get redirected to Strava's login page, and Strava sends your app a token that allows it to read activity data. Your app never sees the user's Strava password.

**Token (authentication context)**
Not to be confused with the platform's conviction tokens — in the context of OAuth and API authentication, a token is a string of characters that proves your application has been granted permission to access a service. Strava access tokens expire every 6 hours; the refresh token is used to obtain a new one automatically.

**Hashing**
A one-way mathematical transformation that converts any input into a fixed-length string. The same input always produces the same output, but you cannot reverse the output back to the input. In this project, passwords are hashed before being stored — if the database is compromised, attackers see the hash, not the password. `werkzeug.security` in Flask handles this using bcrypt.

**Salt (cryptography)**
A random string added to data before hashing to prevent attackers from using pre-computed tables of common hashes. Two users with the same password will have different hashes if different salts are used. In this project, Flask's `werkzeug.security` handles salting automatically for passwords.

**hCaptcha**
A bot-prevention service that presents users with a challenge at registration to confirm they are human. A privacy-respecting alternative to Google's reCAPTCHA — it does not send user behaviour data to Google. In this project, hCaptcha is used at registration as the only identity check, since no email address is collected.

**Session**
A way of remembering who a user is across multiple HTTP requests. HTTP is stateless — each request is independent and the server has no memory of previous ones. Flask uses a signed cookie stored in the browser to maintain session state, so a logged-in user remains logged in as they navigate between pages.

**Cookie**
A small piece of data stored in the user's browser and sent back to the server with every request. Flask uses a session cookie to track logged-in users. Cookies can be inspected by the user but the session cookie is cryptographically signed — it cannot be forged without knowing the Flask secret key.

**Leaflet.js**
An open-source JavaScript library for interactive maps. In this project, Leaflet renders the global heatmap showing where conviction is concentrating. Free, well-documented, and does not require an API key for basic usage.

**Chart.js**
An open-source JavaScript library for data visualisation — bar charts, line charts, pie charts. In this project, Chart.js renders the data visualisations within each lens page.

**Virtual Machine (VM)**
A piece of software that simulates a complete computer — with its own operating system, memory, and storage — running on shared physical hardware. Cloud providers rent VMs by the hour. Render's infrastructure runs on VMs, though this is abstracted away from you as the developer.

**Container**
A lightweight alternative to a VM. Instead of simulating a full operating system, a container packages just your application and its dependencies. Starts in seconds rather than minutes, uses fewer resources, and is portable across environments. Docker is the standard tool for building containers. Render runs your Flask app inside a container.

**Kubernetes**
A system for managing many containers running across many servers — deciding where each runs, restarting crashed containers, scaling up when traffic spikes, and scaling down when it drops. Relevant at significant scale; abstracted away entirely by Render for this project. Understanding it conceptually is useful for future architectural conversations.

**Horizontal Scaling**
Adding more servers to share load rather than making one server more powerful. Requires a database that can handle multiple simultaneous connections — which is why PostgreSQL replaces SQLite in production. When Conviction grows, horizontal scaling means spinning up additional Flask instances on Render, all connecting to the same PostgreSQL database.

**Vertical Scaling**
Making one server more powerful — more CPU, more RAM, more storage. Simpler than horizontal scaling but has a ceiling: there is a limit to how powerful a single machine can be, and it is more expensive per unit of capacity.

**Render Free Tier**
Render's no-cost hosting option. Suitable for a CS50 submission and early-stage deployment. Limitations include the server spinning down after periods of inactivity (causing a slow first load), limited compute resources, and a single server instance. Upgrading to a paid tier removes these limitations when traffic demands it.

**GDPR (General Data Protection Regulation)**
European Union regulation governing how personal data is collected, stored, processed, and deleted. Applies to any platform that serves EU users, regardless of where the platform is hosted. Key obligations: disclose what data you collect and why, obtain consent, allow users to request deletion, report breaches within 72 hours. In this project, the no-email decision eliminates the most significant GDPR liability.

**PIPEDA (Personal Information Protection and Electronic Documents Act)**
Canadian federal privacy legislation with similar principles to GDPR. Applies to this project given the platform founder is based in Canada. Render's infrastructure and the no-email approach keep compliance obligations manageable.

**PII (Personally Identifiable Information)**
Any data that can be used to identify a specific individual — name, email address, phone number, IP address, location data. In this project, the only PII collected is the username (which may or may not be a real name — the user's choice) and the IP address logged by default by Flask and Render's infrastructure. No email address is collected by design.

**Data Processing Agreement (DPA)**
A legal contract between a data controller (you) and a data processor (a third-party service handling data on your behalf) required under GDPR. Render's standard terms of service function as a DPA. No additional DPA is required because no email delivery service is used.

**Seed Data**
Initial data inserted into a database when it is first set up — not user-generated data, but the baseline content the application needs to function. In this project, `seed.py` loads real global data from WHO, World Bank, and Our World in Data APIs into `lenses`, `issues`, `indicators`, and `data_points`. `seed_forces.py` inserts the initial force entries. `platform_config` and `strava_milestones` are seeded with INSERT statements documented in `schema.sql`.

**Append-Only Ledger**
A database pattern where records are only ever added, never modified or deleted. The `token_transactions` table in this project is an append-only ledger — every token movement is a new row. The current balance is always calculated by summing the ledger. This prevents data loss from bugs and provides a complete audit trail of every token movement.

---

- [ ] Step 1: Record 3-minute video (title, name, GitHub username, edX username, city/country, date) → upload to YouTube unlisted
- [ ] Step 2: Finalise README.md (750+ words) → run `submit50 cs50/problems/2026/x/project`
- [ ] Step 3: Visit cs50.me/cs50x to trigger certificate generation
- [ ] Deadline: Thursday, December 31, 2026 at 4:59 PM PDT

---

*This README is a living document. Update it at each major milestone and at the start of each new Claude conversation.*
