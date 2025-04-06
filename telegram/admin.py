from telebot import types
from settings import ADMIN_IDS
import db
from telegram.messages import Buttons
from telegram.keyboards import admin_menu
import telegram.monitoring as monitoring
from telegram.server import bot
from telegram.keyboards import main_menu

waiting_for_vip = False

def is_admin(user_id):
    return user_id in ADMIN_IDS

def handle_admin_commands(message):
    """Обрабатывает админские команды."""
    global waiting_for_vip

    user_id = message.chat.id

    if is_admin(user_id):
        if message.text == Buttons.ADMIN:
            bot.send_message(user_id, "🔐 Админ-панель", reply_markup=admin_menu())

        elif message.text == Buttons.ADMIN_SET_VIP:
            waiting_for_vip = True
            bot.send_message(user_id, "Введите ID пользователя для назначения VIP:")

        elif message.text == Buttons.ADMIN_LIST_VIPS:
            _list_vip_users(message)
        
        elif message.text == Buttons.BACK:
            bot.send_message(user_id, "🔙 Возврат в главное меню", reply_markup=main_menu(is_admin=True))

def admin_input_handler(message):
    """Обрабатывает ввод ID для назначения VIP."""
    global waiting_for_vip

    if waiting_for_vip:
        try:
            vip_id = int(message.text.strip())
            db.set_vip(vip_id)  # Добавляем VIP статус пользователю
            bot.send_message(message.chat.id, f"✅ Пользователю {vip_id} выдан VIP статус.")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Неверный формат ID. Введите число.")
        waiting_for_vip = False
        bot.send_message(message.chat.id, "✅ Вы вернулись в админ-меню", reply_markup=admin_menu())

def _list_vip_users(message):
    """Выводит список всех VIP пользователей."""
    vips = db.get_all_vips()  # Получаем всех VIP из базы
    if not vips:
        bot.send_message(message.chat.id, "Список VIP пользователей пуст.")
    else:
        vip_list = "\n".join([f"• {uid}" for uid in vips])
        bot.send_message(message.chat.id, f"📋 Список VIP:\n{vip_list}")
