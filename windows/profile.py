"""
Модуль профиля пользователя для приложения "Дневник здоровья"
Содержит экран профиля с возможностью изменения данных и аватара
"""

# Стандартные библиотеки Python
import os
import platform
import base64
from datetime import datetime

# Библиотеки Kivy для создания GUI
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView

# Компоненты KivyMD (Material Design)
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton

# Пользовательские модули
from services.photoeditor import SimplePhotoEditor
from database import get_connection, select_user_by_id, update_user_photo, update_user
from kv import REG_KV, PROFILE_KV
from utils.rules import (
    validate_email
)

# Попытка импорта plyer для выбора файлов (кросс-платформенный)
try:
    from plyer import filechooser

    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

# Попытка импорта PIL для работы с изображениями
try:
    from PIL import Image as PILImage
    from PIL import ImageDraw

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    PILImage = None
    ImageDraw = None

# Загрузка всех KV-разметок
#Builder.load_string(REG_KV)
#Builder.load_string(PROFILE_KV)

class ProfileScreen(Screen):
    """
    Экран профиля пользователя

    Отображает информацию о пользователе и позволяет:
    1. Просматривать профиль
    2. Изменять данные пользователя
    3. Загружать и редактировать аватар
    4. Выходить из системы
    """

    dialog = None  # Текущее диалоговое окно
    photo_menu = None  # Меню выбора фото
    avatar_source = StringProperty("")  # Свойство для хранения пути к аватару

    def __init__(self, **kwargs):
        """
        Инициализация экрана профиля
        """
        super().__init__(**kwargs)
        self.user_info_label = None  # Label для отображения информации
        self.profile_image_widget = None  # Виджет изображения профиля
        self.current_user_id = None  # ID текущего пользователя
        self._avatar_loaded = False  # Флаг загрузки аватара
        self._avatar_cache = {}  # Кэш аватаров по user_id
        self._info_loaded = False  # Флаг загрузки информации
        self._data_pending = False  # Флаг ожидания данных

    def update_admin_button(self):
        """
        Обновляет состояние кнопки администратора
        """
        app = MDApp.get_running_app()

        if hasattr(self, 'ids') and 'admin_btn' in self.ids:
            admin_btn = self.ids.admin_btn
            admin_btn.opacity = 1 if app.is_admin else 0
            admin_btn.disabled = not app.is_admin
            print(f"Кнопка администратора: opacity={admin_btn.opacity}, disabled={admin_btn.disabled}")

    def on_pre_enter(self):
        """
        Метод, вызываемый перед переходом на экран профиля
        """
        app = MDApp.get_running_app()
        if hasattr(app, 'apply_user_settings_immediately'):
            app.apply_user_settings_immediately()

        # Загружаем данные пользователя сразу
        self.load_user_data_immediate()

        # Обновляем кнопку администратора
        self.update_admin_button()

    def on_enter(self):
        """
        Метод, вызываемый при переходе на экран профиля
        (оставлен для совместимости)
        """
        pass

    def on_kv_post(self, base_widget):
        """
        Метод, вызываемый после загрузки KV-разметки

        Инициализирует ссылки на виджеты из KV-разметки
        """
        if hasattr(self, 'ids'):
            self.user_info_label = self.ids.user_info
            self.profile_image_widget = self.ids.profile_image

    def load_user_data_immediate(self):
        """
        Немедленно загружает данные пользователя из базы данных

        Загружает:
        1. Информацию о пользователе (имя, email, дата регистрации)
        2. Аватар пользователя (если есть)
        """
        try:
            app = MDApp.get_running_app()
            user_id = app.get_user_id() if hasattr(app, 'get_user_id') else None

            if not user_id:
                self._set_user_info_text("Пользователь не авторизован")
                self.avatar_source = ""
                return

            self.current_user_id = user_id

            # Проверяем кэш аватара
            if user_id in self._avatar_cache:
                cached_avatar = self._avatar_cache[user_id]
                if cached_avatar:
                    self.avatar_source = cached_avatar
                    self._avatar_loaded = True
                    print("Аватар загружен из памяти")

            # Загружаем данные пользователя из БД
            conn = get_connection()
            user_data = select_user_by_id(conn, user_id, detailed=True)

            if user_data:
                # Исправлено: распаковываем только нужные поля
                name, email, created_at_str, profile_photo, is_admin = user_data

                # Обновляем статус администратора в приложении
                app.is_admin = bool(is_admin)

                # Преобразуем строку даты в объект datetime
                created_at = None
                if created_at_str:
                    try:
                        # Пробуем разные форматы дат
                        formats = [
                            '%Y-%m-%d %H:%M:%S',  # SQLite формат
                            '%Y-%m-%d %H:%M:%S.%f',  # SQLite с микросекундами
                            '%Y-%m-%d',  # Только дата
                            '%d.%m.%Y %H:%M:%S',  # Другой возможный формат
                        ]

                        for fmt in formats:
                            try:
                                created_at = datetime.strptime(created_at_str, fmt)
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        print(f"Ошибка парсинга даты {created_at_str}: {e}")
                        created_at = None

                # Форматируем дату в соответствии с настройками пользователя
                date_format = app.user_settings.get('date_format', 'dd-mm-yyyy')
                if created_at:
                    if date_format == 'dd-mm-yyyy':
                        date_str = created_at.strftime('%d.%m.%Y')
                    elif date_format == 'mm-dd-yyyy':
                        date_str = created_at.strftime('%m.%d.%Y')
                    elif date_format == 'yyyy-mm-dd':
                        date_str = created_at.strftime('%Y.%m.%d')
                    else:
                        date_str = created_at.strftime('%d.%m.%Y')
                else:
                    date_str = "неизвестно"

                # Формируем текст информации
                info_text = f"{name}\n{email}\nЗарегистрирован: {date_str}"
                self._set_user_info_text(info_text)
                self._info_loaded = True

                # Обрабатываем аватар, если он есть
                if profile_photo and not self._avatar_loaded:
                    self._process_avatar_sync(profile_photo, user_id)
                elif not profile_photo:
                    self.avatar_source = ""  # Сбрасываем аватар, если его нет
            else:
                self._set_user_info_text("Данные пользователя не найдены")
                self.avatar_source = ""

        except Exception as e:
            print(f"Ошибка загрузки данных пользователя: {e}")
            self._set_user_info_text("Ошибка загрузки")
            self.avatar_source = ""
        finally:
            if 'conn' in locals():
                conn.close()

    def _process_avatar_sync(self, profile_photo, user_id):
        """
        Синхронно обрабатывает аватар пользователя

        Args:
            profile_photo (str): Аватар в формате base64
            user_id (int): ID пользователя
        """
        try:
            if not profile_photo:
                return

            # Декодируем base64 в бинарные данные
            image_data = base64.b64decode(profile_photo)

            # Сохраняем во временный файл
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_path = temp_file.name
            temp_file.write(image_data)
            temp_file.close()

            # Сохраняем в кэш
            self._avatar_cache[user_id] = temp_path

            # Устанавливаем источник изображения
            self.avatar_source = temp_path
            self._avatar_loaded = True

            print(f"Аватар обработан и закэширован для user_id={user_id}")

        except Exception as e:
            print(f"Ошибка обработки аватара: {e}")

    def is_mobile(self):
        """
        Проверяет, является ли устройство мобильным

        Returns:
            bool: True если устройство Android или iOS
        """
        return platform in ('android', 'ios')

    def show_photo_menu(self):
        """
        Показывает меню выбора фото в зависимости от платформы
        """
        if self.is_mobile():
            self.open_mobile_file_chooser()
        else:
            self.open_desktop_file_chooser()

    def open_mobile_file_chooser(self):
        """
        Открывает выбор файла на мобильных устройствах

        На Android использует стандартную галерею,
        на других платформах - универсальный метод
        """
        try:
            if platform == 'android':
                # Используем Android Intent для выбора изображения
                from android import mActivity
                from android.content import Intent
                from android.provider import MediaStore
                intent = Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI)
                mActivity.startActivityForResult(intent, 1001)
            else:
                # Используем plyer для других мобильных платформ
                if PLYER_AVAILABLE:
                    filechooser.open_file(
                        title="Выберите фото",
                        filters=[["Image files", "*.png", "*.jpg", "*.jpeg"]],
                        on_selection=self.handle_file_selection
                    )
                else:
                    self.show_message("Ошибка", "Не удалось открыть галерею")
        except Exception as e:
            print(f"Ошибка открытия галереи: {e}")
            self.open_universal_file_chooser()

    def open_desktop_file_chooser(self):
        """
        Открывает выбор файла на десктопных устройствах

        Использует plyer или Tkinter для выбора файла
        """
        try:
            if PLYER_AVAILABLE:
                # Используем plyer для кросс-платформенного выбора файла
                filechooser.open_file(
                    title="Выберите фото",
                    filters=[["Image files", "*.png", "*.jpg", "*.jpeg"]],
                    on_selection=self.handle_file_selection
                )
            else:
                self.open_tkinter_file_chooser()
        except Exception as e:
            print(f"Ошибка открытия проводника: {e}")
            self.open_universal_file_chooser()

    def open_tkinter_file_chooser(self):
        """
        Открывает диалог выбора файла с помощью Tkinter

        Используется как резервный вариант на десктопах
        """
        try:
            import tkinter as tk
            from tkinter import filedialog

            # Создаем скрытое окно Tkinter
            root = tk.Tk()
            root.withdraw()

            # Открываем диалог выбора файла
            file_path = filedialog.askopenfilename(
                title="Выберите фото",
                filetypes=[("Image files", "*.png *.jpg *.jpeg")]
            )
            root.destroy()

            if file_path:
                # Открываем редактор фото
                Clock.schedule_once(lambda dt: self.open_photo_editor(file_path), 0.1)
        except Exception as e:
            print(f"Ошибка Tkinter файлового диалога: {e}")
            self.open_universal_file_chooser()

    def open_universal_file_chooser(self):
        """
        Универсальный файловый браузер на Kivy

        Используется как последний резервный вариант
        """
        try:
            from kivy.uix.filechooser import FileChooserListView

            # Создаем layout для файлового браузера
            box = BoxLayout(orientation='vertical', spacing=10, padding=10)
            initial_path = os.path.expanduser("~")  # Начинаем с домашней директории

            # Создаем файловый браузер
            filechooser = FileChooserListView(
                path=initial_path,
                filters=['*.png', '*.jpg', '*.jpeg']  # Только изображения
            )

            # Кнопки управления
            btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
            btn_cancel = MDRaisedButton(
                text='Отмена',
                on_release=lambda x: self.file_browser_view.dismiss()
            )
            btn_select = MDRaisedButton(
                text='Выбрать',
                on_release=lambda x: self.on_file_selected(filechooser.selection)
            )

            btn_layout.add_widget(btn_cancel)
            btn_layout.add_widget(btn_select)

            box.add_widget(filechooser)
            box.add_widget(btn_layout)

            # Открываем в модальном окне
            self.file_browser_view = ModalView(size_hint=(0.9, 0.8))
            self.file_browser_view.add_widget(box)
            self.file_browser_view.open()

        except Exception as e:
            self.show_message("Ошибка", f"Не удалось открыть файловый браузер: {str(e)}")

    def handle_file_selection(self, selection):
        """
        Обрабатывает выбор файла из plyer filechooser

        Args:
            selection (list): Список выбранных файлов
        """
        if selection:
            selected_file = selection[0]
            Clock.schedule_once(lambda dt: self.open_photo_editor(selected_file), 0.1)

    def on_file_selected(self, selection):
        """
        Обрабатывает выбор файла из универсального браузера

        Args:
            selection (list): Список выбранных файлов
        """
        if selection:
            selected_file = selection[0]
            self.file_browser_view.dismiss()
            Clock.schedule_once(lambda dt: self.open_photo_editor(selected_file), 0.1)
        else:
            self.file_browser_view.dismiss()

    def open_photo_editor(self, image_path):
        """
        Открывает редактор фотографий для выбранного изображения

        Args:
            image_path (str): Путь к выбранному изображению
        """
        if image_path and os.path.exists(image_path):
            try:
                # Проверяем, что файл действительно изображение
                try:
                    with PILImage.open(image_path) as img:
                        img.verify()
                except Exception as e:
                    self.show_message("Ошибка", "Выбранный файл не является изображением")
                    return

                # Создаем и открываем редактор
                editor = SimplePhotoEditor(image_path, self.on_photo_edited)

                # Даем время на инициализацию виджетов
                Clock.schedule_once(lambda dt: self._open_editor_dialog(editor), 0.1)

            except Exception as e:
                self.show_message("Ошибка", f"Ошибка загрузки фото: {str(e)}")
        else:
            self.show_message("Ошибка", "Файл не найден")

    def _open_editor_dialog(self, editor):
        """Вспомогательный метод для открытия диалога с редактором"""
        self.dialog = MDDialog(
            type="custom",
            content_cls=editor,
            auto_dismiss=False
        )
        self.dialog.open()

    def on_photo_edited(self, image_data_base64):
        """
        Обрабатывает результат редактирования фото

        Args:
            image_data_base64 (str): Отредактированное фото в base64 или None если отмена
        """
        if self.dialog:
            self.dialog.dismiss()

        if image_data_base64:
            # Обрабатываем новый аватар
            self._process_avatar_sync(image_data_base64, self.current_user_id)

            # Сохраняем в базу данных
            Clock.schedule_once(lambda dt: self.save_profile_photo_to_db(image_data_base64), 0.1)
            self.show_message("Успех", "Фото профиля обновлено")
        else:
            print("Редактирование фото отменено")

    def _set_user_info_text(self, text):
        """
        Устанавливает текст информации о пользователе

        Args:
            text (str): Текст для отображения
        """
        try:
            if self.user_info_label:
                self.user_info_label.text = text
            elif hasattr(self, 'ids') and 'user_info' in self.ids:
                self.ids.user_info.text = text
        except Exception as e:
            print(f"Ошибка установки текста: {e}")

    def save_profile_photo_to_db(self, image_data_base64):
        """
        Сохраняет фото профиля в базу данных

        Args:
            image_data_base64 (str): Изображение в формате base64
        """
        app = MDApp.get_running_app()
        user_id = app.get_user_id() if hasattr(app, 'get_user_id') else None
        conn = None

        if not user_id:
            return

        try:
            conn = get_connection()
            update_user_photo(conn, user_id, image_data_base64)
        except Exception as e:
            print(f"Ошибка сохранения аватарки: {str(e)}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def change_profile(self):
        """
        Открывает диалог для изменения данных профиля
        """
        app = MDApp.get_running_app()
        user_id = app.get_user_id() if hasattr(app, 'get_user_id') else None
        conn = None

        if not user_id:
            self.show_message("Ошибка", "Пользователь не авторизован")
            return

        # Загружаем текущие данные пользователя
        try:
            conn = get_connection()
            user_data = select_user_by_id(conn, user_id)

        except Exception as e:
            self.show_message("Ошибка", f"Ошибка загрузки данных: {e}")
            return
        finally:
            if 'conn' in locals() and conn:
                conn.close()

        if not user_data:
            self.show_message("Ошибка", "Данные пользователя не найдены")
            return

        name, email = user_data

        # Создаем форму редактирования
        edit_box = BoxLayout(orientation="vertical", spacing=15, size_hint_y=None)
        edit_box.height = 150

        name_input = MDTextField(
            hint_text="Имя",
            text=name,
            size_hint_y=None,
            height=40
        )

        email_input = MDTextField(
            hint_text="Email",
            text=email,
            size_hint_y=None,
            height=40
        )

        edit_box.add_widget(name_input)
        edit_box.add_widget(email_input)

        # Создаем диалоговое окно
        self.dialog = MDDialog(
            title="Редактировать профиль",
            type="custom",
            content_cls=edit_box,
            buttons=[
                MDRaisedButton(
                    text="Отмена",
                    md_bg_color=(0.7, 0.7, 0.7, 1),
                    on_release=lambda _: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Сохранить",
                    md_bg_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=lambda _: self.save_profile_changes(
                        name_input.text,
                        email_input.text
                    )
                ),
            ],
        )
        self.dialog.open()

    def save_profile_changes(self, name, email):
        """
        Сохраняет изменения профиля в базу данных

        Args:
            name (str): Новое имя пользователя
            email (str): Новый email пользователя
        """
        app = MDApp.get_running_app()
        user_id = app.get_user_id() if hasattr(app, 'get_user_id') else None
        conn = None

        # Проверка валидности данных
        if not name.strip():
            self.show_message("Ошибка", "Имя не может быть пустым")
            return

        try:
            # Валидация email
            validate_email(email.strip())

            # Сохранение в базу данных
            conn = get_connection()
            update_user(conn, user_id, name.strip(), email.strip())

            self.show_message("Успех", "Профиль обновлен")
            self.dialog.dismiss()

            # Обновляем отображение данных
            self.load_user_data_immediate()

        except ValueError as e:
            self.show_message("Ошибка", str(e))
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка сохранения: {str(e)}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def open_settings(self):
        """
        Переход к экрану настроек
        """
        # Проверяем, не гость ли пользователь
        app = MDApp.get_running_app()
        if getattr(app, 'is_guest', False):
            from utils.ui import UIUtils
            UIUtils.show_message("Недоступно", "Настройки недоступны в гостевом режиме")
            return

        self.manager.current = "settings"

    def open_admin_panel(self):
        """
        Переход к административной панели
        """

        # Проверяем, является ли пользователь администратором
        app = MDApp.get_running_app()
        if getattr(app, 'is_admin', False):
            self.manager.current = "admin_dashboard"
        else:
            from utils.ui import UIUtils
            UIUtils.show_message("Доступ запрещен", "Только администраторы могут открывать эту панель")

    def logout(self):
        """
        Выполняет выход пользователя из системы

        Очищает:
        1. Кэш аватара
        2. Данные профиля на экране
        3. Сессию пользователя
        4. Сбрасывает тему к стандартной
        """
        app = MDApp.get_running_app()

        # Очищаем кэш аватара
        if self.current_user_id and self.current_user_id in self._avatar_cache:
            cached_path = self._avatar_cache.pop(self.current_user_id, None)
            if cached_path and os.path.exists(cached_path):
                try:
                    os.unlink(cached_path)
                except:
                    pass

        # Очищаем отображение профиля
        self.avatar_source = ""
        self._set_user_info_text("")
        self._avatar_loaded = False
        self._info_loaded = False
        self._data_pending = False

        # Сбрасываем тему к стандартной
        if hasattr(app, 'reset_theme_to_default'):
            app.reset_theme_to_default()

        # Удаляем сессию пользователя
        if hasattr(app, 'delete_user_session'):
            app.delete_user_session()

        # Сбрасываем ID пользователя в приложении
        if hasattr(app, 'set_user_id'):
            app.set_user_id(None)

        # Переходим на экран авторизации
        if hasattr(app, 'root') and hasattr(app.root, 'current'):
            app.root.current = "registration"

    def go_back(self):
        """
        Возврат к предыдущему экрану (истории записей)
        """
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = "story"

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
