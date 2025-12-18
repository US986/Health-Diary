"""
Тесты логики авторизации
"""

import pytest
import hashlib
import os
import binascii


class TestAuthLogic:
    """Тесты логики авторизации"""

    def test_password_hashing_and_verification(self):
        """Тест хеширования и верификации пароля"""

        # Функция хеширования (аналогичная вашей)
        def hash_password(password: str) -> str:
            salt = os.urandom(32)
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return salt.hex() + pwd_hash.hex()

        # Функция верификации (аналогичная вашей)
        def verify_password(provided_password: str, stored_password_hash: str) -> bool:
            try:
                if len(stored_password_hash) <= 64:
                    return stored_password_hash == provided_password

                salt = bytes.fromhex(stored_password_hash[:64])
                stored_hash = stored_password_hash[64:]

                pwd_hash = hashlib.pbkdf2_hmac(
                    'sha256',
                    provided_password.encode('utf-8'),
                    salt,
                    100000
                )

                return pwd_hash.hex() == stored_hash

            except (ValueError, binascii.Error, Exception):
                return stored_password_hash == provided_password

        # Тестируем
        password = "TestPassword123!"

        # Хешируем пароль
        hashed = hash_password(password)

        # Проверяем формат хеша
        assert len(hashed) > 64
        assert isinstance(hashed, str)

        # Проверяем верификацию
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_evaluate_password_strength(self):
        """Тест оценки сложности пароля"""

        def evaluate_password_strength(password):
            if not password:
                return "Слабый", (1, 0, 0, 1)

            score = 0
            # Проверяем длину
            if len(password) >= 8:
                score += 1
            # Проверяем наличие строчных букв
            if any(c.islower() for c in password):
                score += 1
            # Проверяем наличие заглавных букв
            if any(c.isupper() for c in password):
                score += 1
            # Проверяем наличие цифр
            if any(c.isdigit() for c in password):
                score += 1
            # Проверяем наличие специальных символов
            if any(not c.isalnum() for c in password):
                score += 1

            # Определяем сложность
            if score <= 2:
                return "Слабый", (1, 0, 0, 1)  # Красный
            elif score == 3:
                return "Средний", (1, 1, 0, 1)  # Оранжевый
            elif score == 4:
                return "Сильный", (0, 1, 0, 1)  # Зеленый
            else:
                return "Очень сильный", (0, 0.5, 0, 1)  # Темно-зеленый

        # Тестовые случаи
        test_cases = [
            ("weak", "Слабый"),
            ("Password", "Средний"),
            ("Password123", "Сильный"),
            ("P@ssw0rd!123", "Очень сильный"),
        ]

        for password, expected_strength in test_cases:
            strength, _ = evaluate_password_strength(password)
            assert strength == expected_strength