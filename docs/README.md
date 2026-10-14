# Developer setup guides

These guides and code blocks are generated from the website's developer documentation at platform revision `4b7879729687067d55fe230a0503385b205c0018`. The language-specific runnable entry point is [examples/README.md](../examples/README.md).

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
