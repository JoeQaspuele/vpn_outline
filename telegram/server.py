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

# МЕНЮ ПОМОЩь
@bot.message_handler(commands=['help'])
@authorize
def send_help(message):
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    user_states[message.chat.id] = "support"

    bot.send_message(
        message.chat.id,
        Messages.HELP_PROMPT,
        reply_markup=cancel_or_back_markup(for_admin=is_admin)
    )

#Хэндлер кнопки проверки трафика
@bot.message_handler(func=lambda message: message.text == Buttons.CHECK_TRAFFIC)
def handle_check_traffic(message):
    user_id = message.chat.id
    key_id = db.get_user_key(user_id)

    if not key_id:
        bot.send_message(user_id, PremiumMessages.NO_KEY_FOUND)
        return

    try:
        # Получаем все данные за один запрос
        user_data = db.get_user_data(user_id)
        key = outline.get_key_by_id(key_id, DEFAULT_SERVER_ID)

        # Текущий трафик из Outline (в байтах)
        total_used_bytes = key.used if key.used else 0
        total_used_gb = round(total_used_bytes / 1024**3, 2)

        # Данные о сбросе
        start_bytes, start_date_str = db.get_traffic_reset_info(user_id)
        start_bytes = start_bytes or 0  # Защита от None

        # Проверяем, нужно ли обновить точку отсчёта
        now = datetime.now()
        if not start_date_str:
            # Первый запрос - устанавливаем точку отсчёта
            db.set_traffic_reset_info(user_id, total_used_bytes)
            used_this_month_gb = 0
        else:
            start_date = datetime.fromisoformat(start_date_str)
            if start_date.month != now.month or start_date.year != now.year:
                # Новый месяц - обновляем точку отсчёта
                db.set_traffic_reset_info(user_id, total_used_bytes)
                used_this_month_gb = 0
            else:
                # Трафик за текущий месяц = разница с точкой отсчёта
                used_this_month_bytes = max(0, total_used_bytes - start_bytes)
                used_this_month_gb = round(used_this_month_bytes / 1024**3, 2)

        # Рассчитываем оставшийся трафик
        current_limit_gb = user_data.get('limit', 15)
        remaining_gb = max(0, current_limit_gb - used_this_month_gb)

        # Формируем сообщение
        message_text = (
            "📊 <b>Статистика трафика:</b>\n\n"
            f"🔋 <b>Осталось в этом месяце:</b> {remaining_gb} ГБ\n"
            f"📡 <b>Использовано в этом месяце:</b> {used_this_month_gb} ГБ\n"
            f"📦 <b>Лимит в этом месяце:</b> {current_limit_gb} ГБ\n"
            f"🌐 <b>Всего использовано за всё время:</b> {total_used_gb} ГБ"
        )

        bot.send_message(user_id, message_text, parse_mode="HTML")

    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка при получении трафика: {e}")
        print(f"Error in handle_check_traffic: {e}")

# ADMIN - PANEL
@bot.message_handler(func=lambda message: message.text == Buttons.ADMIN)
def handle_admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        user_states[message.chat.id] = "admin_menu"  # <-- Добавляем это
        bot.send_message(message.chat.id, "🔐 Админ-панель:",
                         reply_markup=admin_menu())


# PREMIUM Кнопка
@bot.message_handler(func=lambda message: message.text == Buttons.PREMIUM)
def handle_premium(message):
    user_states[message.chat.id] = "premium_menu"
    bot.send_message(
        message.chat.id,
        PremiumMessages.DESCRIPTION,
        reply_markup=premium_menu(),
        parse_mode="HTML"
    )

# Обработка кнопки "Сделать PREMIUM"
@bot.message_handler(func=lambda message: message.text == Buttons.MAKE_PREMIUM)
def handle_make_premium(message):
    admin_states[message.chat.id] = "awaiting_premium_id"
    bot.send_message(
        message.chat.id,
        AdminMessages.ENTER_USER_ID,
        reply_markup=cancel_or_back_markup(for_admin=True)
    )

@bot.message_handler(func=lambda message: admin_states.get(message.chat.id) == "awaiting_premium_id")
def process_premium_user_id(message):
    if message.text == Buttons.BACK:
         admin_states.pop(message.chat.id, None)
         bot.send_message(
         message.chat.id,
         Messages.REQUEST_CANCELED,
         reply_markup=main_menu(is_admin=True))
         return

    try:
        user_id = int(message.text)
        db.set_premium(user_id)

        key_id = db.get_user_key(user_id)
        if key_id:
            limit_in_bytes = PREMIUM_DATA_LIMIT_GB * 1024**3
            outline._set_access_key_data_limit(
                key_id=key_id,
                limit_in_bytes=limit_in_bytes,
                server_id=DEFAULT_SERVER_ID
            )

        bot.send_message(
            user_id,
            PremiumMessages.PREMIUM_WELCOME,
            parse_mode="HTML"
        )

        admin_states.pop(message.chat.id, None)
        bot.send_message(
            message.chat.id,
            AdminMessages.SUCCESS_SET_PREMIUM,
            reply_markup=admin_menu()
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            AdminMessages.INVALID_ID,
            reply_markup=cancel_or_back_markup(for_admin=True)
        )

