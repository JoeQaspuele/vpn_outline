from settings import (
    OUTLINE_WINDOWS_DOWNLOAD_LINK,
    OUTLINE_MACOS_DOWNLOAD_LINK,
    OUTLINE_LINUX_DOWNLOAD_LINK,
    OUTLINE_CHOMEOS_DOWNLOAD_LINK,
    OUTLINE_IOS_DOWNLOAD_LINK,
    OUTLINE_ANDROID_DOWNLOAD_LINK,
    OUTLINE_ANDROID_APK_DOWNLOAD_LINK,
    servers
    )
from helpers.aliases import ServerId
from textwrap import dedent


def make_message_for_new_key(app: str, access_key: str,
                             server_id: ServerId) -> str:
   if app == "outline":
      message_to_send = dedent(
f"""<b>🔑 Твой ключ для доступа к OUTLINE:🔑 </b>
      \n<code>{access_key}</code>
      \nНажми на 🔑 выше  чтобы скопировать.\nНеобходимо добавить ключ в приложение для доступа.
      \nСервер :<b>{servers[server_id].location}</b>
      \nУ тебя бесплатный тариф. Ключ можно использовать на всех устройствах. Ограничений нет.
      \nТвой лимит трафика:<b>15GB</b> на 1 месяц.
      \nСброс трафика происходит 1 числа каждого  месяца.
      \nВставь полученный ключ в клиент <b>Outline Client.</b> \nСкачать можно нажав на соответствующую кнопку в telegram боте.
      """)

   else:
      # TODO
      raise Exception

   return message_to_send


def make_download_message() -> str:
    message_to_send = dedent(
    f"""
   <a href="{OUTLINE_WINDOWS_DOWNLOAD_LINK}">   Скачать на  Windows 🪟 </a>

   <a href="{OUTLINE_MACOS_DOWNLOAD_LINK}">Скачать на MacOS 🍏 </a>

   <a href="{OUTLINE_LINUX_DOWNLOAD_LINK}">Скачать на  Linux 🐧</a>

   <a href="{OUTLINE_CHOMEOS_DOWNLOAD_LINK}">Скачать на  ChromeOS 🌐</a>

   <a href="{OUTLINE_IOS_DOWNLOAD_LINK}">Скачать на iOS (AppStore)  🍎</a>

   <a href="{OUTLINE_ANDROID_DOWNLOAD_LINK}">Скачать на  Android 🤖 </a>

   <a href="{OUTLINE_ANDROID_APK_DOWNLOAD_LINK}">Скачать APK 📦</a>
   \nУстановив приложение не удаляй его с телефона, 
   в дальнейшем может быть не доступен в твоем магазине приложений.
    """)
    return message_to_send


def make_help_message() -> str:

    message_to_send = "Press the button to create a key. "\


    return message_to_send


def make_servers_list() -> str:

    message_to_send = ""
    for server_id, server in servers.items():
        message_to_send += f'server_id: {server_id}, location: {server.location}\n'
    return message_to_send
