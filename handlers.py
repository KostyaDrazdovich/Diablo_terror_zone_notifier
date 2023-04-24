import requests
import telebot

from auth_data import d2rwizard_token
from constants.strings import Buttons, CommandsMessages, Locations, InfoMessages as Im, JsonFields
from utils import notification_status


def get_current_terror_zone():
    # https://d2runewizard.com/integration#authorization
    headers = {'D2R-Contact': 'just_sample@gmail.com', 'D2R-Platform': 'Telegram', 'D2R-Repo': 'https://github.com/'}
    response = requests.get(f"https://d2runewizard.com/api/terror-zone?token={d2rwizard_token}", headers=headers).json()
    reported_zones = response[JsonFields.TERROR_ZONE][JsonFields.REPORTED_ZONES]
    if reported_zones:
        reported_zone_name = next(iter(reported_zones))
        return reported_zone_name['zone']
    else:
        return response[JsonFields.TERROR_ZONE]['zone']


def send_message(bot, message, user_favorite_tz):
    if message.text == Buttons.HELP:
        bot.send_message(message.chat.id, CommandsMessages.HELP)
    elif message.text == Buttons.CURRENT:
        terror_zone = get_current_terror_zone()
        bot.send_message(message.chat.id, CommandsMessages.CURRENT_TERROR_ZONE.format(terror_zone))

    elif message.text == Buttons.SELECT:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ACT1, callback_data=Locations.ACT1),
            telebot.types.InlineKeyboardButton(Locations.ACT2, callback_data=Locations.ACT2)
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ACT3, callback_data=Locations.ACT3),
            telebot.types.InlineKeyboardButton(Locations.ACT4, callback_data=Locations.ACT4)
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ACT5, callback_data=Locations.ACT5),
            telebot.types.InlineKeyboardButton(Buttons.CLOSE, callback_data=Buttons.CLOSE)
        )
        bot.send_message(message.chat.id, Im.SELECT_FAVORITE_TERROR_ZONE, reply_markup=keyboard)

    elif message.text == Buttons.FAV:
        favorite_terror_zones = user_favorite_tz.get(str(message.chat.id), {}).get(JsonFields.ZONES, [])
        if not favorite_terror_zones:
            bot.send_message(message.chat.id, Im.NO_SELECTED_TERROR_ZONES)
        else:
            message_text = CommandsMessages.FAV_USER_ZONES
            for zones in favorite_terror_zones:
                message_text += f"{zones}\n"
            bot.send_message(message.chat.id, message_text)

    elif message.text == Buttons.REMOVE:
        favorite_terror_zones = user_favorite_tz.get(str(message.chat.id), {}).get(JsonFields.ZONES, [])
        if not favorite_terror_zones:
            bot.send_message(message.chat.id, Im.NO_SELECTED_TERROR_ZONES)
        else:
            keyboard = telebot.types.InlineKeyboardMarkup()
            for index, fav in enumerate(favorite_terror_zones):
                keyboard.add(telebot.types.InlineKeyboardButton(fav, callback_data=f"remove_{index}"))
            keyboard.add(telebot.types.InlineKeyboardButton(Buttons.CLOSE, callback_data=Buttons.CLOSE))
            bot.send_message(message.chat.id, CommandsMessages.SELECT_ZONE_TO_REMOVE, reply_markup=keyboard)

    elif message.text == Buttons.NOTIFICATION_STATUS:
        user_id = str(message.chat.id)
        if user_id not in user_favorite_tz:
            bot.send_message(message.chat.id, Im.NO_SELECTED_TERROR_ZONES)
        else:
            notifications_enabled = user_favorite_tz[user_id].get(JsonFields.NOTIFICATIONS_ENABLED, False)
            if notifications_enabled:
                bot.send_message(message.chat.id, Im.NOTIFICATIONS_ENABLED)
            else:
                bot.send_message(message.chat.id, Im.NOTIFICATIONS_DISABLED)

    elif message.text == Buttons.NOTIFICATION_START:
        user_id = str(message.chat.id)
        if user_favorite_tz.get(user_id, {}).get(JsonFields.NOTIFICATIONS_ENABLED, False):
            bot.send_message(message.chat.id, Im.NOTIFICATIONS_ALREADY_ENABLED)
        else:
            notification_status(user_favorite_tz, message.chat.id, True)

    elif message.text == Buttons.NOTIFICATION_STOP:
        user_id = str(message.chat.id)
        if not user_favorite_tz.get(user_id, {}).get(JsonFields.NOTIFICATIONS_ENABLED, False):
            bot.send_message(message.chat.id, Im.NOTIFICATIONS_ALREADY_DISABLED)
        else:
            notification_status(user_favorite_tz, message.chat.id, False)


def terror_zone_selection(bot, call):
    act = call.data
    keyboard = telebot.types.InlineKeyboardMarkup()
    if act == Locations.ACT1:
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.1'], callback_data="1.1"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.2'], callback_data="1.2")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.3'], callback_data="1.3"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.4'], callback_data="1.4")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.5'], callback_data="1.5"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.6'], callback_data="1.6")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.7'], callback_data="1.7"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.8'], callback_data="1.8")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.9'], callback_data="1.9"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.10'], callback_data="1.10")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.11'], callback_data="1.11"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['1.12'], callback_data="1.12")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Buttons.CLOSE, callback_data=Buttons.CLOSE)
        )
    elif act == Locations.ACT2:
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['2.1'], callback_data="2.1"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['2.2'], callback_data="2.2")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['2.3'], callback_data="2.3"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['2.4'], callback_data="2.4")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['2.5'], callback_data="2.5"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['2.6'], callback_data="2.6")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['2.7'], callback_data="2.7"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['2.8'], callback_data="2.8")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Buttons.CLOSE, callback_data=Buttons.CLOSE)
        )
    elif act == Locations.ACT3:
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['3.1'], callback_data="3.1"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['3.2'], callback_data="3.2")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['3.3'], callback_data="3.3"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['3.4'], callback_data="3.4")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['3.5'], callback_data="3.5"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['3.6'], callback_data="3.6")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Buttons.CLOSE, callback_data=Buttons.CLOSE)
        )
    elif act == Locations.ACT4:
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['4.1'], callback_data="4.1"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['4.2'], callback_data="4.2")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['4.3'], callback_data="4.3"),
            telebot.types.InlineKeyboardButton(Buttons.CLOSE, callback_data=Buttons.CLOSE)
        )
    elif act == Locations.ACT5:
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['5.1'], callback_data="5.1"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['5.2'], callback_data="5.2")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['5.3'], callback_data="5.3"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['5.4'], callback_data="5.4")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['5.5'], callback_data="5.5"),
            telebot.types.InlineKeyboardButton(Locations.ZONES['5.6'], callback_data="5.6")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(Locations.ZONES['5.7'], callback_data="5.7"),
            telebot.types.InlineKeyboardButton(Buttons.CLOSE, callback_data=Buttons.CLOSE)
        )

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=Im.SELECT_LOCATION_FOR_ACT.format(act),
        reply_markup=keyboard
    )
