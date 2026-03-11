CREATE TABLE domains (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id          UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    domain_name         VARCHAR(255) NOT NULL,
    verification_token  VARCHAR(255) NOT NULL,
    is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(contact_id, domain_name)
);

CREATE TABLE domain_checks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id       UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    spf_record      TEXT,
    dkim_record     TEXT,
    dmarc_record    TEXT,
    spf_status      VARCHAR(20),
    dkim_status     VARCHAR(20),
    dmarc_status    VARCHAR(20),
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_domains_contact_id ON domains(contact_id);
CREATE INDEX idx_domain_checks_domain_id ON domain_checks(domain_id);
