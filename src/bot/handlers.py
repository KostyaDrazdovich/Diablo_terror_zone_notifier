from __future__ import annotations

import logging
from typing import Optional

from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.keyboards import (
    acts_inline_keyboard,
    locations_inline_keyboard,
    main_menu_inline,
    menu_nav_markup,
    notifications_inline_keyboard,
    selected_locations_inline_keyboard,
)
from constants.locations import code_by_name, name_by_code
from db.dal import (
    add_location, get_user, get_user_locations,
    remove_location, set_notification_window, set_notifications_enabled,
)
from services.d2_api import D2ApiClient, D2ApiError, D2ParseError

log = logging.getLogger("bot.handlers")

# ----------------------------- Utilities -------------------------------------

def _parse_act(data: str) -> Optional[int]:
    try:
        return int(data.split(":", 1)[1])
    except Exception:
        return None


def _parse_loc_toggle(data: str) -> Optional[str]:
    try:
        _, code, action = data.split(":")
        return code if action == "toggle" else None
    except Exception:
        return None


def _code_to_act_num(code: str) -> Optional[int]:
    try:
        return int(str(code).split(".", 1)[0])
    except Exception:
        return None


def _parse_window_set(data: str) -> Optional[tuple[int, int]]:
    try:
        _, action, rng = data.split(":")
        if action != "set":
            return None
        s_raw, e_raw = rng.split("-")
        s, e = int(s_raw), int(e_raw)
        if not (0 <= s <= 24 and 0 <= e <= 24):
            return None
        return s, e
    except Exception:
        return None


def _window_presets_keyboard():
    rows = [
        [InlineKeyboardButton("24/7", callback_data="window:set:0-24"),
         InlineKeyboardButton("07–21", callback_data="window:set:7-21")],
        [InlineKeyboardButton("Custom", callback_data="schedule:custom")],
        [InlineKeyboardButton("Back", callback_data="menu:open"),
         InlineKeyboardButton("Close", callback_data="close")],
    ]
    return InlineKeyboardMarkup(rows)


def _hours_keyboard(kind: str) -> "InlineKeyboardMarkup":
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    rows: list[list[InlineKeyboardButton]] = []
    buf: list[InlineKeyboardButton] = []
    for h in range(24):
        label = f"{h:02d}"
        buf.append(InlineKeyboardButton(label, callback_data=f"cust:{kind}:{h:02d}"))
        if len(buf) == 6:
            rows.append(buf); buf = []
    if buf:
        rows.append(buf)
    rows.append([InlineKeyboardButton("Back", callback_data="menu:open"),
                 InlineKeyboardButton("Close", callback_data="close")])
    return InlineKeyboardMarkup(rows)

# ----------------------------- Fallback for old reply buttons -----------------


async def on_any_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return
    chat_id = update.effective_chat.id
    tmp = await context.bot.send_message(chat_id=chat_id, text=".", reply_markup=ReplyKeyboardRemove())
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=tmp.message_id)
    except Exception:
        pass
    await update.effective_chat.send_message("Main menu:", reply_markup=main_menu_inline())

