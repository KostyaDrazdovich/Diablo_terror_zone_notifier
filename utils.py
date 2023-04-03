import json
import telebot

from auth_data import bot_token
from constants.strings import InfoMessages, JsonFields

user_settings_file = 'user_settings.json'


def notification_status(user_favorites, chat_id, notifications_state):
    bot = telebot.TeleBot(token=bot_token)
    user_id = str(chat_id)
    user_favorites[user_id][JsonFields.NOTIFICATIONS_ENABLED] = notifications_state
    with open(user_settings_file, 'w') as f:
        json.dump(user_favorites, f)

    if notifications_state:
        message = InfoMessages.NOTIFICATIONS_ENABLED
    else:
        message = InfoMessages.NOTIFICATIONS_DISABLED

    bot.send_message(chat_id, message)


def read_user_settings():
    with open(user_settings_file, 'r') as f:
        return json.load(f)


def update_user_settings(changed_settings):
    with open(user_settings_file, 'w') as f:
        json.dump(changed_settings, f)