@bot.message_handler(func=lambda message: message.text == Buttons.EXTEND_PREMIUM)
def handle_extend_premium(message):
    admin_states[message.chat.id] = "awaiting_extend_data"
    bot.send_message(
        message.chat.id,
        "Введите ID пользователя и количество дней через пробел (например: <code>123456 15</code>)",
        parse_mode="HTML",
        reply_markup=cancel_or_back_markup(for_admin=True)
    )

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
        user_id, days = map(int, message.text.split())
        if days <= 0:
            raise ValueError
        
        # Получаем текущую дату премиума
        current_date = db.get_premium_date(user_id) or datetime.utcnow().isoformat()
        
        # Рассчитываем новую дату окончания
        new_end_date = (datetime.fromisoformat(current_date) + timedelta(days=days)).isoformat()
        
        # Обновляем в БД
        db.extend_premium(user_id, new_end_date)
        
        # Обновляем лимит трафика
        key_id = db.get_user_key(user_id)
        if key_id:
            daily_limit_gb = round(PREMIUM_DATA_LIMIT_GB / 30 * days, 2)
            new_limit_bytes = int(daily_limit_gb * (1024 ** 3))
            outline._set_access_key_data_limit(key_id, new_limit_bytes, DEFAULT_SERVER_ID)
        
        bot.send_message(
            message.chat.id,
            f"✅ Премиум для пользователя {user_id} продлён на {days} дней\n"
            f"Новый лимит трафика: {daily_limit_gb:.2f} ГБ",
            reply_markup=admin_menu()
        )
        
    except (ValueError, IndexError):
        bot.send_message(
            message.chat.id,
            "❌ Неверный формат. Введите ID и дни через пробел (например: <code>123456 15</code>)",
            parse_mode="HTML",
            reply_markup=cancel_or_back_markup(for_admin=True)
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⚠️ Ошибка: {str(e)}",
            reply_markup=admin_menu()
        )
    finally:
        admin_states.pop(message.chat.id, None)

# КНОПКА ПОСМОТРЕТЬ PREMIUM ПОЛЬЗОВАТЕЛЕЙ
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


@bot.message_handler(func=lambda message: message.text == Buttons.BACK)
def handle_back(message):
    user_id = message.chat.id
    state = user_states.get(user_id)

    if state == "premium_menu":
        user_states.pop(user_id, None)
        bot.send_message(
            user_id,
            Messages.REQUEST_CANCELED,
            reply_markup=main_menu(user_id in ADMIN_IDS)
        )

    elif state == "support_mode":
        user_states.pop(user_id, None)
        bot.send_message(
            user_id,
            Messages.REQUEST_CANCELED,
            reply_markup=main_menu(user_id in ADMIN_IDS)
        )

    elif admin_states.get(user_id) == "awaiting_premium_id":
        admin_states.pop(user_id, None)
        bot.send_message(
            user_id,
            "❌ Действие отменено.",
            reply_markup=admin_menu()
        )

    elif state == "admin_menu":
        user_states.pop(user_id, None)
        bot.send_message(
            user_id,
            Messages.REQUEST_CANCELED,
            reply_markup=main_menu(user_id in ADMIN_IDS)
        )

    else:
        bot.send_message(
            user_id,
            Messages.REQUEST_CANCELED,
            reply_markup=main_menu(user_id in ADMIN_IDS)
        )


# КНОПКА КУПИТЬ ПРЕМИУМ
@bot.message_handler(func=lambda message: message.text == Buttons.BUY_PREMIUM)
def handle_buy_premium(message):
      bot.send_message(
            message.chat.id,
            PremiumMessages.PAYMENT_INFO,
            reply_markup=premium_menu(),
            parse_mode="HTML"
        )

@bot.message_handler(commands=['s'])
@authorize
def send_s_list(message):
    bot.send_message(message.chat.id, f.make_s_list())

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
        bot.send_message(chat_id, Errors.UNKNOWN_COMMAND, reply_markup=main_menu())

@bot.message_handler(content_types=['photo', 'document', 'voice', 'sticker'])
def handle_support_media(message):
    if user_states.get(message.chat.id) == "support":
        send_to_support(message)


def set_help_mode(message):
    """Активирует режим обращения в поддержку"""
    user_states[message.chat.id] = "support"

    bot.send_message(
        message.chat.id,
        Messages.HELP_PROMPT,
        reply_markup=cancel_or_back_markup(for_admin=False)
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
