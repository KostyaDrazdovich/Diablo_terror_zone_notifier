from __future__ import annotations

from typing import Iterable, Sequence

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from constants.locations import (
    ACT1, ACT2, ACT3, ACT4, ACT5,
    codes_for_act, name_by_code,
)

ACT_TITLES_UI = {
    ACT1: "Act I",
    ACT2: "Act II",
    ACT3: "Act III",
    ACT4: "Act IV",
    ACT5: "Act V",
}

# ----------------------------- Main inline menu ------------------------------

def main_menu_inline() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("Current terror zone", callback_data="menu:current")],
        [InlineKeyboardButton("Choose locations", callback_data="menu:choose")],
        [InlineKeyboardButton("My locations list", callback_data="menu:list")],
        [InlineKeyboardButton("Notification settings", callback_data="menu:notif")],
        [InlineKeyboardButton("Close", callback_data="close")],
    ]
    return InlineKeyboardMarkup(rows)


def menu_nav_markup() -> InlineKeyboardMarkup:
    row = [
        InlineKeyboardButton("Menu", callback_data="menu:open"),
        InlineKeyboardButton("Close", callback_data="close"),
    ]
    return InlineKeyboardMarkup([row])


# ----------------------------- Inline sub-menus ------------------------------

def acts_inline_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for idx, act in enumerate((ACT1, ACT2, ACT3, ACT4, ACT5), start=1):
        title = ACT_TITLES_UI.get(act, act)
        rows.append([InlineKeyboardButton(title, callback_data=f"act:{idx}")])
    rows.append([
        InlineKeyboardButton("Menu", callback_data="menu:open"),
        InlineKeyboardButton("Close", callback_data="close"),
    ])
    return InlineKeyboardMarkup(rows)


def locations_inline_keyboard(act_number: int, selected_codes: Iterable[str]) -> InlineKeyboardMarkup:
    act_map = {1: ACT1, 2: ACT2, 3: ACT3, 4: ACT4, 5: ACT5}
    act_title = act_map.get(act_number)
    if not act_title:
        return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back:acts")]])

    selected = set(str(c) for c in selected_codes)
    codes: Sequence[str] = codes_for_act(act_title)

    rows: list[list[InlineKeyboardButton]] = []
    buf: list[InlineKeyboardButton] = []
    for code in codes:
        checked = "✅ " if code in selected else "▫ "
        label = f"{checked}{name_by_code(code)}"
        btn = InlineKeyboardButton(label, callback_data=f"loc:{code}:toggle")
        buf.append(btn)
        if len(buf) == 2:
            rows.append(buf)
            buf = []
    if buf:
        rows.append(buf)

    rows.append([
        InlineKeyboardButton("Back", callback_data="menu:open"),
        InlineKeyboardButton("Close", callback_data="close"),
    ])
    return InlineKeyboardMarkup(rows)


def selected_locations_inline_keyboard(selected_codes: Iterable[str]) -> InlineKeyboardMarkup:
    selected = set(str(c) for c in selected_codes)

    act_order = [(1, ACT1), (2, ACT2), (3, ACT3), (4, ACT4), (5, ACT5)]
    rows: list[list[InlineKeyboardButton]] = []

    any_act = False
    for _, act_title in act_order:
        act_codes = [c for c in codes_for_act(act_title) if c in selected]
        if not act_codes:
            continue
        any_act = True

        raw_title = ACT_TITLES_UI.get(act_title, act_title)
        header_text = f"◆ {raw_title.upper()} ◆"   # мягкий «золотистый» акцент без эмодзи-цвета
        rows.append([InlineKeyboardButton(header_text, callback_data="noop")])

        buf: list[InlineKeyboardButton] = []
        for code in act_codes:
            buf.append(InlineKeyboardButton(name_by_code(code), callback_data=f"loc:{code}:toggle"))
            if len(buf) == 2:
                rows.append(buf); buf = []
        if buf:
            rows.append(buf)

    if not any_act:
        return InlineKeyboardMarkup([[InlineKeyboardButton("Menu", callback_data="menu:open")]])

    rows.append([
        InlineKeyboardButton("Back", callback_data="menu:open"),
        InlineKeyboardButton("Close", callback_data="close"),
    ])
    return InlineKeyboardMarkup(rows)


def notifications_inline_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if enabled:
        rows.append([InlineKeyboardButton("Turn off notifications", callback_data="notif:off")])
    else:
        rows.append([InlineKeyboardButton("Turn on notifications", callback_data="notif:on")])
    rows.append([InlineKeyboardButton("Time schedule (UTC)", callback_data="notif:window")])
    rows.append([
        InlineKeyboardButton("Menu", callback_data="menu:open"),
        InlineKeyboardButton("Close", callback_data="close"),
    ])
    return InlineKeyboardMarkup(rows)
