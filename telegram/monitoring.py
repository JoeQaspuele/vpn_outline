import telebot
from outline.api import check_api_status
from settings import MONITOR_API_TOKEN, ADMIN_CHAT_ID

assert MONITOR_API_TOKEN is not None
assert ADMIN_CHAT_ID is not None

monitor = telebot.TeleBot(MONITOR_API_TOKEN)


def new_key_created(key_id: int, key_name: str, chat_id: int, server_id: str) -> None:
    answer = ("New key created:" + 
            "\nkey_id: "     + str(key_id) + 
            "\nkey_name: "   + str(key_name) + 
            "\nchat_id: "    + str(chat_id) + 
            "\nserver_id: "  + str(server_id) 
             )
    monitor.send_message(ADMIN_CHAT_ID, answer)


def send_error(error_message: str, username: str | None, firstname: str | None,
        lastname: str | None) -> None:

    answer = ("Error detected!" + 
            "\nerror_message: " + error_message + 
            "\nuser_name: "     + str(username) + 
            "\nfirst_name: "    + str(firstname) + 
            "\nlast_name: "     + str(lastname))

    monitor.send_message(ADMIN_CHAT_ID, answer)


def send_api_status() -> None:
    api_status_codes = check_api_status() 
    message_to_send = ''
    for server_id, status_code in api_status_codes.items():
        message_to_send += f"server id:{server_id}, api_status_code: {status_code}\n"

    monitor.send_message(ADMIN_CHAT_ID, message_to_send)


def send_start_message():
    monitor.send_message(ADMIN_CHAT_ID, "-----BOT-STARTED!-----")
    send_api_status()


def report_not_in_whitelist(username: str, chat_id: str) -> None:

    msg = ("User tried to do something, but they are not in the whitelist.\n" +
           f"username: {username}\n" + 
           f"chat_id: {chat_id}")

    monitor.send_message(ADMIN_CHAT_ID, msg)


def report_blacklist_attempt(username: str, chat_id: str) -> None:

    msg = ("User tried to do something, but they are blacklisted.\n" +
           f"username: {username}\n" + 
           f"chat_id: {chat_id}")

    monitor.send_message(ADMIN_CHAT_ID, msg)