# ----------------------------- Callback handling -----------------------------

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query is None:
        return
    cq = update.callback_query
    data = cq.data or ""
    session_factory = context.application.bot_data["session_factory"]

    if data == "noop":
        await cq.answer()
        return

    # -------- Notifications toggle (explicit handling) --------
    if data in ("notif:on", "notifications:on"):
        if update.effective_user is None:
            await cq.answer(); return
        async with session_factory() as session:
            await set_notifications_enabled(session, update.effective_user.id, True)
            user = await get_user(session, update.effective_user.id)
            enabled = bool(user.notifications_enabled) if user else True
        await cq.edit_message_text("Notifications turned on.", reply_markup=notifications_inline_keyboard(enabled))
        await cq.answer(); return

    if data in ("notif:off", "notifications:off"):
        if update.effective_user is None:
            await cq.answer(); return
        async with session_factory() as session:
            await set_notifications_enabled(session, update.effective_user.id, False)
            user = await get_user(session, update.effective_user.id)
            enabled = bool(user.notifications_enabled) if user else False
        await cq.edit_message_text("Notifications turned off.", reply_markup=notifications_inline_keyboard(enabled))
        await cq.answer(); return

    # -------- Main menu navigation --------
    if data == "menu:open":
        await cq.edit_message_text("Main menu:", reply_markup=main_menu_inline())
        await cq.answer(); return

    if data == "menu:current":
        try:
            current_tz, next_tz = await _get_current_zones_cached(context)
            code = code_by_name(current_tz.name)
            current_name = name_by_code(code) if code else current_tz.name
            next_code = code_by_name(next_tz.name)
            next_name = name_by_code(next_code) if next_code else next_tz.name
            text = f"Current terror zone: {current_name}\nNext terror zone: {next_name}"
        except (D2ApiError, D2ParseError) as e:
            log.warning("Failed to fetch current zone: %s", e)
            text = "Couldn't get the current terror zone. Please try again later."
        await cq.edit_message_text(text, reply_markup=menu_nav_markup())
        await cq.answer(); return

    if data == "menu:choose":
        await cq.edit_message_text("Choose an Act:", reply_markup=acts_inline_keyboard())
        await cq.answer(); return

    if data == "menu:list":
        if update.effective_user is None:
            await cq.answer(); return
        async with session_factory() as session:
            selected = await get_user_locations(session, update.effective_user.id)
        if not selected:
            await cq.edit_message_text("You haven't selected any locations yet.", reply_markup=menu_nav_markup())
            await cq.answer(); return
        await cq.edit_message_text("Your selected locations:", reply_markup=selected_locations_inline_keyboard(selected))
        await cq.answer(); return

    if data == "menu:notif":
        if update.effective_user is None:
            await cq.answer(); return
        async with session_factory() as session:
            user = await get_user(session, update.effective_user.id)
            enabled = bool(user.notifications_enabled) if user else False
        await cq.edit_message_text("Notification settings:", reply_markup=notifications_inline_keyboard(enabled))
        await cq.answer(); return

    if data == "menu:schedule":
        if update.effective_user is None:
            await cq.answer(); return
        async with session_factory() as session:
            user = await get_user(session, update.effective_user.id)
        start, end, enabled = _extract_window_from_user(user) if user else (0, 24, False)
        text = (
            "Pick a UTC time schedule preset\n"
            f"Current window (UTC): {start:02d}–{end:02d}"
        )
        if not enabled:
            text += "\nNotifications are currently OFF."
        await cq.edit_message_text(text, reply_markup=_window_presets_keyboard())
        await cq.answer()
        return

    # -------- Schedule (presets & custom) --------
    if data == "notif:window":
        if update.effective_user is None:
            await cq.answer(); return
        async with session_factory() as session:
            user = await get_user(session, update.effective_user.id)
        start, end, enabled = _extract_window_from_user(user) if user else (0, 24, False)
        text = (
            "Pick a UTC time schedule preset\n"
            f"Current window (UTC): {start:02d}–{end:02d}"
        )
        if not enabled:
            text += "\nNotifications are currently OFF."
        await cq.edit_message_text(text, reply_markup=_window_presets_keyboard())
        await cq.answer(); return

    if data.startswith("window:set:"):
        if update.effective_user is None:
            await cq.answer("No user", show_alert=False); return
        parsed = _parse_window_set(data)
        if not parsed:
            await cq.answer("Invalid window format", show_alert=False); return
        s, e = parsed
        async with session_factory() as session:
            await set_notification_window(session, update.effective_user.id, s, e)
        await cq.edit_message_text(f"Notification window (UTC) set to: {s:02d}-{e:02d}")
        await cq.answer(); return

    if data == "schedule:custom":
        await cq.edit_message_text("Select start hour (UTC):", reply_markup=_hours_keyboard("start"))
        await cq.answer(); return

    if data.startswith("cust:start:"):
        try:
            start = int(data.split(":")[2])
        except Exception:
            await cq.answer("Invalid hour", show_alert=False); return
        context.user_data["cust_start_hour"] = start
        await cq.edit_message_text("Select end hour (UTC):", reply_markup=_hours_keyboard("end"))
        await cq.answer(); return

    if data.startswith("cust:end:"):
        if update.effective_user is None:
            await cq.answer("No user", show_alert=False); return
        try:
            end = int(data.split(":")[2])
        except Exception:
            await cq.answer("Invalid hour", show_alert=False); return
        start = context.user_data.get("cust_start_hour")
        if start is None:
            await cq.edit_message_text(
                "Pick a UTC time schedule preset:",
                reply_markup=_window_presets_keyboard(),
            )
            await cq.answer(); return

        if not (0 <= start <= 23 and 0 <= end <= 23) or start > end:
            await cq.edit_message_text(
                "Invalid range. Start must be ≤ end (e.g., 07–21) or equal for a single hour (e.g., 07–07). "
                "No changes saved.",
                reply_markup=_window_presets_keyboard(),
            )
            context.user_data.pop("cust_start_hour", None)
            await cq.answer(); return

        async with session_factory() as session:
            await set_notification_window(session, update.effective_user.id, int(start), int(end))

        context.user_data.pop("cust_start_hour", None)
        await cq.edit_message_text(f"Notification window (UTC) set to: {int(start):02d}-{int(end):02d}")
        await cq.answer(); return

    # -------- Acts & locations --------
    if data.startswith("act:"):
        act_num = _parse_act(data)
        if act_num is None:
            await cq.answer("Unknown act", show_alert=False); return
        selected = set()
        if update.effective_user:
            async with session_factory() as session:
                selected = await get_user_locations(session, update.effective_user.id)
        await cq.edit_message_text(
            text=f"Select locations (Act {act_num}):",
            reply_markup=locations_inline_keyboard(act_num, selected),
        )
        await cq.answer(); return

    if data.startswith("loc:"):
        code = _parse_loc_toggle(data)
        if code is None or update.effective_user is None:
            await cq.answer("Data error", show_alert=False); return
        async with session_factory() as session:
            inserted = await add_location(session, update.effective_user.id, code)
            if not inserted:
                await remove_location(session, update.effective_user.id, code)
            selected = await get_user_locations(session, update.effective_user.id)
        act_num = _code_to_act_num(code)
        if act_num is None:
            await cq.edit_message_text("Choose an Act:", reply_markup=acts_inline_keyboard())
        else:
            await cq.edit_message_text(
                text=f"Select locations (Act {act_num}):",
                reply_markup=locations_inline_keyboard(act_num, selected),
            )
        await cq.answer("Added" if inserted else "Removed", show_alert=False); return

    # -------- Navigation & misc --------
    if data == "back:acts":
        await cq.edit_message_text("Choose an Act:", reply_markup=acts_inline_keyboard())
        await cq.answer(); return

    if data == "back:notif":
        if update.effective_user is None:
            await cq.answer(); return
        async with session_factory() as session:
            user = await get_user(session, update.effective_user.id)
            enabled = bool(user.notifications_enabled) if user else False
        await cq.edit_message_text("Notifications:", reply_markup=notifications_inline_keyboard(enabled))
        await cq.answer(); return

    if data == "close":
        try:
            await cq.message.delete()
        except Exception:
            try:
                await cq.edit_message_text("Closed.")
            except Exception:
                pass
        await cq.answer(); return

    await cq.answer("Unknown action", show_alert=False)


