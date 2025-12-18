"""
Скрипт для создания учетной записи администратора
"""

import hashlib
import os
import sys

sys.path.append('.')

from database import get_connection, insert_user, select_user_by_email


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
    confirm_password = "root"

    # Проверка пароля
    if password != confirm_password:
        print("Ошибка: Пароли не совпадают!")
        return

    if len(password) < 6:
        print("Ошибка: Пароль должен быть не менее 6 символов!")
        return


    # Хеширование пароля
    def hash_password(password: str) -> str:
        salt = os.urandom(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + pwd_hash.hex()


    password_hash = hash_password(password)

    try:
        # Подключение к базе данных
        conn = get_connection(path="../database.db")

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

if __name__ == "__main__":
    create_admin_user()
