import hashlib
import os
import sys
import sqlite3

try:
    import pymysql  # type: ignore
except Exception:
    pymysql = None

DB_FILENAME = "database.db"
local = False
force_local = False

def get_default_db_path():
    """
    Возвращает путь для файла БД.
    На Android кладём в app_storage_path(), на десктопе — в текущий каталог.
    """
    if sys.platform == "android":
        try:
            from android.storage import app_storage_path  # type: ignore
            return os.path.join(app_storage_path(), DB_FILENAME)
        except Exception:
            return os.path.join(os.getcwd(), DB_FILENAME)
    return os.path.join(os.getcwd(), DB_FILENAME)

def set_force_local(value=True):
    global force_local
    force_local = value

def get_connection(database="sqlite", path=None):
    global local, force_local

    if sys.platform == "android":
        database = "sqlite"

    db_path = path or get_default_db_path()

    if database == "sqlite" or force_local or pymysql is None:
        return sqlite3.connect(db_path)
    else:
        try:
            if not local:
                if pymysql is None:
                    raise ImportError("pymysql is not available")
                conn = pymysql.connect(
                    host='localhost',
                    user='root',
                    password='',
                    database='health_diary',
                    charset='utf8mb4',
                )
            else:
                return sqlite3.connect(db_path)
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            print(f"Переход на локальную базу данных...")
            local = True
            return sqlite3.connect(db_path)

        else:
            return conn


def insert_user_session(conn, user_id, device_id, session_token, expires_at):
    try:
        cursor = conn.cursor()

        is_sqlite = hasattr(conn, 'isolation_level')

        if is_sqlite:
            cursor.execute(f"""
                INSERT OR REPLACE INTO user_sessions (user_id, device_id, session_token, expires_at)
                VALUES ({user_id}, '{device_id}', '{session_token}', '{expires_at}')
            """)
        else:
            cursor.execute(f"""
                INSERT INTO user_sessions (user_id, device_id, session_token, expires_at)
                VALUES ({user_id}, '{device_id}', '{session_token}', '{expires_at}')
                ON DUPLICATE KEY UPDATE 
                session_token = VALUES(session_token), 
                expires_at = VALUES(expires_at),
                created_at = CURRENT_TIMESTAMP
            """)

        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при INSERT: {e}")

def insert_user(conn, email, password_hash, name, is_admin=False):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO users (email, password_hash, name, is_admin) VALUES ('{email}', '{password_hash}', '{name}', {1 if is_admin else 0})"
        )
        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при INSERT: {e}")

def insert_record(conn, user_id, weight, pressure_systolic, pressure_diastolic, pulse, temperature, notes, record_date):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""INSERT INTO records (user_id, weight, pressure_systolic, pressure_diastolic, pulse, temperature, notes, record_date)
                        VALUES ({user_id}, {weight}, {pressure_systolic}, {pressure_diastolic}, {pulse}, {temperature}, '{notes}', '{record_date}')"""
        )
        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при INSERT: {e}")

def insert_user_settings(conn, user_id, settings):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO user_settings (user_id, settings) VALUES ({user_id}, '{settings}')"
        )
        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при INSERT: {e}")

def insert_admin_action(conn, admin_id, action_type, action_details, affected_user_id=None, ip_address=None):
    """
    Записывает действие администратора в журнал

    Args:
        conn: соединение с базой данных
        admin_id: ID администратора
        action_type: тип действия (view_records, delete_user, etc.)
        action_details: детали действия
        affected_user_id: ID затронутого пользователя
        ip_address: IP адрес
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""INSERT INTO admin_actions (admin_id, action_type, action_details, affected_user_id, ip_address)
                VALUES ({admin_id}, '{action_type}', '{action_details}', {affected_user_id if affected_user_id else 'NULL'}, '{ip_address if ip_address else ''}')"""
        )
        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при INSERT admin_action: {e}")

def update_user_settings(conn, user_id, settings):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE user_settings SET settings = '{settings}' WHERE user_id = {user_id}"
        )
        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при UPDATE: {e}")

def update_record(conn, record_id, weight, pressure_systolic, pressure_diastolic, pulse, temperature, notes):
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
                        UPDATE records
                        SET weight={weight}, pressure_systolic={pressure_systolic},
                            pressure_diastolic={pressure_diastolic}, pulse={pulse}, temperature={temperature}, notes='{notes}'
                        WHERE id={record_id}
                    """)
        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при UPDATE: {e}")

