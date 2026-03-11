CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE contact_status AS ENUM ('active', 'inactive', 'suspended', 'pending_verification');

CREATE TABLE contacts (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email             VARCHAR(255) NOT NULL UNIQUE,
    password_hash     TEXT,
    name              VARCHAR(255),
    email_verified    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at     TIMESTAMPTZ,
    status            contact_status NOT NULL DEFAULT 'pending_verification'
);

CREATE TABLE google_accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id      UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    google_sub      VARCHAR(255) NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);
