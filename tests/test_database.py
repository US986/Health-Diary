"""
Тесты для модуля database.py
"""

import pytest
import sqlite3
import json


def init_test_db(conn):
    """Инициализация тестовой базы данных"""
    cursor = conn.cursor()

    # Создаем таблицы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            profile_photo TEXT,
            is_admin INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            record_date DATE NOT NULL,
            weight REAL,
            pressure_systolic INTEGER,
            pressure_diastolic INTEGER,
            pulse INTEGER,
            temperature REAL,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            settings TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            device_id TEXT,
            session_token TEXT NOT NULL UNIQUE,
            expires_at DATETIME NOT NULL
        )
    """)

    conn.commit()


class TestDatabase:
    """Тесты функций базы данных"""

    def test_insert_and_select_user(self, temp_db):
        """Тест добавления и поиска пользователя"""
        conn = temp_db
        cursor = conn.cursor()

        # Добавляем пользователя
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            ("test@example.com", "hash123", "Test User")
        )
        conn.commit()

        # Ищем пользователя
        cursor.execute("SELECT * FROM users WHERE email = ?", ("test@example.com",))
        user = cursor.fetchone()

        assert user is not None
        assert user[1] == "test@example.com"  # email
        assert user[3] == "Test User"  # name

    def test_insert_and_select_record(self, temp_db):
        """Тест добавления и поиска записей"""
        conn = temp_db
        cursor = conn.cursor()

        # Добавляем пользователя
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            ("test@example.com", "hash123", "Test User")
        )
        conn.commit()

        # Добавляем запись
        cursor.execute("""
            INSERT INTO records 
            (user_id, weight, pressure_systolic, pressure_diastolic, 
             pulse, temperature, notes, record_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, 70.5, 120, 80, 75, 36.6, "Тестовая запись", "2024-01-01 10:00:00"))
        conn.commit()

        # Ищем записи пользователя
        cursor.execute("SELECT * FROM records WHERE user_id = ?", (1,))
        records = cursor.fetchall()

        assert records is not None
        assert len(records) == 1

        record = records[0]
        assert record[3] == 70.5  # вес
        assert record[4] == 120  # систолическое давление
        assert record[6] == 75  # пульс

    def test_user_settings(self, temp_db):
        """Тест работы с настройками пользователя"""
        conn = temp_db
        cursor = conn.cursor()

        # Добавляем пользователя
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            ("test@example.com", "hash123", "Test User")
        )
        conn.commit()

        # Добавляем настройки
        settings = {'theme': 'blue', 'dark_mode': False}
        cursor.execute(
            "INSERT INTO user_settings (user_id, settings) VALUES (?, ?)",
            (1, json.dumps(settings))
        )
        conn.commit()

        # Получаем настройки
        cursor.execute("SELECT settings FROM user_settings WHERE user_id = ?", (1,))
        result = cursor.fetchone()

        assert result is not None
        loaded_settings = json.loads(result[0])
        assert loaded_settings['theme'] == 'blue'
        assert loaded_settings['dark_mode'] is False

    def test_user_sessions(self, temp_db):
        """Тест работы с сессиями пользователя"""
        conn = temp_db
        cursor = conn.cursor()

        # Добавляем пользователя
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            ("test@example.com", "hash123", "Test User")
        )
        conn.commit()

        # Добавляем сессию
        cursor.execute("""
            INSERT INTO user_sessions 
            (user_id, device_id, session_token, expires_at)
            VALUES (?, ?, ?, ?)
        """, (1, "device123", "token123", "2024-12-31 23:59:59"))
        conn.commit()

        # Ищем сессию
        cursor.execute("""
            SELECT us.user_id, u.email, u.name 
            FROM user_sessions us
            JOIN users u ON us.user_id = u.id
            WHERE us.device_id = ?
        """, ("device123",))
        result = cursor.fetchone()

        assert result is not None
        user_id, email, name = result
        assert user_id == 1
        assert email == "test@example.com"

    def test_delete_record(self, temp_db):
        """Тест удаления записи"""
        conn = temp_db
        cursor = conn.cursor()

        # Добавляем пользователя
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            ("test@example.com", "hash123", "Test User")
        )
        conn.commit()

        # Добавляем запись
        cursor.execute("""
            INSERT INTO records 
            (user_id, weight, record_date) 
            VALUES (?, ?, ?)
        """, (1, 70.5, "2024-01-01"))
        conn.commit()

        record_id = cursor.lastrowid

        # Удаляем запись
        cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()

        # Проверяем, что записи больше нет
        cursor.execute("SELECT * FROM records WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        assert record is None

    def test_update_record(self, temp_db):
        """Тест обновления записи"""
        conn = temp_db
        cursor = conn.cursor()

        # Добавляем пользователя
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            ("test@example.com", "hash123", "Test User")
        )
        conn.commit()

        # Добавляем запись
        cursor.execute("""
            INSERT INTO records 
            (user_id, weight, notes, record_date) 
            VALUES (?, ?, ?, ?)
        """, (1, 70.5, "Старые заметки", "2024-01-01"))
        conn.commit()

        record_id = cursor.lastrowid

        # Обновляем запись
        cursor.execute("""
            UPDATE records
            SET weight = ?, notes = ?
            WHERE id = ?
        """, (72.0, "Новые заметки", record_id))
        conn.commit()

        # Проверяем обновление
        cursor.execute("SELECT * FROM records WHERE id = ?", (record_id,))
        record = cursor.fetchone()

        assert record[3] == 72.0  # вес
        assert record[8] == "Новые заметки"  # заметки

    def test_update_user(self, temp_db):
        """Тест обновления пользователя"""
        conn = temp_db
        cursor = conn.cursor()

        # Добавляем пользователя
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            ("old@example.com", "hash123", "Old Name")
        )
        conn.commit()

        # Обновляем пользователя
        cursor.execute("""
            UPDATE users
            SET name = ?, email = ?
            WHERE id = ?
        """, ("New Name", "new@example.com", 1))
        conn.commit()

        # Проверяем обновление
        cursor.execute("SELECT * FROM users WHERE id = ?", (1,))
        user = cursor.fetchone()

        assert user[3] == "New Name"  # name
        assert user[1] == "new@example.com"  # email