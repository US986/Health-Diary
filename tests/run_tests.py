"""
Скрипт для запуска всех тестов
"""

import sys
import os
import pytest


def main():
    """Главная функция запуска тестов"""
    print("=" * 60)
    print("Запуск тестов для приложения 'Дневник здоровья'")
    print("=" * 60)

    # Добавляем текущую директорию в PYTHONPATH
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

    # Определяем тестовые файлы
    test_files = [
        "tests/test_database.py",
        "tests/test_rules.py",
        "tests/test_auth_logic.py",
        "tests/test_options_logic.py",
        "tests/test_story_logic.py",
        "tests/test_integration.py"
    ]

    # Запускаем тесты
    print("\nЗапуск тестов базы данных...")
    result = pytest.main([
        "tests/test_database.py",
        "-v",
        "--tb=short"
    ])

    print("\nЗапуск тестов правил валидации...")
    result |= pytest.main([
        "tests/test_rules.py",
        "-v",
        "--tb=short"
    ])

    print("\nЗапуск тестов логики авторизации...")
    result |= pytest.main([
        "tests/test_auth_logic.py",
        "-v",
        "--tb=short"
    ])

    print("\nЗапуск тестов логики ввода данных...")
    result |= pytest.main([
        "tests/test_options_logic.py",
        "-v",
        "--tb=short"
    ])

    print("\nЗапуск тестов логики истории...")
    result |= pytest.main([
        "tests/test_story_logic.py",
        "-v",
        "--tb=short"
    ])

    print("\nЗапуск интеграционных тестов...")
    result |= pytest.main([
        "tests/test_integration.py",
        "-v",
        "--tb=short"
    ])

    print("\n" + "=" * 60)
    if result == 0:
        print("✅ Все тесты пройдены успешно!")
    else:
        print("❌ Некоторые тесты не пройдены")
    print("=" * 60)

    return result


if __name__ == "__main__":
    sys.exit(main())