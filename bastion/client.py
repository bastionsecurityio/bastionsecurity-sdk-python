"""Server-side integration. Keep the secret key out of browser code."""
import hashlib
import hmac
import json
import re
import time
import uuid
from urllib.parse import urlparse
from typing import Any, Dict, Optional, Union

import httpx

DEFAULT_ENDPOINT = "https://api.bastionsecurity.io/api/antibot"


class BastionError(RuntimeError):
    def __init__(self, message: str, status: int = 0, response: Any = None):
        super().__init__(message)
        self.status = status
        self.response = response


def verify_webhook(secret: str, raw_body: Union[str, bytes], signature: str,
                   tolerance: int = 300, now: Optional[int] = None) -> bool:
    """Verify raw bytes before parsing JSON; reject expired or modified payloads."""
    parts = [part.strip() for part in signature.split(",")]
    timestamps = [part[2:] for part in parts if re.fullmatch(r"t=\d+", part)]
    if not secret or not timestamps or tolerance < 0:
        return False
    timestamp = timestamps[0]
    if abs((int(time.time()) if now is None else now) - int(timestamp)) > tolerance:
        return False
    payload = raw_body.encode("utf-8") if isinstance(raw_body, str) else raw_body
    expected = hmac.new(secret.encode(), timestamp.encode() + b"." + payload, hashlib.sha256).hexdigest()
    return any(re.fullmatch(r"v1=[0-9a-f]{64}", p) and hmac.compare_digest(p[3:], expected) for p in parts)


class BastionClient:
    def __init__(self, site_key: str, secret: str, endpoint: str = DEFAULT_ENDPOINT,
                 timeout: float = 15, retries: int = 2):
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "::1")):
            raise ValueError("Bastion requires HTTPS except on localhost")
        if not site_key or not secret or any("\n" in s or "\r" in s for s in (site_key, secret)):
            raise ValueError("Valid site credentials are required")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Invalid API endpoint")
        endpoint = endpoint.rstrip("/")
        if parsed.path.rstrip("/") == "":
            endpoint += "/api/antibot"
        elif parsed.path.rstrip("/") == "/api":
            endpoint += "/antibot"
        self.endpoint = endpoint
        self.retries = min(3, max(0, retries))
        self.http = httpx.Client(timeout=min(30, max(1, timeout)), follow_redirects=False,
            headers={"Content-Type": "application/json", "X-Site-Key": site_key, "X-Secret-Key": secret})

    def verify(self, request: Dict[str, Any]) -> Dict[str, Any]:
        body = dict(request)
        body.setdefault("idempotency_key", str(uuid.uuid4()))
        return self._post("/verify", body)

    def classify(self, token: str, context: Dict[str, Any], **telemetry: Any) -> Dict[str, Any]:
        return self.verify(dict(telemetry, token=token, context=context))

    def track(self, event: str, data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        return self.verify({"token": token, "context": dict(data, event_type=event)})

    def fingerprint(self, fingerprint: Dict[str, Any], behavior: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._post("/verify/fingerprint", {"fingerprint": fingerprint, "behavior": behavior})

    def batch(self, events: list) -> Dict[str, Any]:
        return self._post("/verify/batch", {"events": [dict(e, idempotency_key=e.get("idempotency_key") or str(uuid.uuid4())) for e in events]})

    def create_challenge(self, difficulty: int = 4) -> Dict[str, Any]:
        return self._post("/verify/challenge", {"difficulty": difficulty})

    def verify_challenge(self, challenge_id: str, nonce: str) -> Dict[str, Any]:
        return self._post("/verify/challenge/verify", {"challenge_id": challenge_id, "nonce": nonce})

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        # Serialise once so each retry represents exactly the same logical event.
        payload = json.dumps(body, separators=(",", ":"), allow_nan=False)
        safe = bool(body.get("idempotency_key")) or bool(body.get("events") and all(e.get("idempotency_key") for e in body["events"]))
        for attempt in range((self.retries if safe else 0) + 1):
            try:
                response = self.http.post(self.endpoint + path, content=payload)
                try:
                    data = response.json()
                except ValueError as error:
                    raise BastionError("API returned invalid JSON", response.status_code) from error
                if not 200 <= response.status_code < 300:
                    raise BastionError(str(data.get("message", "API request failed")) if isinstance(data, dict) else "API request failed", response.status_code, data)
                if not isinstance(data, dict) or data.get("success") is False:
                    raise BastionError("Invalid API response", response.status_code, data)
                return data.get("data", data)
            except httpx.RequestError as error:
                failure = BastionError("API request could not reach the server")
                failure.__cause__ = error
            except BastionError as error:
                failure = error
            if not safe or attempt >= self.retries or (failure.status and failure.status != 429 and failure.status < 500):
                raise failure
            time.sleep(0.25 * 2 ** attempt)
        raise BastionError("API request failed")

    def close(self) -> None:
        self.http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
