import telebot
from telebot import types
from settings import (
    BOT_API_TOKEN,
    DEFAULT_SERVER_ID,
    BLACKLISTED_CHAT_IDS,
    WHITELISTED_CHAT_IDS,
    ENABLE_BLACKLIST,
    ENABLE_WHITELIST,
    ADMIN_IDS
)
from telegram.messages import Messages, Errors, Buttons, Donation, PremiumMessages, AdminMessages
from telegram.keyboards import main_menu, cancel_or_back_markup, premium_menu, admin_menu
import telegram.monitoring as monitoring
import outline.api as outline
from helpers.exceptions import KeyCreationError, KeyRenamingError, InvalidServerIdError
import telegram.message_formatter as f
from helpers.aliases import ServerId
import db
from datetime import datetime, timedelta

assert BOT_API_TOKEN is not None
bot = telebot.TeleBot(BOT_API_TOKEN, parse_mode='HTML')
admin_states = {}  # user_id -> "awaiting_premium_id"
user_states = {}  # user_id: str
DEFAULT_DATA_LIMIT_GB = 15  # Установленный лимит траффика
PREMIUM_DATA_LIMIT_GB = 50  # Трафик для PREMIUM пользователей

# --- ACCESS CONTROL DECORATOR ---


def authorize(func):
    def wrapper(message):
        chat_id = message.chat.id
        if ENABLE_BLACKLIST and str(chat_id) in BLACKLISTED_CHAT_IDS:
            monitoring.report_blacklist_attempt(
                message.from_user.username, chat_id)
            return
        if ENABLE_WHITELIST and str(chat_id) not in WHITELISTED_CHAT_IDS:
            monitoring.report_not_in_whitelist(
                message.from_user.username, chat_id)
            return
        return func(message)
    return wrapper

# --- HANDLERS ---
@bot.message_handler(commands=['status'])
@authorize
def send_status(message):
    monitoring.send_api_status()

# HANDLER /START
@bot.message_handler(commands=['start'])
@authorize
def send_welcome(message):
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    bot.send_message(
        message.chat.id,
        Messages.WELCOME,
        reply_markup=main_menu(is_admin),
        parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == Buttons.CHECK_TRAFFIC)
def handle_check_traffic(message):
    user_id = message.chat.id
    key_id = db.get_user_key(user_id)

    if not key_id:
        bot.send_message(user_id, PremiumMessages.NO_KEY_FOUND)
        return

    try:
        user_data = db.get_user_data(user_id)
        print(f"[DEBUG] user_data: {user_data}")

        limit = user_data.get("limit", 15)
        used_monthly = user_data.get("monthly_gb", 0)
        total_used_bytes = user_data.get("total_bytes", 0)

        remaining = max(0, round(limit - used_monthly, 2))
        used = round(used_monthly, 2)
        total_used = round(total_used_bytes / 1024**3, 2)  # байты → ГБ

        # Формируем сообщение
        if user_data.get("isPremium"):
            since = user_data.get("premium_since")
            until = user_data.get("premium_until")

            # Даты для текста
            since_text = datetime.fromisoformat(since).strftime('%d.%m.%Y') if since else "неизвестно"
            until_text = datetime.fromisoformat(until).strftime('%d.%m.%Y') if until else "неизвестно"

            bot.send_message(
                user_id,
                PremiumMessages.TRAFFIC_INFO_WITH_PREMIUM.format(
                    remaining=remaining,
                    used=used,
                    limit=limit,
                    total=total_used,
                    since=since_text,
                    until=until_text
                ),
                parse_mode="HTML"
            )
        else:
            bot.send_message(
                user_id,
                PremiumMessages.TRAFFIC_INFO.format(
                    remaining=remaining,
                    used=used,
                    limit=limit,
                    total=total_used
                ),
                parse_mode="HTML"
            )

    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка при получении трафика: {e}")
        print(f"[ERROR] handle_check_traffic: {e}")


# HANDLER - PREMIUM Кнопка
@bot.message_handler(func=lambda message: message.text == Buttons.PREMIUM)
def handle_premium(message):
    user_id = message.chat.id
    user_states[user_id] = "premium_menu"

    bot.send_message(
        user_id,
        PremiumMessages.DESCRIPTION,
        reply_markup=premium_menu(),
        parse_mode="HTML"
    )


