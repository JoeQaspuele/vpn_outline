from telebot import types
from telegram.messages import Buttons


def main_menu(is_admin=False) -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(Buttons.GET_KEY),
        types.KeyboardButton(Buttons.MY_KEY),
        types.KeyboardButton(Buttons.DOWNLOAD),
        types.KeyboardButton(Buttons.SUPPORT),
        types.KeyboardButton(Buttons.DONATE),
        types.KeyboardButton(Buttons.PREMIUM)
    )
    
    # Добавляем кнопку администратора только если пользователь администратор
    if is_admin:
        markup.add(types.KeyboardButton(Buttons.ADMIN))
    
    return markup



def support_cancel_markup() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(Buttons.CANCEL))
    return markup


def premium_menu() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(Buttons.BUY_PREMIUM),
        types.KeyboardButton(Buttons.BACK)
    )
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton(Buttons.ADMIN_SET_VIP))  # Убедись, что используешь types.KeyboardButton
    markup.row(types.KeyboardButton(Buttons.ADMIN_LIST_VIPS))  # Так же для других кнопок
    markup.row(types.KeyboardButton(Buttons.BACK))
    return markup

