import telebot
from telebot import types
from settings import (
    BOT_API_TOKEN,
    DEFAULT_SERVER_ID,
    BLACKLISTED_CHAT_IDS,
    WHITELISTED_CHAT_IDS,
    ENABLE_BLACKLIST,
    ENABLE_WHITELIST
)
import telegram.monitoring as monitoring
import outline.api as outline
from helpers.exceptions import KeyCreationError, KeyRenamingError, InvalidServerIdError
import telegram.message_formatter as f
from helpers.aliases import ServerId
import db  # <-- наш новый модуль для базы данных

assert BOT_API_TOKEN is not None
bot = telebot.TeleBot(BOT_API_TOKEN, parse_mode='HTML')


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
    bot.send_message(message.chat.id, "Hey! This bot is used for creating Outline keys.", reply_markup=_make_main_menu_markup())


@bot.message_handler(commands=['help'])
@authorize
def send_help(message):
    bot.send_message(message.chat.id, f.make_help_message())


@bot.message_handler(commands=['servers'])
@authorize
def send_servers_list(message):
    bot.send_message(message.chat.id, f.make_servers_list())


@bot.message_handler(content_types=['text'])
@authorize
def answer(message):
    text = message.text.strip()
    if text == "🔑 Получить ключ VPN":
        server_id = DEFAULT_SERVER_ID
        key_name = _form_key_name(message)
        _make_new_key(message, server_id, key_name)
    elif text == "🗝️  Мой ключ VPN":
        _send_existing_key(message)
    elif text == "🌐 Скачать клиент VPN":
        bot.send_message(message.chat.id, f.make_download_message(), disable_web_page_preview=True)
    elif text == "❓ Помощь":
        bot.send_message(message.chat.id, 
                         "Опишите свою проблему. Среднее ожидание ответа от поддержки от 10 до 60 минут. Ваше сообщение будет отправлено в поддержку.")
        bot.register_next_step_handler(message, send_to_support)
    elif text == "💰 Поддержать VPN":
        send_support_message(message)
    elif text.startswith("/newkey"):
        server_id, key_name = _parse_the_command(message)
        _make_new_key(message, server_id, key_name)
    else:
        bot.send_message(message.chat.id, "Unknown command.", reply_markup=_make_main_menu_markup())


# --- CORE FUNCTIONS ---
def _make_new_key(message, server_id: ServerId, key_name: str):
    user_id = message.chat.id

    # Проверяем, есть ли уже ключ у пользователя
    old_key_id = db.get_user_key(user_id)

    if old_key_id:
        # Если ключ существует, проверяем, был ли он удалён
        if db.is_key_deleted(old_key_id):
            # Ключ был удалён, создаём новый ключ
            try:
                # Удаляем старый ключ из базы (если он был удалён вручную)
                db.remove_user_key(user_id)
                
                # Создаём новый ключ
                key = outline.get_new_key(key_name, server_id)
                db.save_user_key(user_id, key.kid)
                _send_key(message, key, server_id)
            except KeyCreationError:
                _send_error_message(message, "API error: cannot create the key")
            except KeyRenamingError:
                _send_error_message(message, "API error: cannot rename the key")
            except InvalidServerIdError:
                bot.send_message(message.chat.id, "The server id does not exist.")
        else:
            # Ключ не удалён, отправляем сообщение, что у пользователя уже есть ключ
            try:
                key = outline.get_key_by_id(old_key_id, server_id)
                access_url = key.access_url
                bot.send_message(message.chat.id, f"У вас уже есть ключ: <code>{access_url}</code>\n\nСкопируйте и вставьте его в Outline.")
            except KeyError:
                # Если ключ не найден в API, возможно, он был удалён в Outline
                key = outline.get_new_key(key_name, server_id)
                db.save_user_key(user_id, key.kid)
                _send_key(message, key, server_id)
            except KeyCreationError:
               _send_error_message(message, "API error: cannot create the key")
            except KeyRenamingError:
               _send_error_message(message, "API error: cannot rename the key")
            except InvalidServerIdError:
               bot.send_message(message.chat.id, "The server id does not exist.")
            except Exception as e:
                _send_error_message(message, f"Ошибка при получении ключа: {e}")
    else:
        # Если ключа нет, создаём новый
        try:
            key = outline.get_new_key(key_name, server_id)
            db.save_user_key(user_id, key.kid)
            _send_key(message, key, server_id)
        except KeyCreationError:
            _send_error_message(message, "API error: cannot create the key")
        except KeyRenamingError:
            _send_error_message(message, "API error: cannot rename the key")
        except InvalidServerIdError:
            bot.send_message(message.chat.id, "The server id does not exist.")


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


def _make_main_menu_markup() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🔑 Получить ключ VPN"),
        types.KeyboardButton("🗝️  Мой ключ VPN"),
        types.KeyboardButton("🌐 Скачать клиент VPN"),
        types.KeyboardButton("❓ Помощь"),
        types.KeyboardButton("💰 Поддержать VPN")
    )
    return markup

def send_to_support(message):
    # Ваш Telegram ID для получения сообщений
    your_telegram_id = 245413138  # Замените на свой ID
    user_message = message.text.strip()
    
    # Получаем username пользователя
    username = message.from_user.username
    
    if username:
        # Если username есть, создаем ссылку на его профиль
        user_profile_link = f"https://t.me/{username}"
    else:
        # Если username нет, отправляем ссылку с user_id
        user_profile_link = f"https://t.me/id{message.from_user.id}"
    
    # Отправка сообщения вам в личку, добавляем ссылку на профиль пользователя
    bot.send_message(your_telegram_id, f"Сообщение от пользователя {user_profile_link}:\n{user_message}")
    
    # Информируем пользователя, что его запрос принят
    bot.send_message(message.chat.id, "Ваш запрос отправлен в поддержку. Мы ответим в ближайшее время.",
                     reply_markup=_make_main_menu_markup())  # Возвращаем пользователя к основному меню


def send_support_message(message):
    # Отправляем сообщение с информацией для поддержки
    bot.send_message(message.chat.id, "Спасибо за желание поддержать мой проект!\n"
                                      "Ваша поддержка поможет поддерживать в работе сервер.\n\n"
                                      "Вы можете перевести средства на карту:\n"
                                      "2200 7001 5676 6098\n\n"
                                      "Спасибо за вашу помощь и поддержку!")


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
