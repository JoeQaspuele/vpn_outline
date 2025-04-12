#!/usr/bin/env python3
import sys
import os
import logging
from datetime import datetime
from outline.api import get_traffic_for_key, _set_access_key_data_limit
from db import get_all_users, update_user_limits
from settings import DEFAULT_SERVER_ID

# Настройка логов
logging.basicConfig(
    filename='/var/log/vpn/reset_limits.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def reset_monthly_limits():
    try:
        users = get_all_users(only_regular=True)
        if not users:
            logging.warning("Нет пользователей для обработки")
            return

        for user in users:
            key_id = user.get('key_name')
            if not key_id:
                continue

            try:
                # Получаем текущий трафик
                used_bytes = get_traffic_for_key(key_id, DEFAULT_SERVER_ID)
                used_gb = used_bytes / (1024 ** 3)
                
                # Новый лимит
                new_limit_bytes = int((used_gb + 15) * (1024 ** 3))
                
                # Обновляем в Outline
                _set_access_key_data_limit(key_id, new_limit_bytes, DEFAULT_SERVER_ID)
                
                # Обнуляем used в БД
                update_user_limits(user['user_id'], 0, 15)
                
                logging.info(f"User {user['user_id']}: updated limit to {used_gb + 15:.2f} GB")

            except Exception as e:
                logging.error(f"Ошибка для user_id={user['user_id']}: {str(e)}")
                continue

        logging.info(f"Успешно обработано {len(users)} пользователей")

    except Exception as e:
        logging.critical(f"Критическая ошибка: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # Добавляем путь к проекту в PYTHONPATH
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    reset_monthly_limits()
