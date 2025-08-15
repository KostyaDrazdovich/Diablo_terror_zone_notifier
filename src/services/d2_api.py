from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from utils.config import get_settings, Settings


# ---------------------------- Public datatypes ---------------------------------

@dataclass(frozen=True)
class TerrorZone:
    name: str
    act: Optional[str] = None
    code: Optional[str] = None


class D2ApiError(RuntimeError):
    """Network or server-side error when contacting the D2 API."""


class D2ParseError(RuntimeError):
    """Response JSON structure doesn't contain a recognizable terror zone."""


# ---------------------------- Client implementation ----------------------------

class D2ApiClient:
    def __init__(self, settings: Optional[Settings] = None, *, client: Optional[httpx.AsyncClient] = None) -> None:
        self._settings = settings or get_settings()
        self._own_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=self._settings.http_timeout_seconds,
            headers=self._build_headers(),
        )

    # -------- lifecycle --------

    async def aclose(self) -> None:
        if self._own_client:
            await self._client.aclose()

    async def __aenter__(self) -> "D2ApiClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    # -------- public API --------

    async def get_current_terror_zone(self) -> TerrorZone:
        url = self._settings.d2_api_url
        token = self._settings.d2_api_token

        last_err: Optional[Exception] = None
        retries = max(0, int(self._settings.http_retries))

        for attempt in range(retries + 1):
            try:
                resp = await self._client.get(url, params={"token": token})
                # Retry on certain status codes
                if resp.status_code >= 500 or resp.status_code == 429:
                    raise D2ApiError(f"Upstream returned HTTP {resp.status_code}")

                resp.raise_for_status()
                data = resp.json()
                tz = self._extract_current(data)
                if tz is None or not tz.name:
                    raise D2ParseError(
                        f"Missing terror zone name in response JSON. Top-level keys: {list(data) if isinstance(data, dict) else type(data)}"
                    )
                return tz

            except (httpx.TimeoutException, httpx.TransportError, D2ApiError) as e:
                last_err = e
                if attempt < retries:
                    await asyncio.sleep(self._backoff_delay(attempt))
                else:
                    raise D2ApiError(f"D2 API request failed after {attempt+1} attempts: {e}") from e
            except (ValueError, D2ParseError) as e:
                raise D2ParseError(f"Unable to parse D2 API response: {e}") from e

        raise D2ApiError(f"D2 API request failed: {last_err}")

    # -------- internals --------

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "User-Agent": "diablo-terror-bot/1.0 (+telegram)",
            "Accept": "application/json",
        }
        headers.update(self._settings.d2_request_headers())
        return headers

    @staticmethod
    def _get_str(d: Any, *path: str) -> Optional[str]:
        cur = d
        for key in path:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(key)
        if isinstance(cur, str):
            s = cur.strip()
            return s if s else None
        return None

    @staticmethod
    def _extract_current(payload: Any) -> Optional[TerrorZone]:
        if not isinstance(payload, dict):
            return None

        name = D2ApiClient._get_str(payload, "currentTerrorZone", "zone")
        if name:
            act = D2ApiClient._get_str(payload, "currentTerrorZone", "act")
            return TerrorZone(name=name, act=act)

        name = D2ApiClient._get_str(payload, "terrorZone", "reportedZones", "zone")
        if name:
            act = D2ApiClient._get_str(payload, "terrorZone", "reportedZones", "act") or D2ApiClient._get_str(payload, "terrorZone", "act")
            return TerrorZone(name=name, act=act)

        name = D2ApiClient._get_str(payload, "terrorZone", "zone")
        if name and name.lower() != "unknown":
            act = D2ApiClient._get_str(payload, "terrorZone", "act")
            return TerrorZone(name=name, act=act)

        name = D2ApiClient._get_str(payload, "current_terror_zone", "zone")
        if name:
            act = D2ApiClient._get_str(payload, "current_terror_zone", "act")
            return TerrorZone(name=name, act=act)

        name = D2ApiClient._get_str(payload, "terror_zone", "reported_zones", "zone")
        if name:
            act = D2ApiClient._get_str(payload, "terror_zone", "reported_zones", "act") or D2ApiClient._get_str(payload, "terror_zone", "act")
            return TerrorZone(name=name, act=act)

        name = D2ApiClient._get_str(payload, "terror_zone", "zone")
        if name:
            act = D2ApiClient._get_str(payload, "terror_zone", "act")
            return TerrorZone(name=name, act=act)

        name = D2ApiClient._get_str(payload, "zone")
        if name:
            return TerrorZone(name=name)

        return None

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        base = 0.5 * (2 ** attempt)
        return base + 0.05 * attempt


# ---------------------------- Convenience factory ------------------------------

def build_client(settings: Optional[Settings] = None) -> D2ApiClient:
    return D2ApiClient(settings=settings)
