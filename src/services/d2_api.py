from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from playwright.async_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

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
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._playwright = None
        self._browser = None

    # -------- lifecycle --------

    async def aclose(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def __aenter__(self) -> "D2ApiClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    # -------- public API --------

    async def get_current_and_next_zones(self) -> Tuple[TerrorZone, TerrorZone]:
        """Fetch the current and upcoming terror zones."""

        url = self._settings.d2_api_url
        await self._ensure_browser()
        page = await self._browser.new_page()
        timeout_ms = self._settings.http_timeout_seconds * 1000
        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            await page.wait_for_selector("#a2x", timeout=timeout_ms)
            await page.wait_for_selector("#x2a", timeout=timeout_ms)
            current_block = await page.inner_text("#a2x")
            next_block = await page.inner_text("#x2a")
        except PlaywrightTimeoutError as e:
            raise D2ApiError(f"Timeout contacting terror zone source: {e}") from e
        except PlaywrightError as e:
            raise D2ApiError(f"Error contacting terror zone source: {e}") from e
        finally:
            await page.close()

        try:
            current_names = self._split_names(current_block)
            next_names = self._split_names(next_block)
            current = TerrorZone(name=self._compose_name(current_names))
            nxt = TerrorZone(name=self._compose_name(next_names))
            return current, nxt
        except Exception as e:
            raise D2ParseError(f"Unable to parse terror zone HTML: {e}") from e

    async def get_current_terror_zone(self) -> TerrorZone:
        current, _ = await self.get_current_and_next_zones()
        return current

    # -------- internals --------

    async def _ensure_browser(self) -> None:
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

    @staticmethod
    def _split_names(block: str) -> List[str]:
        return [p.strip() for p in block.replace("\r", "").splitlines() if p.strip()]

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
