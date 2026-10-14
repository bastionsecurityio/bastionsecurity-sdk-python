# Bastion Python SDK (0.2)

Authenticated **server-side** scoring. The browser must use the JavaScript SDK to collect fingerprint, behavior, and environment telemetry; forward its complete `buildRequest()` payload to your server. Never expose the secret key or raw payment credentials to a browser.

Install the current source release: `pip install git+https://github.com/bastionsecurityio/sdk-python.git`. Registry publication is separate from this Git release.

```python
import os
from bastion import BastionClient, verify_webhook
with BastionClient(os.environ['BASTION_SITE_KEY'], os.environ['BASTION_SECRET_KEY']) as client:
    request = dict(browser_request, context={**browser_request['context'],
        'account_id': authenticated_account_id, 'order_amount': validated_amount})
    decision = client.verify(request)
    if decision['action'] != 'allow':
        raise RuntimeError('Challenge or review required')
```

Methods: `verify(request)`, `classify(token, context, **telemetry)`, `track(event, context, token=None)`, `fingerprint(fingerprint, behavior=None)`, `batch(requests)`, `create_challenge(difficulty=4)`, `verify_challenge(id, nonce)`, `close()`; context-manager support. `verify_webhook(secret, raw_body, signature, tolerance=300)` verifies the exact raw bytes. Errors: `BastionError` with `status` and `response`.

The endpoint defaults to `https://api-production-761a5.up.railway.app/api/antibot`; root URLs and `/api` are normalized. Override it for your deployment. HTTPS is required except on localhost. Server authentication uses `X-Site-Key` and `X-Secret-Key`. A 15-second timeout and two bounded retries apply by default; timeouts/retries are configurable. Redirects never forward your credentials. Network/429/5xx retries preserve the serialized body and idempotency key; validation/auth failures are never retried. Invalid JSON and network errors cannot become an allowed decision.

The full API decision includes `action`, `classification`, `risk_score`, `risk_level`, `signals` (rule, score, evidence description), `identity`, `device_id`, `request_id`, `decision_ms`, `timestamp`, and optional `challenge`. Always enforce `action` **before fulfillment**. A successful single-use proof is site-bound and does not override a block/review decision.

Context requires `event_type` (`signup`, `login`, `promo_claim`, `checkout`, `page_view`) and `account_id`. Optional fields include `email`, `ip_address`, `user_agent`, `payment_hash`, `promo_code`, `order_amount`, `request_url`, and server-verified `login_succeeded`. Preserve the browser's `fingerprint`, `behavior`, `environment`, and optional end-user headers. Overwrite business context with authenticated server values rather than trusting client claims.

Keep `idempotency_key` stable across application-level retries of the **same** request. The API stores scoring receipts for 24 hours and rejects changed payloads under the same key (409). Each batch accepts 1–50 events and returns per-item acknowledgements/errors; inspect every result, and retry failures with their existing keys. Supply explicit keys if you may call `batch` again.

Webhooks are signed HMAC-SHA256 over `timestamp.raw-body` with a five-minute tolerance and constant-time signature comparison. Verify the exact raw bytes before JSON parsing. Persist received event IDs to deduplicate at-least-once deliveries.

0.1 migration: replace `/v1` platform paths and `X-Bastion-*` signatures with the actual `/api/antibot` routes/site credentials and explicit context. Old invented tokens are no longer supported. Dashboard management, billing, SSO, support and teams use the authenticated platform control-plane API, not customer scoring keys. Stripe/Resend/IdP setup is done in the platform.

Unit tests cover signature and error/auth/retry behavior. The `test_e2e` test covers real fingerprint registration, all scoring helpers, durable deduplication, partial batches, invalid keys, and proof verification/replay. Set `BASTION_QA_SESSION` to a fixture from the platform's isolated local test environment; production URLs are rejected.

Make your own fulfillment operation idempotent as well: persist the decision/request ID and never fulfill the same logical checkout twice. API retry receipts deduplicate scoring, not your payment provider or business operations.
