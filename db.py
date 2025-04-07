import sqlite3

DB_PATH = 'users.db'

def init_db():
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                key_name TEXT
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
