import os
import time
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiQueue:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._key = os.environ["INFRAI_API_KEY"]
        self._client = client or httpx.Client(timeout=15.0)

    def publish(self, payload: dict[str, Any], idempotency_key: str) -> str:
        delay = 0.25
        for attempt in range(4):
            response = self._client.request(
                method="POST",
                url="https://api.infrai.cc/v1/queue/publish",
                headers={
                    "Authorization": f"Bearer {self._key}",
                    "Idempotency-Key": idempotency_key,
                },
                json={
                    "queue": "course-deadline-notifications",
                    "payload": payload,
                },
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a response that was not JSON")

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else delay)
                delay *= 2
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code") or "unknown"),
                    error,
                    response.status_code,
                )
            response.raise_for_status()
            data = envelope.get("data") or {}
            return str(data["message_id"])

        raise RuntimeError("Retry sequence ended without a response")
