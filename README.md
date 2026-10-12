# Bastion Security Python SDK

Official Python SDK for [Bastion Security](https://bastionsecurity.io) — real-time bot detection and fraud prevention.

## Installation

```bash
pip install bastionsecurity
```

## Usage

```python
from bastion import BastionClient

client = BastionClient(
    site_key="pk_live_your_site_key",
    secret="sk_live_your_secret_key",
)

# Classify a token from the frontend SDK
result = client.classify("token-from-frontend")
print(result["verdict"], result["score"])

# Track a server-side event
client.track("purchase", {"amount": 49.99, "user_id": "usr_123"})
```

### As a context manager

```python
with BastionClient(site_key="...", secret="...") as client:
    result = client.classify(token)
```

## API

### `BastionClient(site_key, secret, endpoint=None, timeout=10.0)`

| Param | Type | Required | Description |
|---|---|---|---|
| site_key | str | Yes | Your site's public key |
| secret | str | Yes | Your site's secret key |
| endpoint | str | No | API endpoint |
| timeout | float | No | Request timeout in seconds |

### `client.classify(token: str) -> dict`

Classify a token from the frontend SDK. Returns verdict, score, signals.

### `client.track(event: str, data: dict = None) -> None`

Track a server-side event.

## License

MIT — © 2024 Bastion Security
