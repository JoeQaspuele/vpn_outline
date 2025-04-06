
class Buttons:
    GET_KEY = "🔑 Получить ключ VPN"
    MY_KEY = "🗝️ Мой ключ VPN"
    DOWNLOAD = "🌐 Скачать клиент VPN"
    SUPPORT = "❓ Помощь"
    DONATE = "💰 Поддержать VPN"
    CANCEL = "❌ Отменить запрос"

class Messages:
    WELCOME = "Привет! Этот бот позволяет получить VPN без ограничения по скорости. Верни доступ к YouTube, Instagram, Twitter, TikTok."
    HELP_PROMPT = "✍️ Опишите свою проблему.\nСреднее время ответа — 10-60 минут."
    SUCCESS_SENT = "✅ Ваше сообщение отправлено в поддержку!"
    REQUEST_CANCELED = "Запрос в поддержку отменён."
    
    @staticmethod
    def key_info(access_url: str, is_new: bool = True) -> str:
        action = "создан" if is_new else "уже есть"
        return f"""
        Ваш ключ VPN ({action}):
        <code>{access_url}</code>
        """

class Errors:
    KEY_NOT_FOUND = "🔴 Ваш ключ был удалён. Запросите новый."
    DEFAULT = "⚠️ Произошла ошибка. Попробуйте позже."
    API_FAIL = "Ошибка API. Пожалуйста, попробуйте позже."
    UNKNOWN_COMMAND = "⚠️ Неизвестная команда. Используйте кнопки меню."

class Donation:
    MESSAGE = """
    Спасибо за желание поддержать проект!
    Ваша помощь поддерживает работу серверов.
    
    Реквизиты для перевода:
    Карта: 2200 7001 5676 6098
    
    Благодарим за вклад!
    """
