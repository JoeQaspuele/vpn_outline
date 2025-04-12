class Buttons:
    GET_KEY = "🔑 ПОЛУЧИТЬ КЛЮЧ"
    MY_KEY = "🗝️ МОЙ КЛЮЧ"
    DOWNLOAD = "⬇️ СКАЧАТЬ"
    SUPPORT = "🆘 ПОМОЩЬ"
    DONATE = "❤️ ПОДДЕРЖАТЬ"
    CANCEL = "❌ ОТМЕНА"
    CHECK_TRAFFIC = "📊 ТРАФИК"
    PREMIUM = "💎 PREMIUM"

  # Добавляем, если ещё нет
    BUY_PREMIUM = "💳 Купить PREMIUM"
    BACK = "⬅️ Назад"

    ADMIN = "🛠 Админ-панель"
    MAKE_PREMIUM = "⭐ Сделать PREMIUM"
    VIEW_PREMIUMS = "📋 Список PREMIUM"
    EXTEND_PREMIUM = "⏳ Продлить премиум"

class Messages:
    WELCOME = "Привет! Этот бот позволяет получить VPN без ограничения по скорости. Верни доступ к YouTube, Instagram, Twitter, TikTok."
    HELP_PROMPT = "✍️ Опишите свою проблему.\nСреднее время ответа — 10-60 минут."
    SUCCESS_SENT = "✅ Ваше сообщение отправлено в поддержку!"
    REQUEST_CANCELED = "Вы вернулись в главное меню."
    
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
class PremiumMessages:
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

    PAYMENT_INFO = (
        "💳 Для оплаты переведите <b>120₽</b> на номер карты:\n"
        "<code>1234 5678 9012 3456</code>\n\n"
        "📩 После оплаты отправьте чек или скрин в поддержку.\n"
        "Администратор вручную активирует подписку."
    )
    PREMIUM_WELCOME = (
        "<b>Поздравляем!</b>🎉 \n"
        "Вы успешно стали <b>PREMIUM</b> пользователем.\n"
        "Ваш лимит трафика увеличен до <b>50ГБ</b>!\n"
        "Спасибо за поддержку проекта — это помогает нам держать сервера в строю 💪 \n"
        "Если у вас будут вопросы — просто напишите в поддержку. Хорошего интернета! 🌐 \n"
    )

    TRAFFIC_INFO = (
        "📊 <b>Статистика по вашему ключу (FREE):</b>\n\n"
        "🔋 <b>Осталось:</b> {remaining} ГБ\n"
        "📡 <b>Использовано:</b> {used} ГБ\n"
        "📦 <b>Общий лимит:</b> {limit} ГБ"
    )

    TRAFFIC_INFO_WITH_PREMIUM = (
        "📊 <b>Статистика по вашему ключу (PREMIUM):</b>\n\n"
        "🔋 <b>Осталось:</b> {remaining} ГБ\n"
        "📡 <b>Использовано:</b> {used} ГБ\n"
        "📦 <b>Общий лимит:</b> {limit} ГБ\n"
        "\n💎 <b>PREMIUM-подписка:</b>\n"
        "🕒 Активирована: <b>{since}</b>\n"
        "📅 Действует до: <b>{until}</b>"
    )
    NO_KEY_FOUND = "❗ У вас ещё нет активного ключа. Получите его через главное меню."

class AdminMessages:
    ENTER_USER_ID = "📝 Введите ID пользователя, которому нужно выдать PREMIUM:"
    SUCCESS_SET_PREMIUM = "✅ Пользователь успешно отмечен как PREMIUM."
    INVALID_ID = "❗ Неверный ID. Пожалуйста, введите число."
    ADMIN_MENU = "Вы вернулись назад в меню админа."
