import telebot
from telebot import types
from telegram.keyboards import main_menu, support_cancel_markup 
    BOT_API_TOKEN,
    DEFAULT_SERVER_ID,
    BLACKLISTED_CHAT_IDS,
    WHITELISTED_CHAT_IDS,
    ENABLE_BLACKLIST,
    ENABLE_WHITELIST
)
from telegram.messages import Messages, Errors, Buttons, Donation
import telegram.monitoring as monitoring
import outline.api as outline
from helpers.exceptions import KeyCreationError, KeyRenamingError, InvalidServerIdError
import telegram.message_formatter as f
from helpers.aliases import ServerId
import db

assert BOT_API_TOKEN is not None
bot = telebot.TeleBot(BOT_API_TOKEN, parse_mode='HTML')

waiting_for_support = False
# Константа для лимита трафика (50 ГБ)
DEFAULT_DATA_LIMIT_GB = 50 # Установленный лимит траффика

# --- ACCESS CONTROL DECORATOR ---
def authorize(func):
    def wrapper(message):
        chat_id = message.chat.id
        if ENABLE_BLACKLIST and str(chat_id) in BLACKLISTED_CHAT_IDS:
            monitoring.report_blacklist_attempt(message.from_user.username, chat_id)
            return
        if ENABLE_WHITELIST and str(chat_id) not in WHITELISTED_CHAT_IDS:
            monitoring.report_not_in_whitelist(message.from_user.username, chat_id)
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
    bot.send_message(message.chat.id, Messages.WELCOME, reply_markup=main_menu())

@bot.message_handler(commands=['help'])
@authorize
def send_help(message):
    global waiting_for_support
    waiting_for_support = True
    bot.send_message(
        message.chat.id,
        Messages.HELP_PROMPT,
        reply_markup=support_cancel_markup()
    )

@bot.message_handler(commands=['servers'])
@authorize
def send_servers_list(message):
    bot.send_message(message.chat.id, f.make_servers_list())

@bot.message_handler(content_types=['text'])
@authorize
def answer(message):
    global waiting_for_support
    
    text = message.text.strip()
    
    # Режим ожидания сообщения в поддержку
    if waiting_for_support:
        if text == Buttons.CANCEL:
            waiting_for_support = False
            bot.send_message(
                message.chat.id,
                Messages.REQUEST_CANCELED,
                reply_markup=main_menu()
            )
        else:
            send_to_support(message)
        return
    
    # Обработка основных команд
    command_handlers = {
        Buttons.GET_KEY: lambda: _make_new_key(
            message, 
            DEFAULT_SERVER_ID, 
            _form_key_name(message)
        ),
        Buttons.MY_KEY: lambda: _send_existing_key(message),
        Buttons.DOWNLOAD: lambda: bot.send_message(
            message.chat.id, 
            f.make_download_message(), 
            disable_web_page_preview=True
        ),
        Buttons.SUPPORT: send_help,
        Buttons.DONATE: send_support_message
    }
    
    if text.startswith("/newkey"):
        server_id, key_name = _parse_the_command(message)
        _make_new_key(message, server_id, key_name)
    elif text in command_handlers:
        command_handlers[text]()
    else:
        bot.send_message(
            message.chat.id,
            Errors.UNKNOWN_COMMAND,
            reply_markup=main_menu()
        )

# --- CORE FUNCTIONS ---