def _extract_window_from_user(user) -> tuple[int, int, bool]:
    """
    Возвращает (start_hour, end_hour, notifications_enabled) из ORM-объекта User,
    не используя sqlalchemy.inspection.inspect. Интроспектим доступные атрибуты.
    """
    names: list[str]
    try:
        names = [attr.key for attr in getattr(user, "__mapper__").attrs]
    except Exception:
        names = [n for n in dir(user) if not n.startswith("_")]

    values: dict[str, object] = {}
    for name in names:
        try:
            values[name] = getattr(user, name)
        except Exception:
            continue

    enabled = bool(values.get("notifications_enabled", False))

    numeric: dict[str, int] = {}
    for k, v in values.items():
        if isinstance(v, int) and 0 <= v <= 24:
            numeric[k] = int(v)

    def pick_start_end(kind: str) -> int | None:
        is_end = (kind == "end")
        keywords_primary = ("end", "to") if is_end else ("start", "from")
        best_key: str | None = None
        best_score = 10**9

        for k, val in numeric.items():
            lk = k.lower()
            if not any(w in lk for w in keywords_primary):
                continue
            score = 0
            if "hour" in lk: score -= 2
            if "window" in lk: score -= 2
            if "notify" in lk or "notif" in lk or "notification" in lk: score -= 1
            if "utc" in lk: score -= 1
            score += len(lk) // 10
            if score < best_score:
                best_score = score
                best_key = k

        return numeric.get(best_key) if best_key is not None else None

    start = pick_start_end("start")
    end = pick_start_end("end")

    if start is None or end is None:
        def weight(k: str) -> int:
            lk = k.lower()
            w = 0
            if "start" in lk or "from" in lk: w -= 3
            if "end" in lk or "to" in lk: w -= 3
            if "hour" in lk: w -= 2
            if "window" in lk: w -= 2
            if "notify" in lk or "notif" in lk or "notification" in lk: w -= 1
            if "utc" in lk: w -= 1
            return w

        ordered = sorted(numeric.keys(), key=weight)
        cand_start = next((k for k in ordered if any(s in k.lower() for s in ("start", "from"))), None)
        cand_end = next((k for k in ordered if any(e in k.lower() for e in ("end", "to")) and k != cand_start), None)
        if cand_start is not None and cand_end is not None:
            start = numeric[cand_start]
            end = numeric[cand_end]

    if start is None or end is None:
        raise LookupError("Cannot determine notification window fields on User")

    return int(start), int(end), enabled


async def _get_current_zones_cached(context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime, timedelta, timezone

    store = context.application.bot_data
    client: D2ApiClient = store["d2_client"]
    now = datetime.now(timezone.utc)

    bypass = now.minute < 5

    if not bypass:
        cached = store.get("tz_cache")
        ts = store.get("tz_cache_ts")
        if cached is not None and ts is not None and (now - ts) <= timedelta(minutes=10):
            return cached

    zones = await client.get_current_and_next_zones()
    store["tz_cache"] = zones
    store["tz_cache_ts"] = now
    return zones


def register_handlers(app: Application) -> None:
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_any_text))
    app.add_handler(CallbackQueryHandler(on_callback))
