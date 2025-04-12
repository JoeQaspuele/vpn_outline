import sqlite3
import requests
from outline import api
from datetime import datetime, timedelta
from settings import DEFAULT_SERVER_ID

PREMIUM_DURATION_DAYS = 31
FREE_DATA_LIMIT_GB = 15
DB_PATH = 'users.db'

def init_db():
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                key_name TEXT
                isPremium INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_keys (
                user_id INTEGER,
                key_name TEXT,
                is_deleted INTEGER DEFAULT 0,  -- Новый столбец для статуса удаления
                PRIMARY KEY (user_id, key_name),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (key_name) REFERENCES users (key_name)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_keys_user_id ON user_keys(user_id)')
        conn.commit()

def user_has_key(user_id: int) -> bool:
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None

def save_user_key(user_id: int, key_name: str):
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()

        # Удаляем старый ключ, если он существует
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        
        # Вставляем новый ключ
        cursor.execute('INSERT INTO users (user_id, key_name) VALUES (?, ?)', (user_id, key_name))
        
        # Сохраняем ключ в таблице user_keys
        cursor.execute('INSERT INTO user_keys (user_id, key_name) VALUES (?, ?)', (user_id, key_name))
        
        conn.commit()


def get_user_key(user_id: int) -> str | None:
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT key_name FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

# Функция для проверки, был ли ключ удалён
def is_key_deleted(user_id: int) -> bool:
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT is_deleted FROM user_keys WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False  # Проверяем, помечен ли ключ как удалённый

# Функция для пометки ключа как удалённого
def mark_key_as_deleted(user_id: int):
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE user_keys SET is_deleted = 1 WHERE user_id = ?', (user_id,))
        conn.commit()

# Функция для удаления ключа (физически)
def remove_key(user_id: int):
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_keys WHERE user_id = ?', (user_id,))
        conn.commit()

def set_premium(user_id: int):
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        premium_date = datetime.utcnow().isoformat()
        cursor.execute('UPDATE users SET isPremium = 1, premium_since = ? WHERE user_id = ?', (premium_date, user_id))
        conn.commit()

def check_premium_expiration():
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, premium_since FROM users WHERE isPremium = 1')
        rows = cursor.fetchall()

        for user_id, since_str in rows:
            if since_str:
                try:
                    premium_date = datetime.fromisoformat(since_str)
                    if datetime.utcnow() - premium_date > timedelta(days=PREMIUM_DURATION_DAYS):
                        print(f"⏳ PREMIUM у пользователя {user_id} истёк. Сбрасываем.")
                        cursor.execute('UPDATE users SET isPremium = 0, premium_since = NULL WHERE user_id = ?', (user_id,))

                        # Снижаем лимит до 15 ГБ
                        key = get_user_key(user_id)
                        if key:
                            #from outline import api
                            api._set_access_key_data_limit(
                                key_id=key,
                                limit_in_bytes=FREE_DATA_LIMIT_GB * 1024**3,
                                server_id=DEFAULT_SERVER_ID
                            )
                except Exception as e:
                    print(f"⚠️ Ошибка при проверке премиума пользователя {user_id}: {e}")

        conn.commit()

def get_premium_date(user_id: int) -> str | None:
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT premium_since FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None


def get_all_premium_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE isPremium = 1")
    rows = cursor.fetchall()

    conn.close()
# Возвращаем список словарей, можно и просто список ID
    return [{"user_id": row[0]} for row in rows]

def get_all_users(only_regular: bool = True) -> list[dict]:
    """Возвращает пользователей с их ключами.
    Args:
        only_regular: Если True (по умолчанию), возвращает только обычных пользователей (не премиум).
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if only_regular:
            cursor.execute('''
                SELECT user_id, key_name, "limit", "used"
                FROM users
                WHERE isPremium = 0
            ''')
        else:
            cursor.execute('SELECT user_id, key_name, "limit", "used" FROM users')

        return [{
            'user_id': row[0],
            'key_name': row[1],
            'limit': row[2],
            'used': row[3]
        } for row in cursor.fetchall()]

def update_user_limits(user_id: int, used: float, limit: int = 15):
    """Обновляет used и limit для пользователя."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET "used" = ?, "limit" = ?, traffic_start_bytes = ?, traffic_start_date = ? WHERE user_id = ?',
            (used, limit, 0, datetime.utcnow().isoformat(), user_id)  # used_bytes заменено на 0
        )
        conn.commit()
        
def get_user_data(user_id: int) -> dict:
    """Возвращает ВСЕ данные пользователя за один запрос"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT "limit", "used", isPremium, traffic_start_bytes, traffic_start_date 
            FROM users
            WHERE user_id = ?
        ''', (user_id,))
        row = cursor.fetchone()

        return {
            'limit': row[0] if row else 15,
            'used': row[1] if row else 0,
            'isPremium': bool(row[2]) if row else False,
            'traffic_start_bytes': row[3] if row and row[3] is not None else 0,
            'traffic_start_date': row[4] if row else None
        } if row else None

# Получить дату и байты начала месяца
def get_traffic_reset_info(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT traffic_start_bytes, traffic_start_date FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0] or 0, row[1]
    return 0, None

# Установить новые данные начала месяца
def set_traffic_reset_info(user_id, start_bytes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET traffic_start_bytes = ?, traffic_start_date = ? WHERE user_id = ?",
        (start_bytes, datetime.now().isoformat(), user_id)
    )
    conn.commit()
    conn.close()

def extend_premium(user_id: int, new_end_date: str):
    """Продлевает премиум-статус до указанной даты"""
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET isPremium = 1, premium_since = ? WHERE user_id = ?',
            (new_end_date, user_id))
        conn.commit()
        
def init_user(user_id: int):
    """Создает запись пользователя с дефолтными значениями"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO users (user_id, "used", "limit") VALUES (?, 0, 15)',
            (user_id,)
        )
        conn.commit()
