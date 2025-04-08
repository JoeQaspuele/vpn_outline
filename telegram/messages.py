class Buttons:
    GET_KEY = "🔑 Получить ключ VPN"
    MY_KEY = "🗝️ Мой ключ VPN"
    DOWNLOAD = "🌐 Скачать клиент VPN"
    SUPPORT = "❓ Помощь"
    DONATE = "💰 Поддержать VPN"
    CANCEL = "❌ Отменить запрос"

    PREMIUM = "💎 PREMIUM"
    BUY_PREMIUM = "💳 Купить PREMIUM"
    BACK = "⬅️ Назад"

    ADMIN = "🛠 Админ-панель"
    MAKE_PREMIUM = "⭐ Сделать PREMIUM"
    VIEW_PREMIUMS = "📋 Список PREMIUM"


class Messages:
    WELCOME = "Привет! Этот бот позволяет получить VPN без ограничения по скорости. Верни доступ к YouTube, Instagram, Twitter, TikTok."
    HELP_PROMPT = "✍️ Опишите свою проблему.\nСреднее время ответа — 10-60 минут."
    SUCCESS_SENT = "✅ Ваше сообщение отправлено в поддержку!"
    REQUEST_CANCELED = "Вы вернулись в главное меню"
    
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
class Premium:
    DESCRIPTION = (
        "🌟 <b>Подписка PREMIUM</b> 🌟\n\n"
        "Оформите премиум за <b>120₽ в месяц</b> и получите:\n"
        "🔸 <b>50 ГБ трафика</b> каждый месяц\n"
        "🔹 Вместо обычных 15 ГБ\n"
        "🔸 Приоритетную поддержку\n"
        "🔹 Быстрый доступ к серверам\n\n"
        "💳 Оплата производится вручную на номер карты.\n"
        "После оплаты отправьте чек в поддержку, и мы активируем вам PREMIUM!"
    )

    PAYMENT_PLACEHOLDER = (
        "💳 Для оплаты переведите <b>120₽</b> на номер карты:\n"
        "<code>2200 7001 5676 6098</code>\n\n"
        "📩 После оплаты отправьте чек или скрин в поддержку.\n"
        "Администратор вручную активирует подписку."
    )

class AdminMessages:
    ENTER_USER_ID = "📝 Введите ID пользователя, которому нужно выдать PREMIUM:"
    SUCCESS_SET_PREMIUM = "✅ Пользователь успешно отмечен как PREMIUM."
    INVALID_ID = "❗ Неверный ID. Пожалуйста, введите число."
    ADMIN_MENU = "Вы вернулись назад в меню админа."

