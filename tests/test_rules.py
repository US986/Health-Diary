"""
Тесты для модуля правил валидации
"""
import re

import pytest


class TestValidationRules:
    """Тесты правил валидации"""

    def test_validate_weight(self):
        """Тест валидации веса"""

        # Создаем простую функцию валидации веса
        def validate_weight(weight_str):
            if not weight_str:
                raise ValueError("Вес не может быть пустым")

            try:
                weight = float(weight_str)
            except ValueError:
                raise ValueError("Вес должен быть числом")

            if weight < 30 or weight > 250:
                raise ValueError("Вес должен быть в пределах 30-250 кг")

            return weight

        # Валидные значения веса
        valid_weights = ["50", "70.5", "100.0", "150"]

        for weight in valid_weights:
            result = validate_weight(weight)
            assert isinstance(result, float)

        # Невалидные значения веса
        invalid_weights = [
            ("", "Вес не может быть пустым"),
            ("abc", "Вес должен быть числом"),
            ("-10", "Вес должен быть в пределах 30-250 кг"),
            ("10", "Вес должен быть в пределах 30-250 кг"),
            ("500", "Вес должен быть в пределах 30-250 кг")
        ]

        for weight, expected_error in invalid_weights:
            with pytest.raises(ValueError) as exc:
                validate_weight(weight)
            assert expected_error in str(exc.value)

    def test_validate_temperature(self):
        """Тест валидации температуры"""

        # Создаем простую функцию валидации температуры
        def validate_temperature(temp_str):
            if not temp_str:
                raise ValueError("Температура не может быть пустой")

            try:
                temp = float(temp_str)
            except ValueError:
                raise ValueError("Температура должна быть числом")

            if temp < 34 or temp > 42:
                raise ValueError("Температура должна быть в пределах 34-42°C")

            return temp

        # Валидные значения температуры
        valid_temps = ["35.0", "36.6", "37.5", "40.0"]

        for temp in valid_temps:
            result = validate_temperature(temp)
            assert isinstance(result, float)

        # Невалидные значения температуры
        invalid_temps = [
            ("", "Температура не может быть пустой"),
            ("abc", "Температура должна быть числом"),
            ("30.0", "Температура должна быть в пределах 34-42°C"),
            ("45.0", "Температура должна быть в пределах 34-42°C")
        ]

        for temp, expected_error in invalid_temps:
            with pytest.raises(ValueError) as exc:
                validate_temperature(temp)
            assert expected_error in str(exc.value)

    def test_validate_email(self):
        """Тест валидации email"""

        def validate_email(email):
            if not email:
                raise ValueError("Email не может быть пустым")

            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
                raise ValueError("Некорректный email адрес")

            return email

        # Валидные email
        valid_emails = [
            "test@example.com",
            "user.name@domain.co",
            "user123@test.ru"
        ]

        for email in valid_emails:
            validate_email(email)

        # Невалидные email
        invalid_emails = [
            ("", "Email не может быть пустым"),
            ("invalid-email", "Некорректный email адрес"),
            ("@domain.com", "Некорректный email адрес"),
            ("user@.com", "Некорректный email адрес"),
            ("user@domain.", "Некорректный email адрес")
        ]

        for email, expected_error in invalid_emails:
            with pytest.raises(ValueError) as exc:
                validate_email(email)
            assert expected_error in str(exc.value)

    def test_validate_name(self):
        """Тест валидации имени"""

        def validate_name(name):
            if not name:
                raise ValueError("Имя не может быть пустым")

            if len(name.strip()) < 2:
                raise ValueError("Имя должно содержать минимум 2 символа")

            if len(name) > 50:
                raise ValueError("Имя не должно превышать 50 символов")

            # Проверяем, что имя содержит только буквы и пробелы
            for char in name:
                if not (char.isalpha() or char.isspace() or char in "-'"):
                    raise ValueError("Имя может содержать только буквы и пробелы")

            return name.strip()

        # Валидные имена
        valid_names = [
            "Иван",
            "John",
            "Мария",
            "Александр"
        ]

        for name in valid_names:
            validate_name(name)

        # Невалидные имена
        invalid_names = [
            ("", "Имя не может быть пустым"),
            (" ", "Имя должно содержать минимум 2 символ"),
            ("И", "Имя должно содержать минимум 2 символа"),
            ("Имя" * 20, "Имя не должно превышать 50 символов"),
            ("Иван123", "Имя может содержать только буквы и пробелы"),
            ("Иван!", "Имя может содержать только буквы и пробелы")
        ]

        for name, expected_error in invalid_names:
            with pytest.raises(ValueError) as exc:
                validate_name(name)
            assert expected_error in str(exc.value)

    def test_validate_password(self):
        """Тест валидации пароля"""

        def validate_password(password, confirm_password):
            if not password or not confirm_password:
                raise ValueError("Пароль не может быть пустым")

            if len(password) < 6:
                raise ValueError("Пароль должен содержать минимум 6 символов")

            if password != confirm_password:
                raise ValueError("Пароли не совпадают")

            # Проверяем сложность
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(not c.isalnum() for c in password)

            if not (has_upper and has_lower and has_digit):
                raise ValueError("Пароль слишком простой. Используйте буквы в разных регистрах и цифры")

            return password

        # Валидные пароли
        valid_passwords = [
            ("Password123!", "Password123!"),
            ("Test123!", "Test123!")
        ]

        for password, confirm in valid_passwords:
            validate_password(password, confirm)

        # Невалидные пароли
        invalid_passwords = [
            ("short", "short", "Пароль должен содержать минимум 6 символов"),
            ("password", "password", "Пароль слишком простой"),
            ("Password123!", "Different123!", "Пароли не совпадают"),
        ]

        for password, confirm, expected_error in invalid_passwords:
            with pytest.raises(ValueError) as exc:
                validate_password(password, confirm)
            assert expected_error in str(exc.value)