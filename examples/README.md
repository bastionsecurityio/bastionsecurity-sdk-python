# Runnable Python examples

These programs call the real SDK and API. Run commands from the repository root after installing dependencies as shown in [the README](../README.md). No application credentials or browser tokens are supplied by the repository.

## Configure a site and your environment

1. Follow [site setup](../docs/quickstart.md) and [authentication](../docs/authentication.md). Copy the public site key and server secret from Integration. Allowlist the exact frontend origin, including scheme and port.
2. Set `BASTION_SITE_KEY`, `BASTION_SECRET_KEY`, and optionally `BASTION_ENDPOINT` in your **server** environment. The endpoint defaults to `https://api-production-761a5.up.railway.app/api/antibot`. [`.env.example`](.env.example) lists the variables; the native CLI does not automatically load dotenv files.
3. Initialize the [browser SDK](../docs/browser-sdk.md) once before the customer interacts. Save the complete JSON returned by `buildRequest()` as `examples/browser-request.json` for this operator-driven CLI walkthrough. Tokens expire after ten minutes; collect a fresh request when needed. In your application, send the payload directly to your authenticated backend rather than writing customer files.
4. Copy `examples/order.example.json` to `examples/order.json`. Replace it with trusted session/database/payment-provider values. This local operator-owned file supplies checkout context; never populate it from client claims or raw card credentials.

```sh
export BASTION_SITE_KEY='YOUR_PUBLIC_SITE_KEY'
export BASTION_SECRET_KEY='YOUR_SERVER_SECRET'
export BASTION_ENDPOINT='https://api-production-761a5.up.railway.app/api/antibot'
python examples/cli.py verify examples/browser-request.json examples/order.json
```

The JSON output contains `allowed` and the complete `decision`, including `action`, signals, and `request_id`. Only `allowed: true` may enter your application's approval path. This program records a real scoring event but does not fulfill an order. Persist its request ID and implement independent payment/fulfillment idempotency. Reuse the same input and idempotency key for retries of the same event; changed payloads under the same key return 409. Missing keys or API failures exit nonzero. A successful API call with a block/review/challenge still prints `allowed: false`.

The [published verification helper](published/) is copied byte-for-byte from the website's Python tab. Adapt it inside your authenticated handler, preserving token, fingerprint, behavior, environment, and idempotency key, and overwriting business context as this CLI does. Add trustworthy IP/user-agent/login outcomes only on the backend.

## Batch acknowledgements

Prepare `examples/batch.json` as an array of 1–50 complete server-owned VerificationRequests. Each must have its own stable `idempotency_key`, full browser telemetry, and validated context. Do not reuse a checkout key for a different event or context. See [request fields](../docs/api-reference.md) and [batch receipts](../docs/idempotency.md).

```sh
python examples/cli.py batch examples/batch.json
```

The CLI reports an `allowed` boolean for each item and exits 2 if any item fails. An HTTP 2xx batch can contain errors. Retry failed items with their original keys; never infer approval from `accepted` alone.

## A real proof challenge

```sh
python examples/cli.py challenge
```

This requests a difficulty-4 challenge, solves SHA-256 using a base-36 nonce, and submits the proof to the API. It stops after 60 seconds or the challenge's expiry. A valid proof is single-use and site-bound; the output's `fulfillment_authorized` stays false. Proof success does not override a block/review or approve a checkout. Apply your application's challenge policy separately.

## Verify a signed delivery with this SDK

Set `BASTION_WEBHOOK_SECRET` to the signing secret from Workspace → Webhooks, not the scoring server secret. Save the **exact raw bytes** of an incoming delivery as `examples/delivery.json` and its `Bastion-Signature` header as `examples/signature.txt`. Do not pretty-print or reserialize the body.

```sh
export BASTION_WEBHOOK_SECRET='YOUR_WEBHOOK_SIGNING_SECRET'
python examples/cli.py webhook examples/delivery.json examples/signature.txt
```

The native CLI verifies HMAC and the five-minute timestamp tolerance before JSON parsing. Invalid/stale signatures exit nonzero. This offline inspection command does not acknowledge, deduplicate, or process a delivery. For a complete HTTP receiver, durable queue, duplicate handling, and atomic worker, use [webhook-receiver/README.md](webhook-receiver/README.md). That shared Node.js 20+/PostgreSQL example is identical to the working receiver in the website docs and uses the JavaScript SDK; no framework dependency is added to this Python SDK.

## Webhooks and SAML setup

Follow [the webhook guide](../docs/webhooks.md) to deploy public HTTPS on port 443, configure the owner-only API or dashboard, enable deliveries, record an event, send a test, and inspect processing. Localhost/private webhook destinations cannot be saved. Webhooks require Pro or Enterprise; demo is exempt.

Follow [the SAML guide](../docs/sso.md) for the exact owner configuration API, IdP certificate, SP metadata/ACS URLs, signed assertions, existing member provisioning, browser sign-in, and one-use exchange. SSO requires Enterprise and authenticates your Bastion workspace team. It does not sign customers into your application and is not a scoring-SDK method. Use the URLs returned by configuration instead of inventing hostnames.

## Keep examples aligned

```sh
node scripts/sync-site-docs.cjs /path/to/platform --check
```

This checks all generated guides, this SDK's published verification helper, and every source/lockfile in the shared receiver against the platform checkout. See [production checks](../docs/production.md) for rollout, fail-closed handling, quotas, retention, and secret rotation. Local credentials, downloaded telemetry, and customer files are ignored by Git.

## Repeat the native end-to-end checks

An optional Node.js 20+ harness invokes the native CLI against an isolated real local API and scoring engine. It rejects production hosts. Supply a private JSON fixture with `endpoint`, `site_key`, and `secret`, and run:

```sh
BASTION_QA_SESSION=/path/to/private-local-fixture.json node scripts/check-examples.cjs
```

The checks exercise trusted-context replacement, repeated receipt IDs, 409 on changed context, invalid/missing credentials, partial batches, proof validation, and valid/tampered/stale webhook signatures. Synthetic events are recorded in the supplied local tenant; temporary input files are removed.
