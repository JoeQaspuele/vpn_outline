from telebot import types

def main_menu() -> types.ReplyKeyboardMarkup:
    """Возвращает главное меню с кнопками."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "🔑 Получить ключ VPN",
        "🗝️ Мой ключ VPN",
        "🌐 Скачать клиент VPN", 
        "❓ Помощь",
        "💰 Поддержать VPN"
    ]
    markup.add(*[types.KeyboardButton(btn) for btn in buttons])
    return markup

def support_cancel_markup() -> types.ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены для поддержки."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌ Отменить запрос"))
    return markup
