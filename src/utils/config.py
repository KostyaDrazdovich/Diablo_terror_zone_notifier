from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


def _maybe_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    else:
        load_dotenv(override=False)


def _env_str(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    val = os.getenv(key, default)
    if required and (val is None or val.strip() == ""):
        raise RuntimeError(f"Missing required environment variable: {key}")
    return val


def _env_int(key: str, default: Optional[int] = None, required: bool = False) -> Optional[int]:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        if required and default is None:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return default
    try:
        return int(raw)
    except ValueError as e:
        raise RuntimeError(f"Invalid int for {key}: {raw!r}") from e


def _env_bool(key: str, default: Optional[bool] = None) -> Optional[bool]:
    raw = os.getenv(key)
    if raw is None:
        return default
    v = raw.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    raise RuntimeError(f"Invalid bool for {key}: {raw!r}")


@dataclass(frozen=True)
class Settings:
    bot_token: str

    d2_api_token: str
    d2_api_url: str = "https://d2runewizard.com/api/terror-zone"
    d2_api_contact: Optional[str] = None
    d2_api_platform: Optional[str] = "Telegram"
    d2_api_repo: Optional[str] = None

    db_dsn: Optional[str] = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "diablo_bot"

    notify_interval_seconds: int = 3600
    notify_align_minute: int = 2
    http_timeout_seconds: int = 10
    http_retries: int = 2

    default_language: str = "ru"
    supported_languages: tuple[str, ...] = ("ru",)

    log_level: str = "INFO"

    @property
    def effective_db_dsn(self) -> str:
        if self.db_dsn:
            return self.db_dsn
        pw = self.db_password
        user = self.db_user
        host = self.db_host
        port = self.db_port
        name = self.db_name
        return f"postgresql://{user}:{pw}@{host}:{port}/{name}"

    def d2_request_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.d2_api_contact:
            headers["D2R-Contact"] = self.d2_api_contact
        if self.d2_api_platform:
            headers["D2R-Platform"] = self.d2_api_platform
        if self.d2_api_repo:
            headers["D2R-Repo"] = self.d2_api_repo
        return headers


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _maybe_load_dotenv()

    bot_token = _env_str("BOT_TOKEN", required=True)
    d2_api_token = _env_str("D2_API_TOKEN", required=True)

    d2_api_url = _env_str("D2_API_URL", default="https://d2runewizard.com/api/terror-zone")
    d2_api_contact = _env_str("D2_API_CONTACT", default=None)
    d2_api_platform = _env_str("D2_API_PLATFORM", default="Telegram")
    d2_api_repo = _env_str("D2_API_REPO", default=None)

    db_dsn = _env_str("DB_DSN", default=None)
    db_host = _env_str("DB_HOST", default="localhost") or "localhost"
    db_port = _env_int("DB_PORT", default=5432) or 5432
    db_user = _env_str("DB_USER", default="postgres") or "postgres"
    db_password = _env_str("DB_PASSWORD", default="postgres") or "postgres"
    db_name = _env_str("DB_NAME", default="diablo_bot") or "diablo_bot"

    notify_interval_seconds = _env_int("NOTIFY_INTERVAL_SECONDS", default=3600) or 3600
    notify_align_minute = _env_int("NOTIFY_ALIGN_MINUTE", default=2) or 2
    http_timeout_seconds = _env_int("HTTP_TIMEOUT_SECONDS", default=10) or 10
    http_retries = _env_int("HTTP_RETRIES", default=2) or 2

    default_language = _env_str("DEFAULT_LANGUAGE", default="ru") or "ru"
    supported_languages_raw = _env_str("SUPPORTED_LANGUAGES", default="ru") or "ru"
    supported_languages = tuple(
        x.strip() for x in supported_languages_raw.split(",") if x.strip()
    )

    log_level = _env_str("LOG_LEVEL", default="INFO") or "INFO"

    return Settings(
        bot_token=bot_token,
        d2_api_token=d2_api_token,
        d2_api_url=d2_api_url or "https://d2runewizard.com/api/terror-zone",
        d2_api_contact=d2_api_contact,
        d2_api_platform=d2_api_platform,
        d2_api_repo=d2_api_repo,
        db_dsn=db_dsn,
        db_host=db_host,
        db_port=db_port,
        db_user=db_user,
        db_password=db_password,
        db_name=db_name,
        notify_interval_seconds=notify_interval_seconds,
        notify_align_minute=notify_align_minute,
        http_timeout_seconds=http_timeout_seconds,
        http_retries=http_retries,
        default_language=default_language,
        supported_languages=supported_languages,
        log_level=log_level,
    )