# HANDLER - BUTTON_PAY_PREMIUM
@bot.message_handler(func=lambda message: message.text == Buttons.BUY_PREMIUM)
def handle_buy_premium(message):
      bot.send_message(
            message.chat.id,
            PremiumMessages.PAYMENT_INFO,
            reply_markup=premium_menu(),
            parse_mode="HTML"
        )

# HANDLER - ADMIN - PANEL
@bot.message_handler(func=lambda message: message.text == Buttons.ADMIN)
def handle_admin_panel(message):
    user_id = message.chat.id
    if user_id in ADMIN_IDS:
        user_states[user_id] = "admin_menu"
        bot.send_message(user_id, "🔐 Админ-панель:", reply_markup=admin_menu())

        
# HANDLER - MAKE_PREMIUM
@bot.message_handler(func=lambda message: message.text == Buttons.MAKE_PREMIUM)
def handle_make_premium(message):
    admin_states[message.chat.id] = "awaiting_premium_id"
    bot.send_message(
        message.chat.id,
        AdminMessages.ENTER_USER_ID,
        reply_markup=cancel_or_back_markup(for_admin=True)
    )
# HANDLER - MAKE_PREMIUM2
@bot.message_handler(func=lambda message: admin_states.get(message.chat.id) == "awaiting_premium_id")
def process_premium_user_id(message):
    if message.text == Buttons.BACK:
        admin_states.pop(message.chat.id, None)
        bot.send_message(
            message.chat.id,
            Messages.REQUEST_CANCELED,
            reply_markup=admin_menu()
        )
        return

    try:
        user_id_str, days_str = message.text.strip().split()
        user_id = int(user_id_str)
        days = int(days_str)

        if days <= 0:
            raise ValueError("Количество дней должно быть положительным")

        # Устанавливаем премиум и получаем лимит
        new_limit_gb = db.set_premium(user_id, days)

        # Устанавливаем лимит в Outline API
        key_id = db.get_user_key(user_id)
        if key_id:
            from settings import DEFAULT_SERVER_ID
            from outline.api import _set_access_key_data_limit

            limit_bytes = int(new_limit_gb * 1024 ** 3)
            _set_access_key_data_limit(key_id, limit_bytes, DEFAULT_SERVER_ID)

        bot.send_message(
            message.chat.id,
            f"✅ Пользователь {user_id} получил PREMIUM на {days} дней.\n"
            f"Установленный лимит: {new_limit_gb:.2f} ГБ",
            reply_markup=admin_menu()
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Введите ID и количество дней через пробел (например: <code>123456 30</code>)",
            parse_mode="HTML",
            reply_markup=cancel_or_back_markup(for_admin=True)
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⚠️ Ошибка: {e}",
            reply_markup=admin_menu()
        )
    finally:
        admin_states.pop(message.chat.id, None)

# HANDLER ADD DAYS PREMIUM (продолжение)
@bot.message_handler(func=lambda message: admin_states.get(message.chat.id) == "awaiting_extend_data")
def process_extend_premium(message):
    if message.text == Buttons.BACK:
        admin_states.pop(message.chat.id, None)
        bot.send_message(
            message.chat.id,
            Messages.REQUEST_CANCELED,
            reply_markup=admin_menu()
        )
        return

    try:
        user_id_str, days_str = message.text.strip().split()
        user_id = int(user_id_str)
        days = int(days_str)

        if days <= 0:
            raise ValueError("Количество дней должно быть положительным")

        # Продлеваем премиум и получаем добавочный лимит
        added_limit_gb = db.extend_premium(user_id, days)

        # Обновляем лимит в Outline API
        key_id = db.get_user_key(user_id)
        if key_id:
            from settings import DEFAULT_SERVER_ID
            from outline.api import _set_access_key_data_limit

            # Получаем полный лимит после обновления из БД
            updated = db.get_user_data(user_id)
            new_total_limit = updated['limit']
            _set_access_key_data_limit(key_id, int(new_total_limit * 1024**3), DEFAULT_SERVER_ID)

        bot.send_message(
            message.chat.id,
            f"✅ Продлил PREMIUM на {days} дней для пользователя {user_id}\n"
            f"Добавлено: {added_limit_gb} ГБ трафика\n"
            f"📅 Новая дата окончания: {updated['premium_until'][:10]}",
            reply_markup=admin_menu()
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⚠️ Ошибка: {str(e)}",
            reply_markup=admin_menu()
        )
    finally:
        admin_states.pop(message.chat.id, None)