def update_user_photo(conn, user_id, image_data):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE users SET profile_photo = '{image_data}' WHERE id = {user_id}",
        )
        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при UPDATE: {e}")

def update_user(conn, user_id, name, email):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE users SET name = '{name}', email = '{email}' WHERE id = {user_id}",
        )
        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при UPDATE: {e}")

def update_user_admin_status(conn, user_id, is_admin):
    """
    Обновляет статус администратора пользователя

    Args:
        conn: соединение с базой данных
        user_id: ID пользователя
        is_admin: 1 если администратор, 0 если нет
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE users SET is_admin = {1 if is_admin else 0} WHERE id = {user_id}",
        )
        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при UPDATE admin status: {e}")

def delete_user_session_db(conn, device_id, user_id=None):
    try:
        cursor = conn.cursor()
        if user_id:
            cursor.execute(
                f"DELETE FROM user_sessions WHERE user_id = {user_id} AND device_id = '{device_id}'"
            )
        else:
            cursor.execute(
                f"DELETE FROM user_sessions WHERE device_id = '{device_id}'"
            )

        conn.commit()

    except Exception as e:
        print(f"Ошибка базы данных при DELETE: {e}")

def delete_record(conn, record_id):
    try:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM records WHERE id = {record_id}")
        conn.commit()
        return True

    except Exception as e:
        print(f"Ошибка базы данных при DELETE записи: {e}")
        return False

def select_user_by_email(conn, email, pass_hash=False):
    try:
        cursor = conn.cursor()
        if pass_hash:
            cursor.execute(f"SELECT id, password_hash, is_admin FROM users WHERE email='{email}'")
        else:
            cursor.execute(f"SELECT id, is_admin FROM users WHERE email='{email}'")

        entry = cursor.fetchone()
        if entry:
            return entry
        else:
            return None

    except Exception as e:
        print(f"Ошибка базы данных при SELECT: {e}")
        return None

def select_user_by_id(conn, user_id, detailed=False):
    try:
        cursor = conn.cursor()
        if detailed:
            cursor.execute(
                f"SELECT name, email, created_at, profile_photo, is_admin FROM users WHERE id = {user_id}",
            )
        else:
            cursor.execute(f"SELECT name, email, is_admin FROM users WHERE id = {user_id}")

        entry = cursor.fetchone()
        if entry:
            return entry
        else:
            return None

    except Exception as e:
        print(f"Ошибка базы данных при SELECT: {e}")
        return None

def select_user_count_by_email(conn, email):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM users WHERE email = '{email}'")

        entry = cursor.fetchone()
        if entry:
            return entry
        else:
            return None

    except Exception as e:
        print(f"Ошибка базы данных при SELECT: {e}")
        return None


def select_all_users(conn, limit=100):
    """
    Выбирает всех пользователей из базы данных

    Args:
        conn: соединение с базой данных
        limit: ограничение количества записей

    Returns:
        Список пользователей или None
    """

    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, name, email, created_at, is_admin 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT {limit}
        """)
        entry = cursor.fetchall()
        if entry:
            return entry
        else:
            return None

    except Exception as e:
        print(f"Ошибка базы данных при SELECT всех пользователей: {e}")
        return None


