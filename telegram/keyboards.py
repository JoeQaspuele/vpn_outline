from telebot import types
from telegram.messages import Buttons

def main_menu() -> types.ReplyKeyboardMarkup:
    """Главное меню с кнопками"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(Buttons.GET_KEY),
        types.KeyboardButton(Buttons.MY_KEY),
        types.KeyboardButton(Buttons.DOWNLOAD),
        types.KeyboardButton(Buttons.SUPPORT),
        types.KeyboardButton(Buttons.DONATE)
    )
    return markup

def support_cancel_markup() -> types.ReplyKeyboardMarkup:
    """Клавиатура для режима поддержки"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(Buttons.CANCEL))
    return markup

def admin_menu() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(Buttons.MAKE_VIP),
        types.KeyboardButton(Buttons.INCREASE_LIMIT),
        types.KeyboardButton(Buttons.REVOKE_KEY),
        types.KeyboardButton(Buttons.BACK_TO_MAIN)
    )
    return markup
