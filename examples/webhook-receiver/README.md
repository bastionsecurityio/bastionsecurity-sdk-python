# Bastion webhook receiver

A runnable Node.js 20+ receiver and PostgreSQL worker. It verifies SDK signatures
against raw bytes, acknowledges only after durable acceptance, and atomically
records each scored event in `bastion_decision_audit`. Duplicate deliveries and
new test deliveries for the same event do not repeat the audit effect.

```sh
npm install
cp .env.example .env
# Set DATABASE_URL and BASTION_WEBHOOK_SECRET in .env.
npm run migrate
npm start
# In another terminal:
npm run worker
```

Expose only `/webhooks/bastion` through your public HTTPS reverse proxy on port
443. Set HOST=0.0.0.0 when a container needs to accept proxy traffic. Configure
that final URL in the tenant's Webhooks page. Localhost destinations cannot be
saved in Bastion; a public HTTPS development tunnel can be used for testing.

The signing secret is the secret from Webhooks, not the scoring server key.
Treat it as a UTF-8 string. Run a scored event before sending a dashboard test.
Inspect `bastion_webhook_inbox` for durable receipt and `bastion_decision_audit`
for completed processing. `processed_at IS NULL` identifies pending work;
`last_error` identifies failures retried by the worker.

This example's business effect is a decision audit. It does not charge a card
or fulfill an order. Financial and fulfillment effects need your application's
own authorization and idempotency policy. If adding them, perform database side
effects in the same transaction, or use a transactional outbox with an
independently idempotent external operation.

Commit the generated package-lock.json to pin the installed SDK revision when
you adopt the example. Never commit .env or use real customer data for QA.
