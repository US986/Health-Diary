"""
Интеграционные тесты
"""

import pytest
import json


class TestIntegration:
    """Интеграционные тесты"""

    def test_full_user_workflow(self, temp_db):
        """Тест полного workflow пользователя"""
        conn = temp_db
        cursor = conn.cursor()

        # 1. Регистрация пользователя
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            ("test@example.com", "hash123", "Test User")
        )
        conn.commit()

        # 2. Проверяем, что пользователь создан
        cursor.execute("SELECT * FROM users WHERE email = ?", ("test@example.com",))
        user = cursor.fetchone()
        assert user is not None
        assert user[1] == "test@example.com"

        user_id = user[0]

        # 3. Добавляем настройки пользователя
        settings = {
            'theme_color': 'blue',
            'dark_mode': False,
            'date_format': 'dd-mm-yyyy'
        }

        cursor.execute(
            "INSERT INTO user_settings (user_id, settings) VALUES (?, ?)",
            (user_id, json.dumps(settings))
        )
        conn.commit()

        # 4. Проверяем настройки
        cursor.execute("SELECT settings FROM user_settings WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        assert result is not None
        loaded_settings = json.loads(result[0])
        assert loaded_settings['theme_color'] == 'blue'

        # 5. Добавляем запись о здоровье
        cursor.execute("""
            INSERT INTO records 
            (user_id, weight, pressure_systolic, pressure_diastolic, 
             pulse, temperature, notes, record_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, 70.5, 120, 80, 75, 36.6, "Тестовая запись", "2024-01-01 10:00:00"))
        conn.commit()

        # 6. Проверяем, что запись добавлена
        cursor.execute("SELECT * FROM records WHERE user_id = ?", (user_id,))
        records = cursor.fetchall()
        assert len(records) == 1

        record = records[0]
        assert record[3] == 70.5  # вес

        # 7. Обновляем запись
        cursor.execute("""
            UPDATE records
            SET weight = ?, notes = ?
            WHERE id = ?
        """, (72.0, "Обновленная запись", record[0]))
        conn.commit()

        # 8. Проверяем обновление
        cursor.execute("SELECT * FROM records WHERE id = ?", (record[0],))
        updated_record = cursor.fetchone()
        assert updated_record[3] == 72.0

        # 9. Удаляем запись
        cursor.execute("DELETE FROM records WHERE id = ?", (record[0],))
        conn.commit()

        # 10. Проверяем, что записи больше нет
        cursor.execute("SELECT * FROM records WHERE id = ?", (record[0],))
        deleted_record = cursor.fetchone()
        assert deleted_record is None

    def test_user_session_workflow(self, temp_db):
        """Тест workflow сессии пользователя"""
        conn = temp_db
        cursor = conn.cursor()

        # 1. Добавляем пользователя
        cursor.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            ("session_test@example.com", "hash123", "Session User")
        )
        conn.commit()

        user_id = cursor.lastrowid

        # 2. Добавляем сессию
        cursor.execute("""
            INSERT INTO user_sessions 
            (user_id, device_id, session_token, expires_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, "device123", "token123", "2024-12-31 23:59:59"))
        conn.commit()

        # 3. Проверяем сессию
        cursor.execute("""
            SELECT us.user_id, u.email, u.name 
            FROM user_sessions us
            JOIN users u ON us.user_id = u.id
            WHERE us.device_id = ?
        """, ("device123",))
        session = cursor.fetchone()

        assert session is not None
        assert session[0] == user_id

        # 4. Удаляем сессию
        cursor.execute("DELETE FROM user_sessions WHERE device_id = ?", ("device123",))
        conn.commit()

        # 5. Проверяем, что сессия удалена
        cursor.execute("SELECT * FROM user_sessions WHERE device_id = ?", ("device123",))
        deleted_session = cursor.fetchone()
        assert deleted_session is None
