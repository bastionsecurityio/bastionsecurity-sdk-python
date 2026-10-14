#!/usr/bin/env node
// Optional Node.js 20+ harness: invokes each repository's native runnable CLI
// against an isolated real API. It refuses production endpoints.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const {spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const {command} = JSON.parse(fs.readFileSync(path.join(__dirname, 'example-language.json')));
const fixturePath = process.env.BASTION_QA_SESSION;
if (!fixturePath) throw new Error('Set BASTION_QA_SESSION to an isolated local fixture with endpoint, site_key, and secret.');
const fixture = JSON.parse(fs.readFileSync(fixturePath));
const url = new URL(fixture.endpoint);
if (url.protocol !== 'http:' || !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) throw new Error('Local QA only');
const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'bastion-sdk-examples-'));
const env = {...process.env, BASTION_ENDPOINT: fixture.endpoint, BASTION_SITE_KEY: fixture.site_key, BASTION_SECRET_KEY: fixture.secret, BASTION_WEBHOOK_SECRET: crypto.randomBytes(32).toString('hex')};
const executable = command[0] === 'node' ? process.execPath : command[0] === 'python' && fs.existsSync(path.join(root, '.venv/bin/python')) ? path.join(root, '.venv/bin/python') : command[0];
function file(name, content) {
  const filename = path.join(directory, name);
  fs.writeFileSync(filename, typeof content === 'string' ? content : JSON.stringify(content), {mode: 0o600});
  return filename;
}
function run(args, expected = 0, overrides = {}) {
  const result = spawnSync(executable, [...command.slice(1), ...args], {cwd: root, env: {...env, ...overrides}, encoding: 'utf8', timeout: 120000});
  assert.equal(result.status, expected, `${args[0]} exited ${result.status}: ${result.error?.message || result.stderr}`);
  return expected === 1 ? result : JSON.parse(result.stdout);
}
async function main() {
  const fingerprint = {canvas_hash: crypto.randomUUID(), platform: 'MacIntel', user_agent: 'Mozilla/5.0 Chrome/130.0', language: 'en-US', languages: ['en-US'], screen_resolution: '1440x900'};
  const response = await fetch(fixture.endpoint + '/verify/fingerprint', {method: 'POST', headers: {'Content-Type':'application/json', 'X-Site-Key': fixture.site_key, 'X-Secret-Key': fixture.secret}, body: JSON.stringify({fingerprint})});
  assert.ok(response.ok, `Fingerprint registration failed: ${response.status}`);
  const registered = (await response.json()).data;
  const telemetry = {token: registered.token, fingerprint, behavior: {}, environment: {nonce:crypto.randomUUID(), request_timestamp: Date.now()}, idempotency_key:crypto.randomUUID(), context:{event_type:'signup',account_id:'untrusted-client',order_amount:0}};
  const telemetryFile = file('telemetry.json', telemetry);
  const order = {customerId:'sdk-examples-' + crypto.randomUUID(), amount:49.99, paymentId:'pm_synthetic_' + crypto.randomUUID()};
  const orderFile = file('order.json', order);
  const decision = run(['verify', telemetryFile, orderFile]);
  assert.ok(decision.decision.request_id);
  assert.equal(decision.allowed, decision.decision.action === 'allow');
  assert.ok(Array.isArray(decision.decision.signals));
  const retry = run(['verify', telemetryFile, orderFile]);
  assert.equal(retry.decision.request_id, decision.decision.request_id);
  // Client-supplied identity/price must not affect trusted checkout context.
  const poisoned = file('poisoned.json', {...telemetry, context:{event_type:'checkout',account_id:'attacker',order_amount:999999,payment_hash:'attacker-card'}});
  assert.equal(run(['verify', poisoned, orderFile]).decision.request_id, decision.decision.request_id);
  const changedOrder = file('changed-order.json', {...order,amount:1});
  run(['verify', telemetryFile, changedOrder], 1);
  run(['verify', telemetryFile, orderFile], 1, {BASTION_SECRET_KEY:'wrong-key'});
  run(['verify', telemetryFile, orderFile], 1, {BASTION_SECRET_KEY:''});
  const batch = file('batch.json', [
    {...telemetry,environment:undefined,idempotency_key:crypto.randomUUID(),context:{event_type:'checkout',account_id:order.customerId,order_amount:order.amount,payment_hash:order.paymentId}},
    {idempotency_key:crypto.randomUUID(),context:{event_type:'unsupported',account_id:'invalid'}}
  ]);
  const result = run(['batch',batch],2);
  assert.equal(result.accepted,1);
  assert.equal(result.results[1].success,false);
  assert.equal(result.results[1].allowed,false);
  assert.equal(result.results[0].allowed,result.results[0].decision.action === 'allow');
  const proof = run(['challenge']);
  assert.equal(proof.valid,true);
  assert.equal(proof.fulfillment_authorized,false);
  const raw = '{"id":"synthetic-delivery","type":"decision.created","label":"café ☃"}';
  const body = file('delivery.json',raw);
  const sign = timestamp => `t=${timestamp},v1=${crypto.createHmac('sha256',env.BASTION_WEBHOOK_SECRET).update(`${timestamp}.${raw}`).digest('hex')}`;
  const signature = file('signature.txt',sign(Math.floor(Date.now()/1000)));
  assert.equal(run(['webhook',body,signature]).verified,true);
  run(['webhook',file('tampered.json',raw + ' '),signature],1);
  run(['webhook',body,file('stale.txt',sign(Math.floor(Date.now()/1000)-301))],1);
  run(['webhook',body,signature],1,{BASTION_WEBHOOK_SECRET:'wrong-signing-secret'});
  console.log('PASS: native examples with real scoring, trusted context, stable receipts, changed-payload rejection, auth failures, partial batches, valid proof, and exact-byte/tamper/stale webhook checks.');
}
main().catch(error => { console.error(error.message); process.exitCode=1; }).finally(() => fs.rmSync(directory,{recursive:true,force:true}));
