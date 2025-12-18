"""
Конфигурация тестов для pytest
"""

import pytest
import tempfile
import os
import sys
import sqlite3
import json
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Мокаем Kivy и KivyMD, чтобы избежать их импорта
import unittest.mock as mock

# Мокаем KivyMD перед любым импортом
sys.modules['kivymd'] = mock.MagicMock()
sys.modules['kivymd.app'] = mock.MagicMock()
sys.modules['kivymd.uix'] = mock.MagicMock()

# Мокаем Kivy
sys.modules['kivy'] = mock.MagicMock()
sys.modules['kivy.app'] = mock.MagicMock()
sys.modules['kivy.uix'] = mock.MagicMock()

# Мокаем plyer
sys.modules['plyer'] = mock.MagicMock()


@pytest.fixture
def temp_db():
    """Фикстура для временной базы данных SQLite"""
    temp_db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db_path = temp_db_file.name
    temp_db_file.close()

    # Создаем соединение с временной базой данных
    conn = sqlite3.connect(temp_db_path)

    # Инициализируем схему базы данных
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

    yield conn

    # Закрываем соединение и удаляем временный файл
    conn.close()
    os.unlink(temp_db_path)


@pytest.fixture
def mock_app():
    """Фикстура для мок-объекта приложения"""
    class MockApp:
        def __init__(self):
            self.user_id = 1
            self.user_settings = {}
            self.is_guest = False
            self.is_admin = False
            self.selected_user_id = None

        def get_user_id(self):
            return self.user_id

        def set_user_id(self, user_id):
            self.user_id = user_id

    return MockApp()


@pytest.fixture
def sample_user_data():
    """Фикстура с тестовыми данными пользователя"""
    return {
        'email': 'test@example.com',
        'name': 'Тестовый Пользователь',
        'password': 'Password123!',
        'user_id': 1
    }


@pytest.fixture
def sample_health_record():
    """Фикстура с тестовыми данными записи здоровья"""
    return {
        'weight': 70.5,
        'pressure_systolic': 120,
        'pressure_diastolic': 80,
        'pulse': 75,
        'temperature': 36.6,
        'notes': 'Тестовая запись'
    }