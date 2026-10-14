import hashlib
from datetime import datetime
import json
import math
import os
import sys
import time
from pathlib import Path
from bastion import BastionClient, BastionError, verify_webhook


def required(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(name + ' is required')
    return value


def load(file):
    return json.loads(Path(file).read_text())


def base36(number):
    alphabet, result = '0123456789abcdefghijklmnopqrstuvwxyz', ''
    while number:
        number, digit = divmod(number, 36)
        result = alphabet[digit] + result
    return result or '0'


def main():
    args = sys.argv[1:]
    mode = args[0] if args else ''
    if mode == 'webhook':
        if len(args) != 3:
            raise ValueError('Usage: webhook raw-body.json signature.txt')
        raw = Path(args[1]).read_bytes()
        signature = Path(args[2]).read_text().strip()
        if not verify_webhook(required('BASTION_WEBHOOK_SECRET'), raw, signature):
            raise ValueError('Invalid or stale webhook signature')
        return {'verified': True, 'event': json.loads(raw)}, 0
    if mode not in ('verify', 'batch', 'challenge'):
        raise ValueError('Usage: verify telemetry.json order.json | batch requests.json | challenge | webhook raw-body.json signature.txt')
    with BastionClient(required('BASTION_SITE_KEY'), required('BASTION_SECRET_KEY'), endpoint=os.environ.get('BASTION_ENDPOINT', 'https://api.bastionsecurity.io/api/antibot')) as client:
        if mode == 'verify':
            if len(args) != 3:
                raise ValueError('Usage: verify telemetry.json order.json')
            telemetry, order = load(args[1]), load(args[2])
            if not all(telemetry.get(k) for k in ('token', 'fingerprint', 'idempotency_key')):
                raise ValueError('Complete buildRequest() telemetry with a stable idempotency_key is required')
            amount = order.get('amount')
            if not isinstance(order.get('customerId'), str) or not order['customerId'] or not isinstance(order.get('paymentId'), str) or not order['paymentId'] or isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
                raise ValueError('Trusted order needs customerId, paymentId, and a finite nonnegative amount')
            request = {k: telemetry[k] for k in ('token', 'fingerprint', 'behavior', 'environment', 'idempotency_key') if k in telemetry}
            request['context'] = {'event_type': 'checkout', 'account_id': order['customerId'], 'order_amount': amount, 'payment_hash': order['paymentId']}
            decision = client.verify(request)
            return {'allowed': decision['action'] == 'allow', 'decision': decision}, 0
        if mode == 'batch':
            if len(args) != 2:
                raise ValueError('Usage: batch requests.json')
            requests = load(args[1])
            if not isinstance(requests, list) or not 1 <= len(requests) <= 50 or any(not r.get('idempotency_key') for r in requests):
                raise ValueError('Batch needs 1–50 server-owned requests, each with a stable idempotency_key')
            result = client.batch(requests)
            for item in result['results']:
                item['allowed'] = item.get('success') is True and item.get('decision', {}).get('action') == 'allow'
            return result, 2 if any(not item['success'] for item in result['results']) else 0
        challenge = client.create_challenge(4)
        expires = datetime.fromisoformat(challenge['expires_at'].replace('Z', '+00:00')).timestamp()
        deadline, nonce = time.monotonic() + min(60, expires - time.time()), 0
        while not hashlib.sha256((challenge['prefix'] + base36(nonce)).encode()).hexdigest().startswith('0' * challenge['difficulty']):
            if time.monotonic() >= deadline:
                raise ValueError('Proof solver deadline reached')
            nonce += 1
        result = client.verify_challenge(challenge['challenge_id'], base36(nonce))
        if not result['valid']:
            raise ValueError('Proof was rejected')
        return dict(result, fulfillment_authorized=False), 0


if __name__ == '__main__':
    try:
        output, status = main()
        print(json.dumps(output, indent=2))
        sys.exit(status)
    except (BastionError, ValueError, OSError, KeyError, TypeError) as error:
        print('Example failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
