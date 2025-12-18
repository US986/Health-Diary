import json
import os
import uuid
from datetime import datetime, timedelta
import platform

# Импорт библиотеки Kivy для создания графического интерфейса
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.lang import Builder

# Импорт компонентов KivyMD (Material Design)
from kivymd.app import MDApp

# Импорт пользовательских модулей
from database import get_connection, init_db, insert_user_session, delete_user_session_db, \
    select_settings_by_user, insert_user_settings, update_user_settings, \
    select_user_session_by_device  # Подключение к базе данных
from windows.story import StoryWindow  # Окно истории записей
from windows.profile import ProfileScreen  # Окно профиля пользователя
from windows.settings import SettingsScreen  # Окно настроек
from windows.auth import RegistrationWindow
from windows.options import OptionsWindow

# Загружаем все KV-разметки один раз при запуске приложения
from kv import REG_KV, SETTINGS_KV, PROFILE_KV, STORY_KV, ADMIN_KV

import logging
import sys

import sys
from kivy.app import App

class HealthDiaryApp(MDApp):
    """
    Главный класс приложения "Дневник здоровья"

    Наследуется от MDApp (KivyMD) и управляет:
    1. Жизненным циклом приложения
    2. Управлением экранами (ScreenManager)
    3. Сессиями пользователей
    4. Настройками приложения
    5. Автоматическим входом
    """

    user_id = None  # ID текущего пользователя
    user_settings = {}  # Настройки пользователя
    store = None  # Локальное хранилище (JsonStore)
    is_guest = False  # Флаг гостевого режима
    guest_device_id = None  # ID устройства для гостя
    is_admin = False  # Флаг административных прав
    selected_user_id = None  # ID выбранного пользователя (для администратора)
    admin_dashboard = None  # Ссылка на панель администратора

    def __init__(self, **kwargs):
        """
        Инициализация приложения

        Создает локальное хранилище для данных устройства
        """
        super().__init__(**kwargs)
        self.store = JsonStore('user_data.json')  # Файл для локального хранения
        self.is_guest = False
        self.is_admin = False
        self.selected_user_id = None
        self.is_android = False

    def build(self):
        """
        Создает и возвращает корневой виджет приложения

        Инициализирует ScreenManager и все экраны приложения

        Returns:
            ScreenManager: Менеджер экранов приложения
        """
        # Сбрасываем тему к значениям по умолчанию
        self.reset_theme_to_default()

        self.is_android = (platform == 'android')

        # Создаем менеджер экранов
        sm = ScreenManager()

        # Добавляем все экраны приложения
        sm.add_widget(RegistrationWindow(name="registration"))
        sm.add_widget(OptionsWindow(name="options"))
        sm.add_widget(StoryWindow(name="story"))
        sm.add_widget(ProfileScreen(name="profile"))
        sm.add_widget(SettingsScreen(name="settings"))

        # Добавляем административные экраны
        from windows.admin import AdminDashboard, AdminUsersScreen, AdminRecordsScreen, AdminAuditScreen
        admin_dashboard = AdminDashboard(name="admin_dashboard")
        sm.add_widget(admin_dashboard)
        sm.add_widget(AdminUsersScreen(name="admin_users"))
        sm.add_widget(AdminRecordsScreen(name="admin_records"))
        sm.add_widget(AdminAuditScreen(name="admin_audit"))

        # Сохраняем ссылку на панель администратора
        self.admin_dashboard = admin_dashboard

        # Планируем попытку автоматического входа
        Clock.schedule_once(lambda dt: self.try_auto_login(sm), 0.1)

        return sm

    def reset_theme_to_default(self):
        """
        Сбрасывает тему приложения к значениям по умолчанию

        Используется при запуске и при выходе пользователя
        """
        try:
            self.theme_cls.primary_palette = "Blue"  # Основная цветовая палитра
            self.theme_cls.theme_style = "Light"  # Светлая тема
            print("Тема сброшена на значения по умолчанию")
        except Exception as e:
            print(f"Ошибка сброса темы: {e}")

    def apply_user_settings_immediately(self):
        """
        Применяет настройки пользователя (тему) немедленно

        Вызывается при смене экрана или изменении настроек
        """
        try:
            if not self.user_id or self.is_guest:
                # Если пользователь не авторизован или гость - тема по умолчанию
                print("Пользователь не авторизован или гость, применяется тема по умолчанию")
                self.reset_theme_to_default()
                return

            # Словарь соответствия цветовых настроек палитрам KivyMD
            theme_colors = {
                'blue': "Blue",
                'green': "Green",
                'purple': "Purple",
                'orange': "Orange",
                'red': "Red"
            }

            # Устанавливаем цветовую палитру
            theme_color = self.user_settings.get('theme_color', 'blue')
            if theme_color in theme_colors:
                self.theme_cls.primary_palette = theme_colors[theme_color]

            # Устанавливаем светлую/темную тему
            self.theme_cls.theme_style = "Dark" if self.user_settings.get('dark_mode', False) else "Light"

            print(
                f"Применены настройки пользователя: тема={theme_color}, "
                f"темный режим={self.user_settings.get('dark_mode', False)}"
            )

        except Exception as e:
            print(f"Ошибка применения настроек пользователя: {e}")

    def try_auto_login(self, sm):
        """
        Пытается выполнить автоматический вход пользователя

        Проверяет наличие активной сессии для устройства

        Args:
            sm (ScreenManager): Менеджер экранов приложения
        """
        if self.check_auto_login():
            print("Автоматический вход выполнен успешно")
            self.apply_user_settings_immediately()
            sm.current = "options"  # Переходим на главный экран
        else:
            sm.current = "registration"  # Переходим на экран авторизации
            print("Автоматический вход не выполнен")

    def get_device_id(self):
        """
        Генерирует или получает уникальный идентификатор устройства

        На Android использует ANDROID_ID, на других платформах - UUID

        Returns:
            str: Уникальный идентификатор устройства
        """
        # Для гостя используем специальный device_id
        if self.is_guest and self.guest_device_id:
            return self.guest_device_id

        try:
            # Проверяем, есть ли сохраненный device_id
            if self.store.exists('device'):
                return self.store.get('device')['device_id']

            # Генерация device_id в зависимости от платформы
            if platform == 'android':
                # На Android получаем ANDROID_ID
                from jnius import autoclass
                SettingsSecure = autoclass('android.provider.Settings$Secure')
                python_activity = autoclass('org.kivy.android.PythonActivity').mActivity
                android_id = SettingsSecure.getString(
                    python_activity.getContentResolver(),
                    SettingsSecure.ANDROID_ID
                )
                device_id = android_id if android_id else str(uuid.uuid4())
            else:
                # На других платформах генерируем UUID
                device_id = str(uuid.uuid4())

            # Сохраняем device_id в локальное хранилище
            self.store.put('device', device_id=device_id)
            return device_id

        except Exception as e:
            print(f"Ошибка получения device_id: {e}")
            # Резервный вариант: генерируем новый или используем сохраненный
            if not self.store.exists('device'):
                device_id = str(uuid.uuid4())
                self.store.put('device', device_id=device_id)
                return device_id
            return self.store.get('device')['device_id']

    def check_auto_login(self):
        """
        Проверяет возможность автоматического входа

        Ищет активную сессию для текущего устройства

        Returns:
            bool: True если найдена активная сессия, иначе False
        """
        # Для гостя не выполняем автоматический вход
        if self.is_guest:
            print("Гостевой режим - автоматический вход отключен")
            return False

        try:
            device_id = self.get_device_id()
            print(f"Проверяем автоматический вход для device_id: {device_id}")

            # Поиск активной сессии в базе данных
            conn = get_connection()
            result = select_user_session_by_device(conn, device_id)

            if result:
                # Найдена активная сессия
                user_id, email, name, is_admin = result
                print(f"Найдена активная сессия для пользователя: {email}")

                self.set_user_id(user_id)  # Устанавливаем ID пользователя
                self.is_guest = False  # Устанавливаем флаг "не гость"
                self.is_admin = bool(is_admin)  # Устанавливаем флаг администратора
                self.load_user_settings()  # Загружаем настройки

                return True
            else:
                print("Активная сессия не найдена")
                return False

        except Exception as e:
            print(f"Ошибка проверки автоматического входа: {e}")
            return False

    def save_user_session(self, user_id):
        """
        Сохраняет сессию пользователя для автоматического входа

        Args:
            user_id: ID пользователя
        """
        # Для гостя не сохраняем сессию
        if self.is_guest:
            print("Гостевой режим - сессия не сохраняется")
            return

        try:
            device_id = self.get_device_id()
            session_token = str(uuid.uuid4())  # Генерируем уникальный токен

            # Время истечения сессии (30 дней)
            expires_at = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

            # Сохранение сессии в базу данных
            conn = get_connection()
            insert_user_session(conn, user_id, device_id, session_token, expires_at)

            print(f"Сессия пользователя {user_id} сохранена для device_id: {device_id}")

        except Exception as e:
            print(f"Ошибка сохранения сессии: {e}")

    def delete_user_session(self):
        """
        Удаляет сессию пользователя

        Вызывается при выходе из аккаунта
        """
        # Для гостя не удаляем сессию
        if self.is_guest:
            print("Гостевой режим - сессия не удаляется")
            return

        try:
            device_id = self.get_device_id()

            conn = get_connection()
            delete_user_session_db(conn, device_id)

            print("Сессия пользователя удалена")

        except Exception as e:
            print(f"Ошибка удаления сессии: {e}")

    def load_user_settings(self):
        """
        Загружает настройки пользователя из базы данных

        Если настроек нет - создает настройки по умолчанию
        """
        # Для гостя не загружаем настройки
        if self.is_guest:
            print("Гостевой режим - настройки не загружаются")
            self.user_settings = self.get_default_settings()
            return

        try:
            if not self.user_id:
                print("Пользователь не авторизован, используются настройки по умолчанию")
                return

            # Получение настроек из базы данных
            conn = get_connection()
            result = select_settings_by_user(conn, self.user_id)

            if result and result[0]:
                # Настройки найдены - загружаем их
                self.user_settings = json.loads(result[0])
                print(f"Настройки пользователя загружены: {self.user_settings}")
            else:
                # Настроек нет - создаем по умолчанию
                self.user_settings = self.get_default_settings()
                print("Созданы настройки по умолчанию")
                self.save_user_settings()  # Сохраняем настройки по умолчанию

        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            self.user_settings = self.get_default_settings()

    def get_default_settings(self):
        """
        Возвращает настройки по умолчанию

        Returns:
            dict: Словарь с настройками по умолчанию
        """
        return {
            'theme_color': 'blue',  # Цветовая тема
            'dark_mode': False,  # Темный режим
            'daily_reminders': False,  # Ежедневные напоминания
            'reminder_time': '20:00',  # Время напоминаний
            'notification_sound': True,  # Звук уведомлений
            'date_format': 'dd-mm-yyyy',  # Формат даты
            'auto_export': False,  # Автоматический экспорт
            'auto_login': True,  # Автоматический вход
            'biometric_auth': False,  # Биометрическая аутентификация
            'auto_logout': False  # Автоматический выход
        }

    def save_user_settings(self):
        """
        Сохраняет настройки пользователя в базу данных
        """
        # Для гостя не сохраняем настройки
        if self.is_guest:
            print("Гостевой режим - настройки не сохраняются")
            return

        try:
            if not self.user_id:
                print("Не удалось сохранить настройки: пользователь не авторизован")
                return

            conn = get_connection()
            # Проверяем, есть ли уже настройки
            exists = select_settings_by_user(conn, self.user_id, check=True)

            if exists:
                # Обновляем существующие настройки
                update_user_settings(conn, self.user_id, json.dumps(self.user_settings))
            else:
                # Создаем новые настройки
                insert_user_settings(conn, self.user_id, json.dumps(self.user_settings))

            print("Настройки пользователя сохранены в базу данных")

        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")

    def get_user_id(self):
        """
        Возвращает ID текущего пользователя

        Returns:
            int or None: ID пользователя или None если не авторизован
        """
        return self.user_id

    def set_user_id(self, user_id):
        """
        Устанавливает ID текущего пользователя

        Args:
            user_id: ID пользователя или None для выхода
        """
        old_user_id = self.user_id
        self.user_id = user_id

        if user_id and user_id >= 0:
            # Пользователь авторизован - загружаем настройки
            Clock.schedule_once(lambda dt: self.load_user_settings(), 0.1)
        else:
            # Пользователь вышел или гость - сбрасываем тему
            self.reset_theme_to_default()
            self.is_admin = False  # Сбрасываем флаг администратора

            # Очищаем данные профиля на экране
            if old_user_id and hasattr(self, 'root'):
                for screen in self.root.screens:
                    if hasattr(screen, 'name') and screen.name == 'profile':
                        if hasattr(screen, 'clear_profile_data'):
                            screen.clear_profile_data()
                        break

    def logout_guest(self):
        """
        Выход из гостевого режима

        Очищает данные гостя и возвращает к экрану авторизации
        """
        if self.is_guest:
            print("Выход из гостевого режима")
            self.is_guest = False
            self.guest_device_id = None
            self.user_id = None
            self.user_settings = {}
            self.reset_theme_to_default()

            # Восстанавливаем нормальный режим базы данных
            from database import force_local_mode
            force_local_mode(False)

            # Переходим на экран авторизации
            if hasattr(self, 'root'):
                self.root.current = "registration"

# Точка входа в приложение
if __name__ == "__main__":
    """
    Запуск приложения "Дневник здоровья"

    Создает экземпляр главного класса и запускает приложение
    """

    init_db()

    # Загрузка всех KV-разметок
    Builder.load_string(REG_KV)
    Builder.load_string(SETTINGS_KV)
    Builder.load_string(PROFILE_KV)
    Builder.load_string(STORY_KV)
    Builder.load_string(ADMIN_KV)

    HealthDiaryApp().run()
