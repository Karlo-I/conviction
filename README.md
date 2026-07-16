# Conviction
### CS50x Final Project — Living Project Brief
**AI Assistance Disclosure:** This `README.md` file was developed with the assistance of AI language models (Claude and Qwen) to refine phrasing, improve formatting, and ensure clarity. All project architecture, design decisions, feature logic, and technical direction are strictly the author's own.

**Last Updated:** July 14, 2026 (rev 18)

**Status:** Deployed — Live at https://conviction-20z3.onrender.com/

---

#### Video Demo
`<URL to be added after recording>`

---

## Description

Conviction is a web application that helps people trace the line between what they experience daily — rising costs, poor health, environmental damage, financial precarity — and the systemic mechanisms that produce those outcomes.

Most people see symptoms. This app surfaces the machinery — and the forces operating that machinery.

Users explore five (seeded) systemic lenses to begin with — **Food**, **Housing**, **Mobility**, **Energy**, and **Healthcare** — which will increase as more users propose new lenses that matters. But the data alone is incomplete. Behind each lens sits a fourth layer: the **underlying forces** — financial capture, regulatory arbitrage, externalised cost, information asymmetry — that operate across all domains simultaneously. The same mechanism that keeps ultra-processed food dominant in dietary policy also keeps housing treated as an investment asset and car dependency entrenched in urban planning. The platform makes that cross-domain pattern visible. There are four forces seeded initially, they too will grow over time as the number of users grow. 

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
| AI Agent | claude-haiku-4-5-20251001 | Contribution digest generation |
| Hosting | Render (free tier) | Live at https://conviction-20z3.onrender.com/ |

**Cost target: Near-zero**
The only ongoing cost is the AI agent call triggered when a user submits a contribution. Using a lightweight model (claude-haiku or gpt-4o-mini), each call costs approximately $0.002–$0.01. At low traffic — say 100 contributions in the first few months — total cost is under $1. Cost scales with contributions submitted, not with page views or users. This is the right scaling relationship. All other components remain free.

---

## Core Features (MVP)

1. **Diagnostic Quiz** — 5–7 questions classifying the user's lived experience into system impact categories. Designed for people who already sense something is wrong; accessible enough to bring in those who don't yet see it.

   **Onboarding flow:** The quiz is the final step of registration, not a separate visit. Sequence: register (username, password) → complete quiz → land on personalised lens. No email address is collected at any point. This ensures every user has a `quiz_response` stored against their `user_id` from the first interaction and personalisation feels immediate.

   **After the quiz:** The result page shows the user's primary lens and a cross-pollination hook — "people who care about food systems often find the housing lens surprising" with a specific data point as the entry. This is the first echo chamber prevention mechanism: exposure to a secondary lens is built into the onboarding result, not left to chance.

   **Retake policy:** Retakeable once every 90 days, enforced by a Python check on the most recent `quiz_responses` entry for that `user_id`. People's circumstances and concerns change — locking the result permanently is wrong. But unlimited retakes allow gaming the lens routing. The 90-day gate is stored in `platform_config` as `quiz_retake_days` and is adjustable without code changes. When a user retakes and gets a different result, the UI surfaces the shift: "your primary lens has moved from Food to Housing since you joined" — the platform reflecting personal change back to the user.

2. **Five Lenses** — Food, Housing, Mobility, Energy, and Healthcare. All five lenses are seeded with structural content (lenses, issues, and indicators) but no pre-loaded institutional data. They are designed to be community-built from day one, demonstrating that the platform's architecture can support new domains without code changes.

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

6. **Peer Validation with AI Digest** — When a user submits a contribution, an AI agent (running in `agent.py`) generates a plain-language summary analyzing the user's provided source. This digest is generated once and shown to all validators, keeping API costs proportional to submissions, not page views. Validators read the digest and cast an approve or reject vote. The AI presents evidence only; it does not make a verdict.

   **User-submitted sources:** Contributors can optionally include their own evidence via two fields: a pasted text excerpt (primary) and a source URL (citation). The pasted text is the reliable input — the agent processes it directly to assess its quality, strengths, and gaps relative to the claim. The URL is a citation for validators to verify manually.

   **Surfacing gaps as a feature:** Where a user-submitted source lacks specificity, dates, or methodological grounding, the digest surfaces those gaps explicitly. This friction is precisely the kind of information asymmetry the forces layer documents — making it visible is consistent with the platform's thesis.

   **Agent fallback:** If a user provides no pasted text and no URL, the agent falls back to querying pre-approved sources only. If those return nothing, the digest shows `no data available` and the UI tells the validator: "No external data found. Evaluate based on the claim alone."

