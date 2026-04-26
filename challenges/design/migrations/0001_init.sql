CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS keys (
    id           uuid        PRIMARY KEY,
    owner_email  text        NOT NULL,
    ciphertext   bytea       NOT NULL,
    nonce        bytea       NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS keys_owner_created_idx
    ON keys (owner_email, created_at DESC);
