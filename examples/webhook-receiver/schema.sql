CREATE TABLE IF NOT EXISTS bastion_webhook_inbox (
  delivery_id text PRIMARY KEY,
  payload jsonb NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz,
  attempts integer NOT NULL DEFAULT 0,
  next_attempt_at timestamptz NOT NULL DEFAULT now(),
  last_error text
);
CREATE INDEX IF NOT EXISTS bastion_inbox_pending
  ON bastion_webhook_inbox (next_attempt_at, received_at)
  WHERE processed_at IS NULL;

-- event_id prevents a dashboard test/new delivery from processing
-- the same scored event twice. This is the example's durable business effect.
CREATE TABLE IF NOT EXISTS bastion_decision_audit (
  event_id text PRIMARY KEY,
  site_id text NOT NULL,
  account_id text NOT NULL,
  action text NOT NULL CHECK (action IN ('allow', 'review', 'challenge', 'block')),
  risk_score double precision NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
  evidence jsonb NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT now()
);