7. **Global Heatmap** — Aggregate token spend by country renders as a heatmap via Leaflet.js. Users watch their contribution shift the map. Starts as a static render; near-real-time updates (page refresh triggers new data fetch) are the target. True real-time via WebSockets is a post-submission stretch goal.

   **Echo chamber prevention toggle:** The heatmap has two modes — "highest conviction" (where token spend is densest) and "least heard" (countries and issues with real data but low token spend). The second mode actively directs attention toward underrepresented voices rather than amplifying already-loud ones. This is a JavaScript toggle on the frontend, backed by two different query parameters to the heatmap endpoint in `app.py`.

---

## SQL Schema

This is the most important architectural decision. The schema is designed to be flexible — new lenses, new issues, and new indicators are added as data rows, not as new code. Two schema files exist: `schema.sql` for SQLite (local development) and `schema_postgres.sql` for PostgreSQL (production on Render). The `Psycopg2Wrapper` class in `app.py` handles syntax differences transparently so `models.py` uses SQLite syntax throughout.

| Table | Purpose |
|-------|---------|
| `lenses`, `issues`, `indicators` | Hierarchical content structure (5 lenses, multiple issues each) |
| `forces`, `force_issue_links` | Cross-lens mechanisms (financial capture, regulatory arbitrage, etc.) |
| `users`, `token_transactions` | Privacy-first auth (no email) + append-only token ledger |
| `contributions`, `contribution_digests` | Unified data architecture — all peer-validated evidence |
| `quiz_responses` | Diagnostic quiz routing (stored as JSON for flexibility) |
| `platform_config` | Key-value config for thresholds, rewards, rate limits |

**Key design decisions:**
- `lenses`, `issues`, `indicators` form a clean hierarchy. Adding a new lens is an INSERT, not a schema change — proven during build when Energy and Healthcare were added with no code changes.
- `Unified data architecture`: The `contributions` table stores ALL data — both seeded data (via the "Data Archive" system user) and user-submitted contributions. There is no separate `data_points` table. This reflects the platform's philosophical commitment: all knowledge is built by the community through peer validation, not handed down from authority.
- `sources` is a registry of reference data sources — not arbiters of truth, but documented reference points with known limitations and institutional context recorded explicitly.
- `forces` sits beneath all lenses simultaneously. A force is not owned by a lens — it connects to issues across lenses via `force_issue_links`.
- `evidence_chain` in `forces` stores a JSON array of sourced claims. Each object contains a claim, a source URL, and a plain-language data summary.
- `users` stores no email address — a deliberate privacy-by-design decision. Bot prevention is handled by hCaptcha at registration. Account recovery is not possible and this is disclosed explicitly to users at registration.
- `token_transactions` is an append-only ledger. `token_balance` on `users` is a derived cache — always recalculable from the ledger. Python always writes to the ledger first; balance is never updated independently.
- `contributions` has a `contribution_type` field — `data_point`, `force_claim`, or `lens_proposal`. Python in `models.py` routes approved force claims into `forces` and `force_issue_links` when the `force_approval_threshold` and `minimum_total_votes_force_claim` in `platform_config` are reached.
- `contribution_digests` stores the AI agent's output once per contribution. All validators see the same digest — the agent never runs more than once per contribution.
- `contribution_votes` has a `UNIQUE` constraint on `(contribution_id, user_id)` — the database enforces one vote per user per contribution.
- `confidence` in `contribution_digests` uses plain-language values (`strong evidence`, `partial evidence`, `weak evidence`, `no evidence provided`) — the AI reports what it found, not what it concluded.
- `platform_config` is a key-value config table. Validation thresholds, token rewards, AI model choice, and rate limits are all rows — adjustable without touching Python code.
- `quiz_responses` stores raw JSON so question wording can evolve without a schema migration.

---

## Project Structure & File Descriptions

- **`app.py`**: The main Flask application entry point. Handles all routing, session management, CSRF protection, and request/response flow, while delegating all database interactions to `models.py`.
- **`models.py`**: The exclusive location for all SQL database queries. Contains organized functions for user authentication, append-only token ledger management, contribution fetching/validation, and quiz response tracking.
- **`agent.py`**: The background AI digest agent. Triggered upon contribution submission, it analyzes the user's provided source excerpt, assesses its quality and gaps relative to the claim, and generates a plain-language summary for peer validators.
- **`quiz.py`**: Contains the rule-based classification logic for the diagnostic quiz, scoring user responses to route them to their most relevant systemic lens.
- **`seed.py`**: A dual-mode (SQLite/PostgreSQL) initialization script. It populates the database with the foundational structure (lenses, issues, indicators, and pre-approved forces) and a "Data Archive" system user, intentionally omitting external API data fetching to prioritize community-built evidence.
- **`schema.sql` & `schema_postgres.sql`**: The database schema definitions for local development (SQLite) and production (PostgreSQL), respectively. They establish the unified data architecture, cross-lens force links, and append-only token economy.
- **`templates/`**: Contains all Jinja2 HTML templates (e.g., `lens.html`, `contribute.html`, `validate.html`, `heatmap.html`) that render the user interface and dynamically display data passed from the backend.
- **`static/`**: Contains vanilla CSS for styling and JavaScript files (e.g., `heatmap.js` for Leaflet.js map rendering, `charts.js` for data visualization) to handle frontend interactivity without heavy frameworks.

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
6. Additionally, the AI cleans obvious typos and erratic capitalization from the user's submission before it is saved to the database, improving readability without altering the original meaning or context. The digest is then displayed to all peer validators on `validate.html`.