@bot.message_handler(func=lambda message: message.text == Buttons.EXTEND_PREMIUM)
def handle_extend_premium(message):
    admin_states[message.chat.id] = "awaiting_extend_data"
    bot.send_message(
        message.chat.id,
        "Введите ID пользователя и количество дней через пробел (например: <code>123456 10</code>)",
        parse_mode="HTML",
        reply_markup=cancel_or_back_markup(for_admin=True)
    )


# HANDLER - ALL_PREMIUM_USER
@bot.message_handler(func=lambda message: message.text == Buttons.VIEW_PREMIUMS and message.chat.id in ADMIN_IDS)
def handle_view_premiums(message):
    premium_users = db.get_all_premium_users()  # Предполагаемая функция
    if premium_users:
        user_list = "\n".join(
            [f"👤 ID: {user['user_id']}" for user in premium_users])
        bot.send_message(
            message.chat.id, f"Список PREMIUM-пользователей:\n\n{user_list}", reply_markup=admin_menu())
    else:
        bot.send_message(
            message.chat.id, "❗ Пока нет PREMIUM-пользователей.", reply_markup=admin_menu())

@bot.message_handler(commands=['s'])
@authorize
def send_s_list(message):
    bot.send_message(message.chat.id, f.make_s_list())

# HANDLER - SUPPORT_MENU
@bot.message_handler(content_types=['text'])
@authorize
def answer(message):
    text = message.text.strip()
    chat_id = message.chat.id

    # === Режим поддержки ===
    if user_states.get(chat_id) == "support":
        if text == Buttons.CANCEL:
            user_states.pop(chat_id, None)
            bot.send_message(chat_id, Messages.REQUEST_CANCELED, reply_markup=main_menu())
        else:
            send_to_support(message)
        return

    # === Режим установки премиума (теперь через admin_states) ===
    if admin_states.get(chat_id) == "awaiting_premium_id":
        if text == Buttons.BACK:
            admin_states.pop(chat_id, None)
            bot.send_message(chat_id, "Вы вернулись в админ меню.", reply_markup=admin_menu())
            return
        try:
            user_id = int(text)
            db.set_premium(user_id)
            admin_states.pop(chat_id, None)
            bot.send_message(chat_id, "✅ Пользователь успешно отмечен как PREMIUM.", reply_markup=admin_menu())
        except ValueError:
            bot.send_message(chat_id, "❌ Пожалуйста, введите корректный ID или нажмите Назад.")
        return

    # === Остальные действия ===
    if text == Buttons.PREMIUM:
        handle_premium(message)
        return

    if text == Buttons.ADMIN:
        handle_admin_panel(message)
        return

    command_handlers = {
        Buttons.GET_KEY: lambda msg: _make_new_key(msg, DEFAULT_SERVER_ID, _form_key_name(msg)),
        Buttons.MY_KEY: _send_existing_key,
        Buttons.DOWNLOAD: lambda msg: bot.send_message(msg.chat.id, f.make_download_message(), disable_web_page_preview=True),
        Buttons.SUPPORT: set_help_mode,
        Buttons.DONATE: send_support_message,
    }

    if text.startswith("/newkey"):
        server_id, key_name = _parse_the_command(message)
        _make_new_key(message, server_id, key_name)
    elif text in command_handlers:
        command_handlers[text](message)
    else:
       is_admin = chat_id in ADMIN_IDS
       bot.send_message(chat_id, Errors.UNKNOWN_COMMAND, reply_markup=main_menu(is_admin))
         


# HANDLER - МЕНЮ ПОМОЩь
@bot.message_handler(commands=['help'])
@authorize
def send_help(message):
    user_id = message.chat.id
    is_admin = user_id in ADMIN_IDS
    user_states[user_id] = "support_mode"

    bot.send_message(
        message.chat.id,
        Messages.HELP_PROMPT,
        reply_markup=cancel_or_back_markup(for_admin=is_admin)
    )

