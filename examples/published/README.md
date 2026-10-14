# Published verification function

The adjacent source file is copied exactly from this SDK's tab in [the website server guide](../../docs/server-sdks.md). It is an application integration function; it does not run a web server or supply customer credentials.

Call it from your authenticated server handler after replacing business context with verified session, database, and payment-provider values. Preserve the complete browser telemetry, use a stable idempotency key, and enforce the returned action before your independently idempotent approval or fulfillment operation. Errors must stop approval.

For an executable walkthrough with explicit input files, environment validation, all decision actions, batches, proof challenges, and raw webhook verification, use [the native CLI](../README.md). PHP's snippet assumes your application-root `vendor/autoload.php`; Go's function can be imported as an integration package; Python and Ruby functions can be imported or required. Node's TypeScript function requires TypeScript and `@types/node` in the consuming application.
