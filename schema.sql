-- schema.sql
-- Conviction: database schema
-- Run once to initialise the database: flask --app app init-db
-- AI assistance: Claude (Anthropic) assisted with schema design review.
-- Logic, structure, and decisions are the author's own.

-- Required only for SQLite, enforces the foreign key rules defined in the schema
PRAGMA foreign_keys = ON; 

-- ============================================================
-- CONTENT STRUCTURE
-- ============================================================

CREATE TABLE IF NOT EXISTS lenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lens_id INTEGER NOT NULL REFERENCES lenses(id),
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    mechanism TEXT NOT NULL,
    evidence_chain JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS force_issue_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    force_id INTEGER NOT NULL REFERENCES forces(id),
    issue_id INTEGER NOT NULL REFERENCES issues(id),
    explanation TEXT,
    -- A force_id can link to many issue_ids, and vice versa. UNIQUE makes sure the pair/link of two ids to exist only once
    UNIQUE(force_id, issue_id)
);

-- ============================================================
-- USERS
-- No email collected — privacy by design.
-- Bot prevention via hCaptcha at registration.
-- Account recovery is not possible. Disclosed at registration.
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    token_balance INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SOURCES REGISTRY
-- Reference points for AI agent and validators.
-- Not arbiters of truth — documented with known limitations.
-- ============================================================

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    methodology_url TEXT,
    limitations TEXT,
    institutional_context TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TOKEN ECONOMY
-- token_transactions is an append-only ledger.
-- token_balance on users is a cache — always recalculable from ledger.
-- ============================================================

CREATE TABLE IF NOT EXISTS token_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,
    reason TEXT NOT NULL,
    issue_id INTEGER REFERENCES issues(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- CONTRIBUTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    source_url TEXT,
    source_excerpt TEXT,
    contributor_user_id INTEGER NOT NULL REFERENCES users(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contribution_lens_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    issue_id INTEGER NOT NULL REFERENCES issues(id),
    UNIQUE(contribution_id, issue_id)
);

-- ============================================================
-- DIAGNOSTIC QUIZ
-- ============================================================

CREATE TABLE IF NOT EXISTS quiz_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    session_id TEXT,
    responses JSON NOT NULL,
    recommended_lens_id INTEGER REFERENCES lenses(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- AI DIGEST (generated once per contribution)
-- ============================================================

CREATE TABLE IF NOT EXISTS contribution_digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
    summary TEXT NOT NULL,
    sources JSON,
    confidence TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PEER VALIDATION
-- ============================================================

CREATE TABLE IF NOT EXISTS contribution_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INSERT only: if key exists, error (whole syntax fails) / if key doesn't exist, inserts 
-- INSERT OR IGNORE: if key exists, skips silently (moves to next row) / if key doesn't exist, inserts
INSERT OR IGNORE INTO platform_config (key, value, description) VALUES
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
    ('max_shares_per_day', '3', 'Max token-earning shares per user per day'),
    ('quiz_retake_days', '90', 'Minimum days between quiz retakes per user');

-- ============================================================
-- SHARES
-- ============================================================

CREATE TABLE IF NOT EXISTS shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    content_type TEXT NOT NULL,
    content_id INTEGER,
    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
