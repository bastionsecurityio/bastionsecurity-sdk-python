import hashlib
import hmac
import json
import time
from typing import Any

import httpx

DEFAULT_ENDPOINT = "https://api.bastionsecurity.io"


class BastionClient:
    def __init__(
        self,
        site_key: str,
        secret: str,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float = 10.0,
    ):
        self.site_key = site_key
        self.secret = secret
        self.endpoint = endpoint.rstrip("/")
        self._http = httpx.Client(timeout=timeout)

    def classify(self, token: str) -> dict[str, Any]:
        body = json.dumps({"token": token}).encode()
        resp = self._http.post(
            f"{self.endpoint}/v1/classify",
            content=body,
            headers=self._headers(body),
        )
        resp.raise_for_status()
        return resp.json()

    def track(self, event: str, data: dict[str, Any] | None = None) -> None:
        payload = {
            "event": event,
            "data": data or {},
            "site_key": self.site_key,
            "ts": int(time.time() * 1000),
        }
        body = json.dumps(payload).encode()
        resp = self._http.post(
            f"{self.endpoint}/v1/events",
            content=body,
            headers=self._headers(body),
        )
        resp.raise_for_status()

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _headers(self, body: bytes) -> dict[str, str]:
        sig = hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest()
        return {
            "Content-Type": "application/json",
            "X-Bastion-Site-Key": self.site_key,
            "X-Bastion-Signature": sig,
        }
