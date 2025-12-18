"""
Утилиты для проверки прав администратора
"""

from kivymd.app import MDApp


def is_admin():
    """
    Проверяет, является ли текущий пользователь администратором

    text
    Returns:
        bool: True если пользователь администратор, иначе False
    """

    app = MDApp.get_running_app()
    return getattr(app, 'is_admin', False)


def require_admin(func):
    """
    Декоратор для проверки прав администратора перед выполнением функции

    Args:
        func: Функция для выполнения

    Returns:
        Обернутая функция
    """

    def wrapper(*args, **kwargs):
        if not is_admin():
            from utils.ui import UIUtils
            UIUtils.show_message("Доступ запрещен", "Только администраторы могут выполнять это действие")
            return None
        return func(*args, **kwargs)


    return wrapper