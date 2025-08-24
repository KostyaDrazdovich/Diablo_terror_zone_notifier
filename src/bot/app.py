from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, JobQueue

from utils.config import get_settings
from db.dal import (
    create_engine, create_session_factory, ensure_schema,
    upsert_user, set_notifications_enabled, set_notification_window, users_to_notify_for_location,
)
from services.d2_api import D2ApiClient, D2ApiError, D2ParseError
from constants.locations import code_by_name, name_by_code
from bot.keyboards import main_menu_inline
from bot.handlers import register_handlers


def _setup_logging() -> None:
    settings = get_settings()
    lvl = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=lvl, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")


log = logging.getLogger("bot.app")


def _next_aligned_run_utc(minute: int) -> datetime:
    now = datetime.now(timezone.utc)
    target = now.replace(minute=minute, second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(hours=1)
    return target


def _parse_window(arg: str):
    try:
        s_raw, e_raw = arg.strip().split("-")
        s, e = int(s_raw), int(e_raw)
        if not (0 <= s <= 24 and 0 <= e <= 24):
            return None
        return s, e
    except Exception:
        return None


# ----------------------------- Commands --------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await menu_cmd(update, context)


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    if update.effective_user is not None:
        session_factory = context.application.bot_data["session_factory"]
        async with session_factory() as session:
            await upsert_user(session, update.effective_user.id)

    await context.bot.send_message(chat_id=chat_id, text="Main menu:", reply_markup=main_menu_inline())


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await notify_off(update, context)


async def current(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    client: D2ApiClient = context.application.bot_data["d2_client"]
    try:
        current_tz, next_tz = await client.get_current_and_next_zones()
        code = code_by_name(current_tz.name)
        current_name = name_by_code(code) if code else current_tz.name
        next_code = code_by_name(next_tz.name)
        next_name = name_by_code(next_code) if next_code else next_tz.name
        text = f"Current zone: {current_name}\nNext zone: {next_name}"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    except (D2ApiError, D2ParseError) as e:
        log.warning("Failed to fetch current zone: %s", e)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Couldn't get the current zone. Please try again later.",
        )


async def notify_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    session_factory = context.application.bot_data["session_factory"]
    async with session_factory() as session:
        await set_notifications_enabled(session, update.effective_user.id, True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Notifications turned on.")


async def notify_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    session_factory = context.application.bot_data["session_factory"]
    async with session_factory() as session:
        await set_notifications_enabled(session, update.effective_user.id, False)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Notifications turned off.")


async def set_window_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Provide a range in HH-HH format, e.g.: /set_window 8-23",
        )
        return
    parsed = _parse_window(context.args[0])
    if not parsed:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Invalid format. Use: /set_window 0-24 (UTC).",
        )
        return
    start_hour, end_hour = parsed
    session_factory = context.application.bot_data["session_factory"]
    async with session_factory() as session:
        await set_notification_window(session, update.effective_user.id, start_hour, end_hour)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Notification window (UTC) set to: {start_hour:02d}-{end_hour:02d}",
    )


# ----------------------------- Scheduler job ---------------------------------

async def check_and_notify(context: ContextTypes.DEFAULT_TYPE) -> None:
    from datetime import datetime, timedelta, timezone

    store = context.application.bot_data
    client: D2ApiClient = store["d2_client"]

    now = datetime.now(timezone.utc)
    bypass = now.minute <= 5
    zones = None

    if not bypass:
        cached = store.get("tz_cache")
        ts = store.get("tz_cache_ts")
        if cached is not None and ts is not None and (now - ts) <= timedelta(minutes=10):
            zones = cached

    try:
        if zones is None:
            zones = await client.get_current_and_next_zones()
            store["tz_cache"] = zones
            store["tz_cache_ts"] = now

        current_tz = zones[0]
        code = code_by_name(current_tz.name)
        if not code:
            logging.getLogger("bot.app").warning("Unknown terror zone from source: %r", current_tz.name)
            return

        async with store["session_factory"]() as session:
            user_ids = await users_to_notify_for_location(session, code, now_utc=now)

        if not user_ids:
            return

        text = f"Zone active now: {name_by_code(code)}"
        for uid in user_ids:
            try:
                await context.bot.send_message(chat_id=uid, text=text)
            except Exception as e:
                logging.getLogger("bot.app").warning("Failed to send message to %s: %s", uid, e)

    except (D2ApiError, D2ParseError) as e:
        logging.getLogger("bot.app").warning("Scheduled job: failed to fetch zone: %s", e)


# ----------------------------- App bootstrap ---------------------------------

async def build_application() -> Application:
    settings = get_settings()
    _setup_logging()
    log.info("Starting application...")

    engine = create_engine(settings.effective_db_dsn)
    await ensure_schema(engine)
    session_factory = create_session_factory(engine)

    d2_client = D2ApiClient(settings=settings)

    async def _on_shutdown(app: Application) -> None:
        log.info("Shutting down...")
        try:
            await d2_client.aclose()
        except Exception as e:
            log.warning("D2 client close error: %s", e)
        try:
            await engine.dispose()
        except Exception as e:
            log.warning("Engine dispose error: %s", e)

    jq = JobQueue()
    app = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .job_queue(jq)
        .post_shutdown(_on_shutdown)
        .build()
    )

    app.bot_data["settings"] = settings
    app.bot_data["session_factory"] = session_factory
    app.bot_data["engine"] = engine
    app.bot_data["d2_client"] = d2_client

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("current", current))
    app.add_handler(CommandHandler("notify_on", notify_on))
    app.add_handler(CommandHandler("notify_off", notify_off))
    app.add_handler(CommandHandler("set_window", set_window_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))

    register_handlers(app)

    # Periodic job
    first_run = _next_aligned_run_utc(settings.notify_align_minute)
    app.job_queue.run_repeating(
        check_and_notify,
        interval=settings.notify_interval_seconds,
        first=first_run,
        name="check_and_notify",
    )
    log.info("Job scheduled: first run at %s (UTC)", first_run.isoformat())

    return app


async def amain() -> None:
    app = await build_application()
    log.info("Bot up. Polling…")

    await app.initialize()
    await app.start()

    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()



def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
