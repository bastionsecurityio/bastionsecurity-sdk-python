# Developer setup guides

These guides and code blocks are generated from the website's developer documentation at platform revision `44c75b5c6715fb9a30b07e2c3ee319e0ac0810b2`. The language-specific runnable entry point is [examples/README.md](../examples/README.md).

- [Build with Bastion.](overview.md) — Developer guides for connecting your application to fraud scoring, bot protection, signed webhooks, and workspace SSO.
- [Your first integration](quickstart.md) — Collect telemetry in the browser, verify on your server, and enforce the result before completing checkout.
- [Authentication & site setup](authentication.md) — Use public keys for browser collection, private keys for server verification, and scoped sessions for workspace management.
- [Browser SDK](browser-sdk.md) — Collect fingerprint, environment, and interaction telemetry in JavaScript applications without exposing a server secret.
- [Server SDKs](server-sdks.md) — Authenticated verification and webhook signatures in Node.js, Python, Go, Ruby, and PHP.
- [Scoring API reference](api-reference.md) — HTTP routes, request fields, decision schemas, response envelopes, and body limits.
- [Decisions & enforcement](decisions.md) — Turn risk evidence into application behavior using the action returned by your site policy.
- [Retries & batch processing](idempotency.md) — Retry safely, avoid duplicate decisions, and handle partial batch failures.
- [Proof-of-work challenges](challenges.md) — Create, solve, and validate site-bound challenges while keeping authorization on your backend.
- [Signed webhooks](webhooks.md) — Receive decision.created events, verify the exact payload, deduplicate retries, and process deliveries durably.
- [SAML single sign-on](sso.md) — Connect your organization’s identity provider to the Bastion tenant workspace using SAML 2.0.
- [Workspace management API](workspace-api.md) — Manage tenant sites, team membership, rules, and integrations with authenticated workspace requests.
- [Custom rules](rules.md) — Express site-specific risk conditions with a bounded comparison grammar and plan-aware rule configuration.
- [Signals & analyst evidence](signals.md) — Understand browser, behavioral, network, velocity, and identity evidence used in scoring and case investigation.
- [Plans, quotas & retention](plans-and-limits.md) — Design integrations around enforced tenant entitlements, monthly decision caps, and retention windows.
- [Errors & troubleshooting](errors.md) — Diagnose key, origin, quota, telemetry, webhook, and SAML failures without accidentally approving an operation.
- [Production integration checklist](production.md) — Roll out enforcement with trusted context, bounded retries, durable event handling, and tenant-aware configuration.

To update after a platform docs change, install the platform checkout's dependencies and run from this SDK repository:

```sh
node scripts/sync-site-docs.cjs /path/to/platform
node scripts/sync-site-docs.cjs /path/to/platform --check
```

The generator also copies the complete PostgreSQL webhook receiver and the exact published server verification function. Review and commit regenerated files with the matching SDK changes.


## Optional browser protection (disabled by default)

An owner can enable individual layers in **Settings → Site protection → Optional browser protection**. Choose browser telemetry receipts, interaction evidence and/or the ChaCha20-Poly1305 exchange, select event types (initial selection: signup), then choose Monitor before Enforce. Installing an SDK does not enable these policies. Global Monitor decision policy keeps enforcement observational.

Use the latest JavaScript browser SDK `buildRequest(context)`. It reads the site's public policy; selected events negotiate a five-minute exchange and return an opaque `browser_receipt`, `context` and `idempotency_key`. Off and unselected events use the existing flow. The encrypted exchange uses ephemeral P-256 ECDH, HKDF-SHA256 and authenticated ChaCha20-Poly1305 over HTTPS. No client signing secret is embedded. Existing standalone fingerprint calls still use their normal HTTPS transport.

Forward the **entire** request to this server SDK's `verify` method; keep `browser_receipt` and the original `idempotency_key`. The receipt binds the site, event type, account ID and request attempt. Your server authenticates the customer and supplies authoritative order/identity facts separately. Go accepts the receipt in `ClassifyRequest.BrowserReceipt`; its JSON name is `browser_receipt`. The other SDKs forward that JSON field unchanged. The included verify CLI accepts both full legacy telemetry and receipt-only handoffs.

Do not complete an action on `challenge`, `review`, `block`, or any SDK/API error. Missing/expired/replayed or incomplete evidence can require verification when Enforce and the site's enforcement policy are enabled. Retries of a recorded request keep its idempotency key; a new attempt requires new evidence. If the browser cannot prepare enforced evidence, offer a retry or your own separately verified recovery flow; never silently fulfill.

For custom controls, call `bastion.recordInteraction()` from the real interaction handler. Keyboard/form/touch observations are also supported. Do not pass field contents or cookie-consent choices; acceptance/rejection is not scored. Evidence alone does not prove a human. [Full setup and protocol](https://bastionsecurity.io/docs/browser-sdk#optional-layers).
