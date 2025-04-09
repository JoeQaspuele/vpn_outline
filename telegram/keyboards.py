from telebot import types
from telegram.messages import Buttons

def main_menu() -> types.ReplyKeyboardMarkup:
    """Главное меню с кнопками"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(Buttons.GET_KEY),
        types.KeyboardButton(Buttons.MY_KEY),
        types.KeyboardButton(Buttons.DOWNLOAD),
        types.KeyboardButton(Buttons.PREMIUM),
        types.KeyboardButton(Buttons.CHECK_TRAFFIC),
        types.KeyboardButton(Buttons.SUPPORT),
        types.KeyboardButton(Buttons.DONATE)
    if is_admin:
        markup.add(types.KeyboardButton(Buttons.ADMIN))
    return markup

def cancel_or_back_markup(for_admin=False) -> types.ReplyKeyboardMarkup:
    """Клавиатура с кнопкой 'Назад' для админа или 'Отменить' для пользователя"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = Buttons.BACK if for_admin else Buttons.CANCEL
    markup.add(types.KeyboardButton(button))
    return markup

def premium_menu() -> types.ReplyKeyboardMarkup:
    """Меню PREMIUM с кнопками"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(Buttons.BUY_PREMIUM),
        types.KeyboardButton(Buttons.BACK)
    )
    return markup

def admin_menu() -> types.ReplyKeyboardMarkup:
    """Клавиатура администратора"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(Buttons.MAKE_PREMIUM),
        types.KeyboardButton(Buttons.VIEW_PREMIUMS),
        types.KeyboardButton(Buttons.BACK)
    )
    return markup