def _make_new_key(message, server_id: ServerId, key_name: str):
    """
    Создает новый VPN-ключ или обрабатывает существующий ключ пользователя.
    
    Логика работы:
    1. Проверяет наличие старого ключа
    2. Если ключ был удален - создает новый
    3. Если ключ активен - показывает его пользователю
    4. Если ключа нет - создает новый
    
    Args:
        message: Объект сообщения от пользователя
        server_id: ID сервера Outline
        key_name: Имя для нового ключа
    """
    user_id = message.chat.id
    old_key_id = db.get_user_key(user_id)

    # Обработка случая, когда у пользователя уже есть ключ
    if old_key_id:
        # Если ключ был помечен как удаленный
        if db.is_key_deleted(old_key_id):
            try:
                # Шаг 1: Очищаем старые данные
                db.remove_user_key(user_id)
                
                # Шаг 2: Создаем новый ключ с лимитом трафика
                key = outline.get_new_key(
                    key_name=key_name,
                    server_id=server_id,
                    data_limit_gb=DEFAULT_DATA_LIMIT_GB
                )
                
                # Шаг 3: Сохраняем новый ключ
                db.save_user_key(user_id, key.kid)
                
                # Шаг 4: Отправляем ключ пользователю
                _send_key(message, key, server_id)
                
            except KeyCreationError:
                _send_error_message(message, Errors.API_CREATION_FAILED)
            except KeyRenamingError:
                _send_error_message(message, Errors.API_RENAMING_FAILED)
            except InvalidServerIdError:
                bot.send_message(message.chat.id, Errors.INVALID_SERVER_ID)
        
        # Если ключ активен
        else:
            try:
                # Пытаемся получить существующий ключ
                key = outline.get_key_by_id(old_key_id, server_id)
                bot.send_message(
                    message.chat.id,
                    Messages.key_info(key.access_url, is_new=False),
                    parse_mode="HTML"
                )
                
            except KeyError:
                # Если ключ не найден (например, удален вручную в Outline)
                key = outline.get_new_key(
                    key_name=key_name,
                    server_id=server_id,
                    data_limit_gb=DEFAULT_DATA_LIMIT_GB
                )
                db.save_user_key(user_id, key.kid)
                _send_key(message, key, server_id)
                
            except Exception as e:
                _send_error_message(message, Errors.UNEXPECTED_ERROR.format(error=str(e)))
    
    # Если у пользователя нет ключа
    else:
        try:
            # Создаем полностью новый ключ
            key = outline.get_new_key(
                key_name=key_name,
                server_id=server_id,
                data_limit_gb=DEFAULT_DATA_LIMIT_GB
            )
            db.save_user_key(user_id, key.kid)
            _send_key(message, key, server_id)
            
        except KeyCreationError:
            _send_error_message(message, Errors.API_CREATION_FAILED)
        except KeyRenamingError:
            _send_error_message(message, Errors.API_RENAMING_FAILED)
        except InvalidServerIdError:
            bot.send_message(message.chat.id, Errors.INVALID_SERVER_ID)

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
            bot.send_message(user_id, f"Ваш ключ:\n<code>{access_url}</code>\n\nСкопируйте и вставьте его в Outline.")
        else:
            bot.send_message(user_id, "Ваш ключ был удалён. Попробуйте получить новый или обратитесь в поддержку.")
    except KeyError as e:  # ловим ошибку, если ключ не найден
        db.mark_key_as_deleted(user_id)  # Помечаем ключ как удалённый
        bot.send_message(user_id, "Ваш ключ был удалён. Попробуйте получить новый или обратитесь в поддержку.")
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
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )

def send_to_support(message):
    global waiting_for_support
    
    your_telegram_id = 245413138
    user_message = message.text.strip()
    
    username = message.from_user.username
    user_link = f'<a href="https://t.me/{username}">пользователя</a>' if username else f'<a href="tg://user?id={message.from_user.id}">пользователя</a>'
    
    bot.send_message(
        your_telegram_id,
        f"📩 Новый запрос от {user_link}:\n\n{user_message}",
        parse_mode="HTML"
    )
    
    waiting_for_support = False
    bot.send_message(
        message.chat.id,
        "✅ Ваше сообщение отправлено в поддержку!",
        reply_markup=main_menu()
    )

def send_support_message(message):
    bot.send_message(
        message.chat.id,
        Donation.MESSAGE,
        parse_mode="HTML"
    )


def _parse_the_command(message) -> list:
    parts = message.text.strip().split()
    server_id = parts[1] if len(parts) > 1 else DEFAULT_SERVER_ID
    key_name = ''.join(parts[2:]) if len(parts) > 2 else _form_key_name(message)

    # Валидация server_id
    if not server_id.isdigit():
        raise InvalidServerIdError("Server ID must be numeric")

    return [server_id, key_name]


def _form_key_name(message) -> str:
    username = message.from_user.username or "no_username"
    return f"{message.chat.id}_{username}"


def start_telegram_server():
    db.init_db()
    monitoring.send_start_message()
    bot.infinity_polling()
