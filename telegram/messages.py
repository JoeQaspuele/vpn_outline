
# Главное меню
WELCOME_MESSAGE = """
Привет! Этот бот позволяет получить VPN без ограничения по скорости. 
Верни доступ к YouTube, Instagram, Twitter, TikTok.
"""

HELP_PROMPT = """
✍️ Опишите свою проблему. 
Среднее время ответа — 10-60 минут.
Для отмены нажмите кнопку ниже.
"""

SUPPORT_SUCCESS = "✅ Ваше сообщение отправлено в поддержку!"
SUPPORT_CANCEL = "Запрос в поддержку отменён."

# Ключи VPN
KEY_RECEIVED = """
Ваш ключ VPN:
<code>{access_url}</code>

Скопируйте и вставьте его в приложение Outline.
"""

KEY_EXISTS = """
У вас уже есть ключ:
<code>{access_url}</code>
"""
# Текст с кнопки поддержки 
HELP_PROJECT = """
"Спасибо за желание поддержать мой проект!\n"
"Ваша поддержка поможет поддерживать в работе сервер.\n\n"
"Вы можете перевести средства на карту:\n"
"2200 7001 5676 6098\n\n"
"Спасибо за вашу помощь и поддержку!")
"""

#Кнопки
BUTTONS = {
    "get_key": "🔑 Получить ключ VPN",
    "my_key": "🗝️ Мой ключ VPN",
    "support": "❓ Помощь"
}

# Ошибки
ERROR_KEY_NOT_FOUND = "🔴 Ваш ключ был удалён. Запросите новый."
ERROR_DEFAULT = "⚠️ Произошла ошибка. Попробуйте позже."

# messages.py
def key_message(access_url: str, server_name: str) -> str:
    return f"""
    🛡️ <b>Ваш VPN-ключ для {server_name}:</b>
    <code>{access_url}</code>
    """