# HANDLER - BUTTON_BACK
@bot.message_handler(func=lambda message: message.text == Buttons.BACK)
def handle_back(message):
    user_id = message.chat.id
    is_admin = user_id in ADMIN_IDS

    # Удаляем состояния
    user_states.pop(user_id, None)
    admin_states.pop(user_id, None)

    # Возврат в главное меню
    bot.send_message(
        user_id,
        Messages.REQUEST_CANCELED,
        reply_markup=main_menu(is_admin)
    )

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "support_mode", content_types=['text', 'photo', 'document', 'voice', 'sticker'])
def handle_support_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username
    is_admin = user_id in ADMIN_IDS

    user_link = (
        f'<a href="https://t.me/{username}">пользователя</a>'
        if username
        else f'<a href="tg://user?id={user_id}">пользователя</a>'
    )

    try:
        if message.text:
            support_text = f"📩 Новый запрос от {user_link}:\n\n{message.text}"
            bot.send_message(245413138, support_text, parse_mode="HTML")

        elif message.photo:
            photo = message.photo[-1]
            caption = f"📸 Фото от {user_link}"
            if message.caption:
                caption += f"\n\n{message.caption}"
            bot.send_photo(245413138, photo.file_id, caption=caption, parse_mode="HTML")

        elif message.document:
            caption = f"📁 Файл от {user_link}"
            if message.caption:
                caption += f"\n\n{message.caption}"
            bot.send_document(245413138, message.document.file_id, caption=caption, parse_mode="HTML")

        elif message.voice:
            bot.send_voice(245413138, message.voice.file_id, caption=f"🎤 Голосовое от {user_link}", parse_mode="HTML")

        elif message.sticker:
            bot.send_message(245413138, f"🛑 Стикер от {user_link} (ID: {message.sticker.file_id})")

        # Очищаем состояние после обработки
        user_states.pop(chat_id, None)

        bot.send_message(
            chat_id,
            Messages.SUCCESS_SENT,
            reply_markup=main_menu(is_admin)
        )

    except Exception as e:
        user_states.pop(chat_id, None)
        bot.send_message(
            chat_id,
            Errors.DEFAULT,
            reply_markup=main_menu(is_admin)
        )
        monitoring.send_error(str(e), username or str(user_id))


# HANDLER - SUPPORT MEDIA
@bot.message_handler(content_types=['photo', 'document', 'voice', 'sticker'])
def handle_support_media(message):
    if user_states.get(message.chat.id) == "support":
        send_to_support(message)

# ------ UTIL def ------- #
def set_help_mode(message):
    """Активирует режим обращения в поддержку"""
    user_id = message.chat.id
    is_admin = user_id in ADMIN_IDS
    user_states[user_id] = "support_mode"

    bot.send_message(
        user_id,
        Messages.HELP_PROMPT,
        reply_markup=cancel_or_back_markup(for_admin=is_admin)
    )


# --- CORE FUNCTIONS ---
def _make_new_key(message, server_id: ServerId, key_name: str):
    user_id = message.chat.id
    old_key_id = db.get_user_key(user_id)

    try:
        # Инициализируем пользователя если его нет
        if not db.get_user_data(user_id):
            db.init_user(user_id)

        if old_key_id:
            if db.is_key_deleted(old_key_id):
                db.remove_user_key(user_id)
                key = outline.get_new_key(key_name, server_id, DEFAULT_DATA_LIMIT_GB)
                db.save_user_key(user_id, key.kid)
                db.update_user_limits(user_id, used=0, limit=DEFAULT_DATA_LIMIT_GB)
                _send_key(message, key, server_id)
            else:
                try:
                    key = outline.get_key_by_id(old_key_id, server_id)
                    bot.send_message(message.chat.id, Messages.key_info(key.access_url, is_new=False), parse_mode="HTML")
                except KeyError:
                    key = outline.get_new_key(key_name, server_id, DEFAULT_DATA_LIMIT_GB)
                    db.save_user_key(user_id, key.kid)
                    db.update_user_limits(user_id, used=0, limit=DEFAULT_DATA_LIMIT_GB)
                    _send_key(message, key, server_id)
        else:
            key = outline.get_new_key(key_name, server_id, DEFAULT_DATA_LIMIT_GB)
            db.save_user_key(user_id, key.kid)
            db.update_user_limits(user_id, used=0, limit=DEFAULT_DATA_LIMIT_GB)
            _send_key(message, key, server_id)

    except Exception as e:
        _send_error_message(message, Errors.API_FAIL)
        logging.error(f"Key creation error: {str(e)}")