def select_all_records(conn, limit=500):
    """
    Выбирает все записи из базы данных с информацией о пользователях

    Args:
        conn: соединение с базой данных
        limit: ограничение количества записей

    Returns:
        Список записей с информацией о пользователях или None
    """

    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT 
                r.id, 
                r.user_id, 
                u.name as user_name, 
                u.email as user_email,
                r.weight, 
                r.pressure_systolic, 
                r.pressure_diastolic, 
                r.pulse, 
                r.temperature, 
                r.notes, 
                r.record_date,
                r.created_at
            FROM records r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.record_date DESC, r.created_at DESC
            LIMIT {limit}
        """)

        entry = cursor.fetchall()
        if entry:
            return entry
        else:
            return None

    except Exception as e:
        print(f"Ошибка базы данных при SELECT всех записей: {e}")
        return None


def select_user_records_by_admin(conn, user_id=None, limit=200):
    """
    Выбирает записи конкретного пользователя или всех пользователей для администратора

    Args:
        conn: соединение с базой данных
        user_id: ID пользователя (None для всех пользователей)
        limit: ограничение количества записей

    Returns:
        Список записей или None
    """

    try:
        cursor = conn.cursor()
        if user_id:
            cursor.execute(f"""
                SELECT 
                    r.id, 
                    r.user_id, 
                    u.name as user_name, 
                    u.email as user_email,
                    r.weight, 
                    r.pressure_systolic, 
                    r.pressure_diastolic, 
                    r.pulse, 
                    r.temperature, 
                    r.notes, 
                    r.record_date,
                    r.created_at
                FROM records r
                JOIN users u ON r.user_id = u.id
                WHERE r.user_id = {user_id}
                ORDER BY r.record_date DESC, r.created_at DESC
                LIMIT {limit}
            """)
        else:
            cursor.execute(f"""
                SELECT 
                    r.id, 
                    r.user_id, 
                    u.name as user_name, 
                    u.email as user_email,
                    r.weight, 
                    r.pressure_systolic, 
                    r.pressure_diastolic, 
                    r.pulse, 
                    r.temperature, 
                    r.notes, 
                    r.record_date,
                    r.created_at
                FROM records r
                JOIN users u ON r.user_id = u.id
                ORDER BY r.record_date DESC, r.created_at DESC
                LIMIT {limit}
            """)

        entry = cursor.fetchall()
        if entry:
            return entry
        else:
            return None

    except Exception as e:
        print(f"Ошибка базы данных при SELECT записей для администратора: {e}")
        return None

def select_settings_by_user(conn, user_id, check=False):
    try:
        cursor = conn.cursor()
        if check:
            cursor.execute(f"SELECT 1 FROM user_settings WHERE user_id = {user_id}")
        else:
            cursor.execute(f"SELECT settings FROM user_settings WHERE user_id = {user_id}")

        entry = cursor.fetchone()
        if entry:
            return entry
        else:
            return None

    except Exception as e:
        print(f"Ошибка базы данных при SELECT: {e}")
        return None

def select_user_session_by_device(conn, device_id):
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
                        SELECT us.user_id, u.email, u.name, u.is_admin 
                        FROM user_sessions us
                        JOIN users u ON us.user_id = u.id
                        WHERE us.device_id = '{device_id}' AND (us.expires_at IS NULL OR us.expires_at > CURRENT_TIMESTAMP)
                    """)

        entry = cursor.fetchone()
        if entry:
            return entry
        else:
            return None

    except Exception as e:
        print(f"Ошибка базы данных при SELECT: {e}")
        return None

def select_records_by_user(conn, user_id):
    try:
        cursor = conn.cursor()
        cursor.execute(f"""SELECT id, weight, pressure_systolic, pressure_diastolic,
                                      pulse, temperature, notes, record_date
                                      FROM records WHERE user_id = {user_id} ORDER BY record_date DESC""")

        entry = cursor.fetchall()
        if entry:
            return entry
        else:
            return None

    except Exception as e:
        print(f"Ошибка базы данных при SELECT: {e}")
        return None


def select_admin_actions(conn, admin_id=None, limit=100):
    """
    Выбирает действия администраторов из журнала

    Args:
        conn: соединение с базой данных
        admin_id: ID администратора (None для всех)
        limit: ограничение количества записей

    Returns:
        Список действий или None
    """

    try:
        cursor = conn.cursor()
        if admin_id:
            cursor.execute(f"""
                SELECT 
                    aa.id, 
                    aa.admin_id, 
                    a.name as admin_name,
                    aa.action_type, 
                    aa.action_details, 
                    aa.affected_user_id,
                    u.name as affected_user_name,
                    aa.ip_address,
                    aa.created_at
                FROM admin_actions aa
                LEFT JOIN users a ON aa.admin_id = a.id
                LEFT JOIN users u ON aa.affected_user_id = u.id
                WHERE aa.admin_id = {admin_id}
                ORDER BY aa.created_at DESC
                LIMIT {limit}
            """)
        else:
            cursor.execute(f"""
                SELECT 
                    aa.id, 
                    aa.admin_id, 
                    a.name as admin_name,
                    aa.action_type, 
                    aa.action_details, 
                    aa.affected_user_id,
                    u.name as affected_user_name,
                    aa.ip_address,
                    aa.created_at
                FROM admin_actions aa
                LEFT JOIN users a ON aa.admin_id = a.id
                LEFT JOIN users u ON aa.affected_user_id = u.id
                ORDER BY aa.created_at DESC
                LIMIT {limit}
            """)

        entry = cursor.fetchall()
        if entry:
            return entry
        else:
            return None

    except Exception as e:
        print(f"Ошибка базы данных при SELECT действий администратора: {e}")
        return None


