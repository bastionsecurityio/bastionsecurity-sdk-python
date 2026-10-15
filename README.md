# Bastion Python SDK

Authenticated server scoring, proof challenges, and webhook verification. Collect browser telemetry with the JavaScript SDK and forward its complete request to your backend.

Requires Python 3.9+. Install the current Git source release in your application:

```sh
pip install git+https://github.com/bastionsecurityio/bastionsecurity-sdk-python.git
```

Registry publication is separate from this Git release. Pin a reviewed revision and commit your dependency lockfile for production.

To run the examples, clone this repository and follow [examples/README.md](examples/README.md):

```sh
git clone https://github.com/bastionsecurityio/bastionsecurity-sdk-python.git
cd bastionsecurity-sdk-python
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

- [Setup and browser-to-server integration](docs/quickstart.md)
- [Server methods and language examples](docs/server-sdks.md)
- [Authentication and origin allowlists](docs/authentication.md)
- [Actions and enforcement](docs/decisions.md)
- [Batches and idempotency](docs/idempotency.md)
- [Single-use proof challenges](docs/challenges.md)
- [Signed webhooks and durable processing](docs/webhooks.md)
- [Enterprise SAML setup](docs/sso.md)
- [All developer guides](docs/README.md) · [live docs](https://bastionsecurity.io/docs)

The guides and the published verification function are generated from the same source as the website. The repository includes executable native Python examples and the website's complete Node.js/PostgreSQL webhook receiver and worker. The shared receiver needs Node.js 20+; native signature verification uses this SDK.

Keep `BASTION_SECRET_KEY` on your server. Replace customer, price, and payment context with authenticated server values. Only an `allow` action permits the approval path; API errors and all other actions stop it. New sites start in monitor mode, where even high-risk traffic is allowed until you configure enforcement. Scoring receipts do not make payment or fulfillment operations idempotent.

Webhooks use their own signing secret and the exact raw request bytes. Deliveries can repeat; deduplicate delivery IDs and scored-event IDs, and acknowledge only after durable acceptance. Retries are bounded to five attempts; a failed delivery is not guaranteed to arrive. SAML authenticates existing workspace members, requires Enterprise, and uses the Bearer-authenticated control plane rather than scoring keys.

SDK contract tests and isolated local end-to-end tests remain available in this repository. See the test files for `BASTION_QA_SESSION`; end-to-end fixtures intentionally reject production hosts. The runnable examples can use your configured site and consume real decisions; they never perform payment or fulfillment.


## Optional browser protection (disabled by default)

An owner can enable individual layers in **Settings → Site protection → Optional browser protection**. Choose browser telemetry receipts, interaction evidence and/or the ChaCha20-Poly1305 exchange, select event types (initial selection: signup), then choose Monitor before Enforce. Installing an SDK does not enable these policies. Global Monitor decision policy keeps enforcement observational.

Use the latest JavaScript browser SDK `buildRequest(context)`. It reads the site's public policy; selected events negotiate a five-minute exchange and return an opaque `browser_receipt`, `context` and `idempotency_key`. Off and unselected events use the existing flow. The encrypted exchange uses ephemeral P-256 ECDH, HKDF-SHA256 and authenticated ChaCha20-Poly1305 over HTTPS. No client signing secret is embedded. Existing standalone fingerprint calls still use their normal HTTPS transport.

Forward the **entire** request to this server SDK's `verify` method; keep `browser_receipt` and the original `idempotency_key`. The receipt binds the site, event type, account ID and request attempt. Your server authenticates the customer and supplies authoritative order/identity facts separately. Go accepts the receipt in `ClassifyRequest.BrowserReceipt`; its JSON name is `browser_receipt`. The other SDKs forward that JSON field unchanged. The included verify CLI accepts both full legacy telemetry and receipt-only handoffs.

Do not complete an action on `challenge`, `review`, `block`, or any SDK/API error. Missing/expired/replayed or incomplete evidence can require verification when Enforce and the site's enforcement policy are enabled. Retries of a recorded request keep its idempotency key; a new attempt requires new evidence. If the browser cannot prepare enforced evidence, offer a retry or your own separately verified recovery flow; never silently fulfill.

For custom controls, call `bastion.recordInteraction()` from the real interaction handler. Keyboard/form/touch observations are also supported. Do not pass field contents or cookie-consent choices; acceptance/rejection is not scored. Evidence alone does not prove a human. [Full setup and protocol](https://bastionsecurity.io/docs/browser-sdk#optional-layers).