**3. Design principle:** 

The AI presents evidence. Humans decide. User-submitted sources are analyzed for context, methodology, and internal consistency — not judged against privileged institutional databases. Where a source lacks specificity or presents a unique local perspective, the digest surfaces those details explicitly. The friction between different community perspectives is the insight. This is consistent with the platform's thesis that information asymmetry is itself a force worth documenting.

**4. Cost estimate:** 

~$0.002–$0.01 per contribution at current model pricing. Under $1 for the first 100 contributions.

**5. Variability in user-submitted evidence:** 

Community sources may vary in quality, specificity, or methodological grounding. The AI digest is designed to explicitly flag these gaps rather than hide them, maintaining epistemic humility.

---

**Development timeline:** 4 weeks (June 19 - July 16, 2026)
- Week 1: Schema, auth, Flask skeleton
- Week 2: Lenses, quiz, token system
- Week 3: Heatmap, contributions, AI agent, validation
- Week 4: Polish, PostgreSQL migration, deployment

---

## Remaining Known Risks (Accepted):
- **Multiple accounts:** No email collected, making duplicate account detection impossible by design. Token economy limits damage — opening balance requires genuine participation to grow.
- **No account recovery:** Without email, users who lose their password cannot recover their account. Disclosed explicitly at registration.
- **Quiz AI credibility:** The weighted scoring classifier in `quiz.py` is rule-based logic, not machine learning. Accurately described as a classification system, not AI in the neural network sense.
- **Agent data coverage bias:** WHO and World Bank data covers OECD countries more completely. UI surfaces gaps explicitly.
- **Validator read-only limitation:** Validators cannot add evidence of their own. Documented in `how_it_works.html`. `contribution_comments` table scoped for post-submission.
- **Sharing mechanic deliberately dropped:** Unverifiable mechanic inconsistent with platform's integrity principles. `shares` table retained in schema for potential future implementation with proper verification.
- **Render free tier spin-down:** 50-second cold start after inactivity. Mitigated by UptimeRobot ping every 5 minutes.

---

## Legal and Ethical Framework

No email collected (privacy-by-design). Users consent at registration and can request deletion. Full details at /privacy and /terms.

---

## Echo Chamber Prevention

A platform built around systemic critique will attract users who already agree. The following design decisions actively counter confirmation bias — they are architectural choices, not content moderation.

- **Quiz cross-pollination:** After routing to their primary lens, users see a secondary lens with a specific data point.
- **Heatmap "least heard" mode:** Toggle directs attention toward underrepresented countries/issues.
- **Forces layer:** Cross-lens links show the same mechanism (e.g., financial capture) operating across Food, Housing, and Mobility — pulling users out of silos through evidence structure, not algorithms.
- **Community validation:** Force claims require validators to confirm: plain-language mechanism description, 2+ independent sources, and cross-lens links spanning 2+ domains.

---

## Deployment & Future Scope

**Live Deployment**
- **URL:** https://conviction-20z3.onrender.com/
- **Infrastructure:** Render free tier (Web Service + Managed PostgreSQL)
- **Availability:** UptimeRobot configured to ping every 5 minutes, preventing the 50-second cold start inherent to free-tier hosting.

**Deferred Features (Post-Submission)**
The current schema fully supports these features; they require only additional Python and template work:
- **Admin Moderation Interface:** A dashboard for reviewing flagged contributions, adjusting `platform_config` values, and monitoring token economy health.
- **Forces Content Dispute Mechanism:** A formal flagging flow for challenging a force entry's evidence chain, complete with a documented community review process.

**AI Attribution & Academic Honesty**
Every Python and JavaScript file in this project includes a header comment attributing Claude (Anthropic) and Qwen (Qwen3.7-Plus) as development aids. These comments explicitly describe what the AI assisted with in that specific file (e.g., query structure, error handling patterns) and confirm that all core logic, architectural decisions, and project direction are the author's own.

---

## Submission Checklist
- [ ] Step 1: Record 3-minute video (title, name, GitHub username, edX username, city/country, date) → upload to YouTube unlisted
- [ ] Step 2: Finalise README.md (750+ words) → run `submit50 cs50/problems/2026/x/project`
- [x] Step 3 prep: Visit https://conviction-20z3.onrender.com/ to confirm live deployment
- [ ] Step 3: Visit cs50.me/cs50x to trigger certificate generation
- [ ] Deadline: Thursday, December 31, 2026 at 4:59 PM PDT