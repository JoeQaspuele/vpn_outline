
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
    API_CREATION_FAILED = "🔴 Ошибка API: не удалось создать ключ"
    API_RENAMING_FAILED = "🔴 Ошибка API: не удалось переименовать ключ"
    INVALID_SERVER_ID = "🔴 Неверный ID сервера"
    UNEXPECTED_ERROR = "⚠️ Неожиданная ошибка: {error}"

class Donation:
    MESSAGE = """
    Спасибо за желание поддержать проект!
    Ваша помощь поддерживает работу серверов.
    
    Реквизиты для перевода:
    Карта: 2200 7001 5676 6098
    
    Благодарим за вклад!
    """

class Messages:
    @staticmethod
    def key_info(access_url: str, is_new: bool = True) -> str:
        """Генерирует сообщение о ключе"""
        status = "создан новый" if is_new else "уже существует"
        return f"""
        🛡️ Ваш VPN-ключ ({status}):
        <code>{access_url}</code>
        
        Скопируйте и вставьте его в приложение Outline.
        """