def _send_existing_key(message):
    user_id = message.chat.id
    key_name = db.get_user_key(user_id)

    if not key_name:
        bot.send_message(user_id, "У вас ещё нет ключа.")
        return

    try:
        key = outline.get_key_by_id(key_name, DEFAULT_SERVER_ID)
        if key:
            access_url = key.access_url
            bot.send_message(
                user_id,
                f"Ваш ключ:\n\n<code>{access_url}</code>\n\nСкопируйте и вставьте его в приложение Outline. \n На бесплатном тарифе у вас 15Гб без ограничесний по скорости")
        else:
            bot.send_message(
                user_id,
                "Ваш ключ был удалён. Попробуйте получить новый или обратитесь в поддержку.")
    except KeyError as e:  # ловим ошибку, если ключ не найден
        db.mark_key_as_deleted(user_id)  # Помечаем ключ как удалённый
        bot.send_message(
            user_id,
            "Ваш ключ был удалён. Попробуйте получить новый или обратитесь в поддержку.")
    except Exception as e:
        _send_error_message(message, f"Ошибка при получении ключа: {e}")


def _send_key(message, key, server_id):
    text = f.make_message_for_new_key("outline", key.access_url, server_id)
    bot.send_message(message.chat.id, text)
    monitoring.new_key_created(key.kid, key.name, message.chat.id, server_id)


def _send_error_message(message, error_message):
    bot.send_message(message.chat.id, error_message)
    monitoring.send_error(
        error_message,
        message.from_user.username or "нет username"
    )


def send_to_support(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS

    username = message.from_user.username
    user_link = (
        f'<a href="https://t.me/{username}">пользователя</a>'
        if username
        else f'<a href="tg://user?id={user_id}">пользователя</a>'
    )

    try:
        if message.text:
            support_text = f"📩 Новый запрос от {user_link}:\n\n{message.text}"
            bot.send_message(245413138, support_text, parse_mode="HTML")

        elif message.photo:
            photo = message.photo[-1]
            caption = f"📸 Фото от {user_link}"
            if message.caption:
                caption += f"\n\n{message.caption}"
            bot.send_photo(245413138, photo.file_id, caption=caption, parse_mode="HTML")

        elif message.document:
            caption = f"📁 Файл от {user_link}"
            if message.caption:
                caption += f"\n\n{message.caption}"
            bot.send_document(245413138, message.document.file_id, caption=caption, parse_mode="HTML")

        elif message.voice:
            bot.send_voice(245413138, message.voice.file_id, caption=f"🎤 Голосовое от {user_link}", parse_mode="HTML")

        elif message.sticker:
            bot.send_message(245413138, f"🛑 Стикер от {user_link} (ID: {message.sticker.file_id})")

        # После обработки — очищаем состояние
        user_states.pop(chat_id, None)

        bot.send_message(
            chat_id,
            Messages.SUCCESS_SENT,
            reply_markup=main_menu(is_admin)
        )

    except Exception as e:
        user_states.pop(chat_id, None)
        bot.send_message(
            chat_id,
            Errors.DEFAULT,
            reply_markup=main_menu(is_admin)
        )
        monitoring.send_error(str(e), username or str(user_id))


def send_support_message(message):
    bot.send_message(
        message.chat.id,
        Donation.MESSAGE,
        parse_mode="HTML"
    )

def _parse_the_command(message) -> list:
    parts = message.text.strip().split()
    server_id = parts[1] if len(parts) > 1 else DEFAULT_SERVER_ID
    key_name = ''.join(parts[2:]) if len(
        parts) > 2 else _form_key_name(message)

    # Валидация server_id
    if not server_id.isdigit():
        raise InvalidServerIdError("Server ID must be numeric")

    return [server_id, key_name]

def _form_key_name(message) -> str:
    username = message.from_user.username or "no_username"
    return f"{message.chat.id}_{username}"

def start_telegram_server():
    db.init_db()
    db.check_premium_expiration()  # 💥 Проверка перед запуском
    monitoring.send_start_message()
    bot.infinity_polling()
