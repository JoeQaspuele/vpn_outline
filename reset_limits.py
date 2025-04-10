from datetime import datetime
from db import get_all_users, update_user_limits
from api import get_traffic_for_key, _set_access_key_data_limit
from settings import DEFAULT_SERVER_ID

def reset_monthly_limits():
    """Сбрасывает лимиты трафика для всех пользователей в начале месяца."""
    users = get_all_users()  # Нужно добавить эту функцию в db.py
    
    for user in users:
        key_id = user.get('key_name')  # Или другой способ получить key_id
        if not key_id:
            continue
        
        # Получаем потраченный трафик (в байтах)
        used_bytes = get_traffic_for_key(key_id, DEFAULT_SERVER_ID)
        used_gb = used_bytes / (1024 ** 3)  # Переводим в ГБ
        
        # Обновляем лимит: used + 15 ГБ (новый лимит)
        new_limit_bytes = (used_gb + 15) * (1024 ** 3)
        _set_access_key_data_limit(key_id, new_limit_bytes, DEFAULT_SERVER_ID)
        
        # Сохраняем used в БД
        update_user_limits(user['user_id'], used_gb, 15)
