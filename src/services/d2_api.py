from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import httpx

from utils.config import Settings, get_settings


# ---------------------------- Public datatypes ---------------------------------


@dataclass(frozen=True)
class TerrorZone:
    name: str


class D2ApiError(RuntimeError):
    """Network or server-side error when contacting the terror zone source."""


class D2ParseError(RuntimeError):
    """Unable to parse terror zone information from the source page."""


# ---------------------------- Client implementation ----------------------------


class D2ApiClient:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        *,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._own_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=self._settings.http_timeout_seconds,
            headers={"User-Agent": "diablo-terror-bot/1.0 (+telegram)"},
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

    async def get_current_and_next_zones(self) -> Tuple[TerrorZone, TerrorZone]:
        """Fetch the current and upcoming terror zones."""

        url = self._settings.d2_api_url
        try:
            resp = await self._client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise D2ApiError(f"HTTP error contacting terror zone source: {e}") from e

        html = resp.text
        try:
            current_names = self._extract_names(html, "a2x")
            next_names = self._extract_names(html, "x2a")
            current = TerrorZone(name=self._compose_name(current_names))
            nxt = TerrorZone(name=self._compose_name(next_names))
            return current, nxt
        except Exception as e:
            raise D2ParseError(f"Unable to parse terror zone HTML: {e}") from e

    async def get_current_terror_zone(self) -> TerrorZone:
        current, _ = await self.get_current_and_next_zones()
        return current

    # -------- internals --------

    @staticmethod
    def _extract_names(html: str, div_id: str) -> List[str]:
        import re

        pattern = rf'<div id="{div_id}">(.*?)</div>'
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError(f"div #{div_id} not found")
        block = match.group(1)
        return [p.strip() for p in block.split("<br>") if p.strip()]

    @staticmethod
    def _compose_name(parts: List[str]) -> str:
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        if len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        return ", ".join(parts[:-1]) + f", and {parts[-1]}"


# ---------------------------- Convenience factory ------------------------------


def build_client(settings: Optional[Settings] = None) -> D2ApiClient:
    return D2ApiClient(settings=settings)
