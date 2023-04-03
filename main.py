import schedule
import telebot
import threading
import time

from auth_data import bot_token
from constants.strings import Buttons, CommandsMessages as Cm, Locations, JsonFields
from handlers import send_message, terror_zone_selection, get_current_terror_zone
from utils import update_user_settings, read_user_settings


def telegram_bot(token):
    bot = telebot.TeleBot(token=token)

    @bot.message_handler(commands=[Buttons.START])
    def start_message(message):
        bot.send_message(message.chat.id, Cm.START)

    @bot.message_handler(content_types=["text"])
    def send_message_handler(message):
        user_favorites = read_user_settings()
        send_message(bot, message, user_favorite_tz=user_favorites)

    @bot.callback_query_handler(
        func=lambda call: call.data in [Locations.ACT1, Locations.ACT2, Locations.ACT3, Locations.ACT4, Locations.ACT5])
    def handle_act_selection_handler(call):
        terror_zone_selection(bot, call)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        user_favorite_tz = read_user_settings()

        if call.data == Buttons.CLOSE:
            bot.answer_callback_query(call.id, text=Cm.CLOSED)
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        elif call.data.startswith("remove_"):
            index = int(call.data.split("_")[1])
            user_id = call.message.chat.id
            favorite_terror_zones = user_favorite_tz.get(str(user_id), {}).get(JsonFields.ZONES, [])
            if index < len(favorite_terror_zones):
                zone_to_remove = favorite_terror_zones[index]
                favorite_terror_zones.remove(zone_to_remove)
                user_favorite_tz[str(user_id)] = {
                    JsonFields.ZONES: favorite_terror_zones,
                    JsonFields.NOTIFICATIONS_ENABLED: user_favorite_tz.get
                    (str(user_id), {}).get(JsonFields.NOTIFICATIONS_ENABLED, True)}
                update_user_settings(user_favorite_tz)
                bot.send_message(chat_id=user_id,
                                 text=Cm.ZONE_REMOVED_FROM_FAV.format(zone_to_remove),
                                 reply_markup=None)
            else:
                bot.send_message(chat_id=user_id, text=Cm.ZONE_ALREADY_REMOVED, reply_markup=None)

        else:
            user_id = call.message.chat.id
            favorite_terror_zones = user_favorite_tz.get(str(user_id), {}).get(JsonFields.ZONES, [])
            selected_zone = Locations.ZONES[call.data]
            if selected_zone not in favorite_terror_zones:
                favorite_terror_zones.append(selected_zone)
                user_favorite_tz[str(user_id)] = {JsonFields.ZONES: favorite_terror_zones,
                                                  JsonFields.NOTIFICATIONS_ENABLED: user_favorite_tz.get
                                                  (str(user_id), {}).get(JsonFields.NOTIFICATIONS_ENABLED, True)}
                update_user_settings(user_favorite_tz)
                bot.send_message(chat_id=user_id, text=Cm.ZONE_ADDED_TO_FAV.format(selected_zone), reply_markup=None)
            else:
                bot.send_message(chat_id=user_id, text=Cm.ZONE_ALREADY_IN_FAV.format(selected_zone))

    def check_and_send_notifications():
        user_favorites = read_user_settings()
        for user_id, settings in user_favorites.items():
            if not settings[JsonFields.NOTIFICATIONS_ENABLED]:
                continue
            terror_zone = get_current_terror_zone()
            if terror_zone in settings[JsonFields.ZONES]:
                bot.send_message(chat_id=user_id, text=Cm.CURRENT_TERROR_ZONE.format(terror_zone))

    def run_bot():
        bot.polling(none_stop=True)

    def run_schedule():
        schedule.every().hour.at(":01").do(check_and_send_notifications)
        # Temporarily disabled
        # schedule.every().minute.do(check_and_send_notifications)
        # schedule.every().day.at("23:02").do(notification_status, False)
        # schedule.every().day.at("09:00").do(notification_status, True)
        while True:
            schedule.run_pending()
            time.sleep(1)

    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()

    bot_thread.join()
    schedule_thread.join()


if __name__ == '__main__':
    telegram_bot(bot_token)
