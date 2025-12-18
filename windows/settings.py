"""
Модуль настроек приложения "Дневник здоровья"
Содержит экран настроек с различными параметрами приложения
"""

# Стандартные библиотеки Python
import json
import uuid
import hashlib
import os
import binascii
from datetime import datetime, timedelta, time
import platform

# Библиотеки Kivy для создания GUI
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.app import App
from kivy.storage.jsonstore import JsonStore
from kivy.uix.image import Image
from kivy.properties import StringProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout

# Компоненты KivyMD (Material Design)
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFloatingActionButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDTimePicker
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.list import OneLineListItem, TwoLineListItem

# Пользовательские модули

from kv import PROFILE_KV, SETTINGS_KV

from database import get_connection, insert_user_session, delete_user_session_db, select_settings_by_user, \
    update_user_settings, insert_user_settings

# Попытка импорта PIL для работы с изображениями
try:
    from PIL import Image as PILImage
    from PIL import ImageDraw

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    PILImage = None
    ImageDraw = None

class SettingsScreen(Screen):
    """
    Экран настроек приложения

    Позволяет пользователю настраивать:
    1. Внешний вид (цветовая тема, темный режим)
    2. Уведомления и напоминания
    3. Экспорт данных
    4. Безопасность и вход
    """

    dialog = None  # Текущее диалоговое окно
    theme_menu = None  # Меню выбора цветовой темы
    date_format_menu = None  # Меню выбора формата даты
    current_settings = {}  # Текущие настройки пользователя
    _settings_loaded = False  # Флаг загрузки настроек
    _pending_changes = False  # Флаг наличия несохраненных изменений

    # Свойства для отображения текста (синхронизированы с UI)
    theme_display = StringProperty('Синий')
    date_format_display = StringProperty('ДД-ММ-ГГГГ')
    reminder_time_display = StringProperty('20:00')

    def __init__(self, **kwargs):
        """
        Инициализация экрана настроек

        Создает меню и планирует предзагрузку настроек
        """
        super().__init__(**kwargs)
        self.setup_theme_menu()  # Настраиваем меню выбора темы
        self.setup_date_format_menu()  # Настраиваем меню выбора формата даты
        Clock.schedule_once(self._preload_settings, 0.5)  # Отложенная загрузка настроек

    def _preload_settings(self, dt):
        """
        Предварительная загрузка настроек пользователя

        Загружает настройки из приложения или базы данных
        """
        try:
            app = MDApp.get_running_app()
            user_id = app.get_user_id() if hasattr(app, 'get_user_id') else None

            if user_id:
                # Проверяем, есть ли настройки в объекте приложения
                if hasattr(app, 'user_settings') and app.user_settings:
                    self.current_settings = app.user_settings.copy()
                    self._settings_loaded = True
                    # Применяем настройки к UI с небольшой задержкой
                    Clock.schedule_once(lambda dt: self._apply_ui_settings(), 0.1)
                else:
                    # Если нет - загружаем из базы данных
                    self._load_settings_from_db()
        except Exception as e:
            print(f"Ошибка предзагрузки настроек: {e}")

    def _load_settings_from_db(self):
        """
        Загружает настройки пользователя из базы данных

        Если настроек нет - создает настройки по умолчанию
        """
        try:
            app = MDApp.get_running_app()
            user_id = app.get_user_id() if hasattr(app, 'get_user_id') else None

            if not user_id:
                return

            # Загружаем настройки из базы данных
            conn = get_connection()
            result = select_settings_by_user(conn, user_id)

            if result and result[0]:
                # Настройки найдены - загружаем их
                self.current_settings = json.loads(result[0])
                # Копируем в объект приложения
                if hasattr(app, 'user_settings'):
                    app.user_settings = self.current_settings.copy()
            else:
                # Настроек нет - создаем по умолчанию
                self.current_settings = self.get_default_settings()
                self._save_settings_to_db()  # Сохраняем настройки по умолчанию

            self._settings_loaded = True
            # Применяем настройки к UI
            Clock.schedule_once(lambda dt: self._apply_ui_settings(), 0.1)

        except Exception as e:
            print(f"Ошибка загрузки настроек из БД: {e}")
            self.current_settings = self.get_default_settings()
            self._settings_loaded = True

    def _apply_ui_settings(self):
        """
        Применяет текущие настройки к элементам UI

        Устанавливает значения переключателей и текстовых полей
        """
        if not hasattr(self, 'ids'):
            # Если UI еще не загружен, планируем повторную попытку
            Clock.schedule_once(lambda dt: self._apply_ui_settings(), 0.1)
            return

        try:
            # Устанавливаем значения всех переключателей
            self.ids.dark_mode_switch.active = self.current_settings.get('dark_mode', False)
            self.ids.daily_reminders_switch.active = self.current_settings.get('daily_reminders', False)
            self.ids.notification_sound_switch.active = self.current_settings.get('notification_sound', True)
            self.ids.auto_export_switch.active = self.current_settings.get('auto_export', False)
            self.ids.auto_login_switch.active = self.current_settings.get('auto_login', True)
            self.ids.auto_logout_switch.active = self.current_settings.get('auto_logout', False)

            # Обновляем текстовые поля
            self.update_display_texts()

        except Exception as e:
            print(f"Ошибка применения настроек к UI: {e}")

    def on_pre_enter(self):
        """
        Метод, вызываемый перед переходом на экран настроек

        Загружает настройки, если они еще не загружены
        """
        if not self._settings_loaded:
            self._load_settings_from_db()
        else:
            # Применяем настройки к UI
            Clock.schedule_once(lambda dt: self._apply_ui_settings(), 0.1)

    def setup_theme_menu(self):
        """
        Настраивает меню выбора цветовой темы

        Создает список доступных тем с обработчиками выбора
        """
        theme_items = [
            {
                "text": "Синий (по умолчанию)",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="blue": self.set_theme_color(x)
            },
            {
                "text": "Зеленый",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="green": self.set_theme_color(x)
            },
            {
                "text": "Фиолетовый",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="purple": self.set_theme_color(x)
            },
            {
                "text": "Оранжевый",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="orange": self.set_theme_color(x)
            },
            {
                "text": "Красный",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="red": self.set_theme_color(x)
            },
        ]

        # Создаем меню с перечисленными элементами
        self.theme_menu = MDDropdownMenu(
            caller=None,  # Caller будет установлен при открытии
            items=theme_items,
            width_mult=4,  # Ширина меню (4 * стандартная ширина)
        )

    def setup_date_format_menu(self):
        """
        Настраивает меню выбора формата даты

        Создает список доступных форматов даты
        """
        date_format_items = [
            {
                "text": "ДД-ММ-ГГГГ (Европейский)",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="dd-mm-yyyy": self.set_date_format(x)
            },
            {
                "text": "ММ-ДД-ГГГГ (Американский)",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="mm-dd-yyyy": self.set_date_format(x)
            },
            {
                "text": "ГГГГ-ММ-ДД (Международный)",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="yyyy-mm-dd": self.set_date_format(x)
            },
        ]

        # Создаем меню для выбора формата даты
        self.date_format_menu = MDDropdownMenu(
            caller=None,
            items=date_format_items,
            width_mult=4,
        )

    def update_display_texts(self):
        """
        Обновляет текстовые поля отображения настроек

        Синхронизирует свойства StringProperty с текущими значениями настроек
        """
        self.theme_display = self.get_theme_display_name()
        self.date_format_display = self.get_date_format_display()
        self.reminder_time_display = self.get_reminder_time_display()

    def get_theme_display_name(self):
        """
        Возвращает отображаемое имя текущей цветовой темы

        Returns:
            str: Человекочитаемое название темы
        """
        theme_names = {
            'blue': 'Синий',
            'green': 'Зеленый',
            'purple': 'Фиолетовый',
            'orange': 'Оранжевый',
            'red': 'Красный'
        }
        return theme_names.get(self.current_settings.get('theme_color', 'blue'), 'Синий')

    def get_reminder_time_display(self):
        """
        Возвращает отображаемое время напоминания

        Returns:
            str: Время в формате "ЧЧ:ММ"
        """
        return self.current_settings.get('reminder_time', '20:00')

    def get_date_format_display(self):
        """
        Возвращает отображаемое название формата даты

        Returns:
            str: Человекочитаемое название формата
        """
        format_names = {
            'dd-mm-yyyy': 'ДД-ММ-ГГГГ',
            'mm-dd-yyyy': 'ММ-ДД-ГГГГ',
            'yyyy-mm-dd': 'ГГГГ-ММ-ДД'
        }
        return format_names.get(
            self.current_settings.get('date_format', 'dd-mm-yyyy'),
            'ДД-ММ-ГГГГ'
        )

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
            'auto_logout': False  # Автоматический выход
        }

    def open_theme_menu(self, button):
        """
        Открывает меню выбора цветовой темы

        Args:
            button: Кнопка, которая вызвала меню
        """
        self.theme_menu.caller = button  # Устанавливаем кнопку-вызыватель
        self.theme_menu.open()  # Открываем меню

    def set_theme_color(self, color):
        """
        Устанавливает выбранную цветовую тему

        Args:
            color (str): Код цвета ('blue', 'green', 'purple', 'orange', 'red')
        """
        self.current_settings['theme_color'] = color  # Сохраняем выбор
        self.theme_menu.dismiss()  # Закрываем меню
        self.update_display_texts()  # Обновляем отображение
        self.apply_app_settings()  # Применяем настройки к приложению
        self._pending_changes = True  # Помечаем изменения как несохраненные

    def on_dark_mode_change(self, instance, value):
        """
        Обработчик изменения переключателя темного режима

        Args:
            instance: Объект переключателя
            value (bool): Новое значение переключателя
        """
        self.current_settings['dark_mode'] = value  # Сохраняем настройку
        self.apply_app_settings()  # Применяем настройки к приложению
        self._pending_changes = True  # Помечаем изменения как несохраненные

    def on_daily_reminders_change(self, instance, value):
        """
        Обработчик изменения переключателя ежедневных напоминаний

        Args:
            instance: Объект переключателя
            value (bool): Новое значение переключателя
        """
        self.current_settings['daily_reminders'] = value
        self._pending_changes = True

    def on_notification_sound_change(self, instance, value):
        """
        Обработчик изменения переключателя звука уведомлений

        Args:
            instance: Объект переключателя
            value (bool): Новое значение переключателя
        """
        self.current_settings['notification_sound'] = value
        self._pending_changes = True

    def on_auto_export_change(self, instance, value):
        """
        Обработчик изменения переключателя автоматического экспорта

        Args:
            instance: Объект переключателя
            value (bool): Новое значение переключателя
        """
        self.current_settings['auto_export'] = value
        self._pending_changes = True

    def on_auto_login_change(self, instance, value):
        """
        Обработчик изменения переключателя автоматического входа

        Args:
            instance: Объект переключателя
            value (bool): Новое значение переключателя
        """
        self.current_settings['auto_login'] = value
        self._pending_changes = True

    def on_auto_logout_change(self, instance, value):
        """
        Обработчик изменения переключателя автоматического выхода

        Args:
            instance: Объект переключателя
            value (bool): Новое значение переключателя
        """
        self.current_settings['auto_logout'] = value
        self._pending_changes = True

    def open_time_picker(self):
        """
        Открывает пикер выбора времени для напоминаний
        """
        # Получаем текущее время напоминания
        current_time = self.current_settings.get('reminder_time', '20:00')

        try:
            # Парсим время из строки
            hours, minutes = map(int, current_time.split(':'))
            # Создаем пикер времени
            time_picker = MDTimePicker()
            time_picker.set_time(time(hours, minutes))  # Устанавливаем текущее время
            time_picker.bind(time=self.on_reminder_time_set)  # Привязываем обработчик
            time_picker.open()  # Открываем пикер
        except:
            # В случае ошибки открываем пикер со временем по умолчанию
            time_picker = MDTimePicker()
            time_picker.bind(time=self.on_reminder_time_set)
            time_picker.open()

    def on_reminder_time_set(self, instance, time_value):
        """
        Обработчик выбора времени напоминания

        Args:
            instance: Объект пикера времени
            time_value (time): Выбранное время
        """
        # Сохраняем время в формате "ЧЧ:ММ"
        self.current_settings['reminder_time'] = time_value.strftime("%H:%M")
        self.update_display_texts()  # Обновляем отображение
        self._pending_changes = True  # Помечаем изменения как несохраненные

    def open_date_format_menu(self, button):
        """
        Открывает меню выбора формата даты

        Args:
            button: Кнопка, которая вызвала меню
        """
        self.date_format_menu.caller = button
        self.date_format_menu.open()

    def set_date_format(self, date_format):
        """
        Устанавливает выбранный формат даты

        Args:
            date_format (str): Код формата даты
        """
        self.current_settings['date_format'] = date_format
        self.date_format_menu.dismiss()  # Закрываем меню
        self.update_display_texts()  # Обновляем отображение
        self._pending_changes = True  # Помечаем изменения как несохраненные

    def apply_app_settings(self):
        """
        Применяет текущие настройки к приложению

        Изменяет тему и стиль приложения в реальном времени
        """
        try:
            app = MDApp.get_running_app()

            # Словарь соответствия кодов цветов палитрам KivyMD
            theme_colors = {
                'blue': "Blue",
                'green': "Green",
                'purple': "Purple",
                'orange': "Orange",
                'red': "Red"
            }

            # Устанавливаем цветовую палитру
            theme_color = self.current_settings.get('theme_color', 'blue')
            if theme_color in theme_colors:
                app.theme_cls.primary_palette = theme_colors[theme_color]

            # Устанавливаем светлую/темную тему
            app.theme_cls.theme_style = "Dark" if self.current_settings.get('dark_mode', False) else "Light"

        except Exception as e:
            print(f"Ошибка применения настроек приложения: {e}")

    def save_all_settings(self):
        """
        Сохраняет все настройки в базу данных

        Обновляет значения из UI, сохраняет в БД и применяет изменения
        """
        try:
            # Собираем текущие значения из UI элементов
            if hasattr(self, 'ids'):
                self.current_settings['dark_mode'] = self.ids.dark_mode_switch.active
                self.current_settings['daily_reminders'] = self.ids.daily_reminders_switch.active
                self.current_settings['notification_sound'] = self.ids.notification_sound_switch.active
                self.current_settings['auto_export'] = self.ids.auto_export_switch.active
                self.current_settings['auto_login'] = self.ids.auto_login_switch.active
                self.current_settings['auto_logout'] = self.ids.auto_logout_switch.active

            # Сохраняем настройки в базу данных
            self._save_settings_to_db()

            # Применяем настройки к приложению
            self.apply_app_settings()

            # Обрабатываем настройки сессии
            if not self.current_settings.get('auto_login', True):
                # Если отключен автоматический вход - удаляем сессию
                self.delete_user_session()
            else:
                # Если включен - создаем/обновляем сессию
                self.create_user_session()

            # Сбрасываем флаг несохраненных изменений
            self._pending_changes = False

            # Показываем сообщение об успехе
            self.show_message("Успех", "Настройки успешно сохранены!")

        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            self.show_message("Ошибка", f"Не удалось сохранить настройки: {str(e)}")

    def _save_settings_to_db(self):
        """
        Сохраняет настройки в базу данных

        Обновляет существующие настройки или создает новые
        """
        try:
            app = MDApp.get_running_app()
            user_id = app.get_user_id() if hasattr(app, 'get_user_id') else None

            if not user_id:
                return

            conn = get_connection()
            # Проверяем, есть ли уже настройки у пользователя
            exists = select_settings_by_user(conn, user_id, check=True)

            if exists:
                # Обновляем существующие настройки
                update_user_settings(conn, user_id, json.dumps(self.current_settings))
            else:
                # Создаем новые настройки
                insert_user_settings(conn, user_id, json.dumps(self.current_settings))

            # Обновляем настройки в объекте приложения
            if hasattr(app, 'user_settings'):
                app.user_settings = self.current_settings.copy()

        except Exception as e:
            print(f"Ошибка сохранения настроек в БД: {e}")
            raise e

    def get_device_id(self):
        """
        Генерирует или получает уникальный идентификатор устройства

        На Android использует ANDROID_ID, на других платформах - UUID

        Returns:
            str: Уникальный идентификатор устройства
        """
        try:
            if platform == 'android':
                # На Android получаем ANDROID_ID
                from jnius import autoclass
                SettingsSecure = autoclass('android.provider.Settings$Secure')
                python_activity = autoclass('org.kivy.android.PythonActivity').mActivity
                android_id = SettingsSecure.getString(
                    python_activity.getContentResolver(),
                    SettingsSecure.ANDROID_ID
                )
                return android_id if android_id else str(uuid.uuid4())
            else:
                # На других платформах генерируем UUID
                return str(uuid.uuid4())
        except Exception as e:
            # В случае ошибки генерируем UUID
            return str(uuid.uuid4())

    def create_user_session(self):
        """
        Создает или обновляет сессию пользователя для автоматического входа
        """
        try:
            app = MDApp.get_running_app()
            user_id = app.get_user_id() if hasattr(app, 'get_user_id') else None

            if not user_id:
                return

            # Получаем ID устройства
            device_id = self.get_device_id()
            # Генерируем уникальный токен сессии
            session_token = str(uuid.uuid4())
            # Устанавливаем срок действия сессии (30 дней)
            expires_at = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

            # Сохраняем сессию в базу данных
            conn = get_connection()
            insert_user_session(conn, user_id, device_id, session_token, expires_at)

        except Exception as e:
            print(f"Ошибка создания сессии: {e}")

    def delete_user_session(self):
        """
        Удаляет сессию пользователя

        Используется при отключении автоматического входа
        """
        try:
            app = MDApp.get_running_app()
            user_id = app.get_user_id() if hasattr(app, 'get_user_id') else None

            if not user_id:
                return

            # Получаем ID устройства
            device_id = self.get_device_id()

            # Удаляем сессию из базы данных
            conn = get_connection()

            delete_user_session_db(conn, device_id, user_id)

        except Exception as e:
            print(f"Ошибка удаления сессии: {e}")

    def reset_to_default(self):
        """
        Сбрасывает все настройки к значениям по умолчанию

        Обновляет текущие настройки и применяет их к UI
        """
        self.current_settings = self.get_default_settings()  # Сбрасываем настройки
        self._apply_ui_settings()  # Применяем настройки к UI
        self.apply_app_settings()  # Применяем настройки к приложению
        self._pending_changes = True  # Помечаем изменения как несохраненные
        self.show_message("Успех", "Настройки сброшены к значениям по умолчанию. Не забудьте сохранить!")

    def go_back(self):
        """
        Возврат к предыдущему экрану (профилю)

        Проверяет наличие несохраненных изменений перед выходом
        """
        if self._pending_changes:
            # Если есть несохраненные изменения - показываем диалог
            self.show_unsaved_changes_dialog()
        else:
            # Если изменений нет - просто переходим назад
            if hasattr(self, 'manager') and self.manager:
                self.manager.current = "profile"

    def show_unsaved_changes_dialog(self):
        """
        Показывает диалоговое окно с предупреждением о несохраненных изменениях
        """
        dialog = MDDialog(
            title="Несохраненные изменения",
            text="У вас есть несохраненные изменения. Сохранить перед выходом?",
            buttons=[
                MDRaisedButton(
                    text="Не сохранять",
                    on_release=lambda _: (dialog.dismiss(), self._force_go_back())
                ),
                MDRaisedButton(
                    text="Сохранить",
                    md_bg_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=lambda _: (
                        dialog.dismiss(),
                        self.save_all_settings(),
                        self._force_go_back()
                    )
                ),
            ]
        )
        dialog.open()

    def _force_go_back(self):
        """
        Принудительный возврат к экрану профиля

        Используется при отказе от сохранения изменений
        """
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = "profile"

    def show_message(self, title, text):
        """
        Показывает диалоговое окно с сообщением

        Args:
            title (str): Заголовок сообщения
            text (str): Текст сообщения
        """
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    md_bg_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=lambda _: dialog.dismiss()
                )
            ]
        )
        dialog.open()