def get_user_statistics(conn, user_id=None):
    """
    Получает статистику по пользователям и записям

    Args:
        conn: соединение с базой данных
        user_id: ID пользователя (None для общей статистики)

    Returns:
        Словарь со статистикой
    """


    try:
        cursor = conn.cursor()
        stats = {}

        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM records")
        stats['total_records'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        stats['total_admins'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        stats['total_sessions'] = cursor.fetchone()[0]

        # Статистика за последние 7 дней
        cursor.execute("""
            SELECT COUNT(*) FROM records 
            WHERE record_date >= DATE('now', '-7 days')
        """)
        stats['records_last_7_days'] = cursor.fetchone()[0]

        # Статистика по пользователям (если не указан конкретный пользователь)
        if not user_id:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT user_id) as active_users,
                    AVG(records_per_user) as avg_records_per_user
                FROM (
                    SELECT user_id, COUNT(*) as records_per_user
                    FROM records
                    WHERE record_date >= DATE('now', '-30 days')
                    GROUP BY user_id
                )
            """)
            result = cursor.fetchone()
            if result:
                stats['active_users_30_days'] = result[0] if result[0] else 0
                stats['avg_records_per_user'] = round(result[1], 2) if result[1] else 0

        return stats

    except Exception as e:
        print(f"Ошибка базы данных при получении статистики: {e}")
        return {}

def create_admin_user():
    """
    Создает учетную запись администратора
    """

    print("=" * 50)
    print("Создание учетной записи администратора")
    print("=" * 50)

    # Ввод данных администратора
    #email = input("Введите email администратора: ").strip()
    #name = input("Введите имя администратора: ").strip()
    #password = input("Введите пароль администратора: ").strip()
    #confirm_password = input("Повторите пароль: ").strip()

    email = "test@admin.com"
    name = "admin"
    password = "root"

    # Хеширование пароля
    def hash_password(password: str) -> str:
        salt = os.urandom(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + pwd_hash.hex()


    password_hash = hash_password(password)

    try:
        # Подключение к базе данных
        conn = get_connection(path="database.db")

        # Проверка существования пользователя
        existing_user = select_user_by_email(conn, email)
        if existing_user:
            print(f"Ошибка: Пользователь с email '{email}' уже существует!")
            conn.close()
            return

        # Создание администратора
        insert_user(conn, email, password_hash, name, is_admin=True)

        print("=" * 50)
        print("Администратор успешно создан!")
        print(f"Email: {email}")
        print(f"Имя: {name}")
        print("=" * 50)

        conn.close()

    except Exception as e:
        print(f"Ошибка при создании администратора: {e}")


def init_db():
    conn = sqlite3.connect(get_default_db_path())
    sql_code = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                profile_photo TEXT,
                is_admin INTEGER DEFAULT 0,
                idx_email TEXT
            );

            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                record_date DATE NOT NULL,
                weight REAL,
                pressure_systolic INTEGER,
                pressure_diastolic INTEGER,
                pulse INTEGER,
                sleep_hours REAL,
                temperature REAL,
                mood TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_user_date ON records (user_id, record_date);
            CREATE INDEX IF NOT EXISTS idx_date ON records (record_date);

            CREATE TABLE IF NOT EXISTS exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                export_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                export_format TEXT NOT NULL CHECK (export_format IN ('PDF', 'Excel')),
                file_path TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_user_export ON exports (user_id, export_date);

            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                settings TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_user ON user_settings (user_id);

            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reminder_time TIME NOT NULL,
                reminder_type TEXT NOT NULL,
                message TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_user_active ON reminders (user_id, is_active);
            CREATE INDEX IF NOT EXISTS idx_time ON reminders (reminder_time);

            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_id TEXT,
                session_token TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_token ON user_sessions (session_token);
            CREATE INDEX IF NOT EXISTS idx_user_device ON user_sessions (user_id, device_id);
            CREATE INDEX IF NOT EXISTS idx_expires ON user_sessions (expires_at);
            
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                action_details TEXT,
                affected_user_id INTEGER,
                ip_address TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_admin_actions ON admin_actions (admin_id, created_at);
    """

    cursor = conn.cursor()

    # Разделяем SQL на отдельные команды и выполняем их
    commands = sql_code.split(';')
    for command in commands:
        command = command.strip()
        if command:
            cursor.execute(command)

    conn.commit()

    try:
        create_admin_user()
    except:
        print("Unable to insert Admin")

