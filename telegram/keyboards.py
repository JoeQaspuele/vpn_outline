from telebot import types
from telegram.messages import Buttons


def main_menu() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(Buttons.GET_KEY),
        types.KeyboardButton(Buttons.MY_KEY),
        types.KeyboardButton(Buttons.DOWNLOAD),
        types.KeyboardButton(Buttons.SUPPORT),
        types.KeyboardButton(Buttons.DONATE),
        types.KeyboardButton(Buttons.PREMIUM)
    )
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
    markup.row(Buttons.ADMIN_SET_VIP)
    markup.row(Buttons.ADMIN_LIST_VIPS)
    markup.row(Buttons.BACK)
    return markup
