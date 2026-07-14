-- schema_postgres.sql
-- PostgreSQL version of the schema.sql
-- Conviction: database schema
-- Run once to initialise the database: flask --app app init-db
-- AI assistance: Both Claude (Anthropic) and Qwen.ai (3.7-Plus) assisted with query structure and error handling patterns.
-- Logic, structure, and decisions are the author's own.

-- ============================================================
-- CONTENT STRUCTURE
-- ============================================================

CREATE TABLE IF NOT EXISTS lenses (
    id SERIAL PRIMARY KEY,
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

-- ============================================================
-- FORCES LAYER
-- ============================================================

CREATE TABLE IF NOT EXISTS forces (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    mechanism TEXT NOT NULL,
    evidence_chain JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS force_issue_links (
    id SERIAL PRIMARY KEY,
    force_id INTEGER NOT NULL REFERENCES forces(id),
    issue_id INTEGER NOT NULL REFERENCES issues(id),
    explanation TEXT,
    UNIQUE(force_id, issue_id)
);

-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    token_balance INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SOURCES REGISTRY
-- ============================================================

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    methodology_url TEXT,
    limitations TEXT,
    institutional_context TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TOKEN ECONOMY
-- ============================================================

CREATE TABLE IF NOT EXISTS token_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,
    reason TEXT NOT NULL,
    issue_id INTEGER REFERENCES issues(id),
    force_id INTEGER REFERENCES forces(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- CONTRIBUTIONS
-- ============================================================

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
    contribution_type TEXT DEFAULT 'data_point',
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

-- ============================================================
-- DIAGNOSTIC QUIZ
-- ============================================================

CREATE TABLE IF NOT EXISTS quiz_responses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id TEXT,
    responses JSON NOT NULL,
    recommended_lens_id INTEGER REFERENCES lenses(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- AI DIGEST 
-- ============================================================

CREATE TABLE IF NOT EXISTS contribution_digests (
    id SERIAL PRIMARY KEY,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    summary TEXT NOT NULL,
    sources JSON,
    confidence TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extracted_json TEXT
);

-- ============================================================
-- PEER VALIDATION
-- ============================================================

CREATE TABLE IF NOT EXISTS contribution_votes (
    id SERIAL PRIMARY KEY,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    vote TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(contribution_id, user_id)
);

-- ============================================================
-- PLATFORM CONFIGURATION
-- ============================================================

CREATE TABLE IF NOT EXISTS platform_config (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PostgreSQL uses ON CONFLICT DO NOTHING instead of INSERT OR IGNORE
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