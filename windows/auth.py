"""
Главный модуль приложения "Дневник здоровья"
Содержит основные классы для работы с авторизацией, вводом данных и настройками
"""

# Импорт стандартных библиотек Python
import hashlib
import os
import binascii
import uuid

# Импорт библиотеки Kivy для создания графического интерфейса
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.metrics import dp
from kivy.clock import Clock

# Импорт компонентов KivyMD (Material Design)
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar

# Импорт пользовательских модулей
from database import get_connection, insert_user, \
    select_user_by_email, select_user_count_by_email  # Подключение к базе данных
from kv import REG_KV
from utils.ui import UIUtils, CustomMDRaisedButton
from utils.rules import (
    validate_email,  # Валидация email
    validate_name,  # Валидация имени
    validate_password,  # Валидация пароля
    evaluate_password_strength  # Оценка сложности пароля
)

# Загрузка KV-разметки в приложение
# Builder.load_string(REG_KV)

class RegistrationWindow(Screen):
    """
    Окно регистрации и входа в приложение

    Отвечает за:
    1. Авторизацию существующих пользователей
    2. Регистрацию новых пользователей
    3. Валидацию вводимых данных
    4. Переключение между режимами входа и регистрации
    """

    mode = "login"  # Текущий режим: "login" (вход) или "register" (регистрация)

    def on_pre_enter(self):
        """
        Метод, вызываемый перед переходом на этот экран

        Применяет настройки пользователя (тему) перед показом экрана
        """
        app = MDApp.get_running_app()
        if hasattr(app, 'apply_user_settings_immediately'):
            app.apply_user_settings_immediately()

    def on_kv_post(self, base_widget):
        """
        Метод, вызываемый после загрузки KV-разметки

        Инициализирует все UI-компоненты окна регистрации
        """
        # Создаем заголовок окна
        self.title_label = MDLabel(
            text="Вход в Health Diary",
            halign="center",
            font_style="H5",
            theme_text_color="Custom",
            text_color=(0, 0, 1, 1),  # Синий текст
            size_hint_y=None,
            height=dp(40)
        )

        # Создаем поля ввода с помощью UIUtils
        self.email = UIUtils.create_text_field("Введите email")
        self.password = UIUtils.create_text_field("Введите пароль", password=True)
        self.name_field = UIUtils.create_text_field("Введите имя")
        self.confirm_password = UIUtils.create_text_field("Повторите пароль", password=True)

        # Основная кнопка (Войти/Зарегистрироваться)
        self.main_button = CustomMDRaisedButton(
            text="Войти",
            size_hint_x=None,
            width=dp(200),
            pos_hint={"center_x": 0.5},
            md_bg_color=(0, 0, 1, 1),  # Синий фон
            text_color=(1, 1, 1, 1)  # Белый текст
        )

        # Кнопка переключения между режимами
        self.switch_button = CustomMDRaisedButton(
            text="Зарегистрироваться",
            size_hint_x=None,
            width=dp(200),
            pos_hint={"center_x": 0.5},
            md_bg_color=(0, 0, 1, 1),
            text_color=(1, 1, 1, 1)
        )

        # Кнопка входа как гостя
        self.guest_button = CustomMDRaisedButton(
            text="Войти как гость",
            size_hint_x=None,
            width=dp(200),
            pos_hint={"center_x": 0.5},
            md_bg_color=(0.5, 0.5, 0.5, 1),  # Серый цвет для гостя
            text_color=(1, 1, 1, 1)
        )

        # Привязываем обработчики нажатия кнопок
        self.main_button.bind(on_release=self.on_main_button_pressed)
        self.switch_button.bind(on_release=self.on_switch_button_pressed)
        self.guest_button.bind(on_release=self.on_guest_button_pressed)

        # Элементы для отображения сложности пароля
        self.password_strength_label = MDLabel(
            size_hint_y=None,
            height=dp(30),
            pos_hint={"center_x": 0.5}
        )
        self.password_strength_bar = MDProgressBar(
            size_hint=(None, None),
            width=dp(300),
            height=dp(5),
            pos_hint={"center_x": 0.5}
        )

        # Строим начальную форму (режим входа)
        self._build_form(register=False)

    def on_main_button_pressed(self, instance):
        """
        Обработчик нажатия основной кнопки

        Добавляет анимацию изменения цвета кнопки при нажатии
        """
        # Изменяем цвет кнопки при нажатии (анимация)
        instance.md_bg_color = (0, 0, 0.8, 1)  # Более темный синий
        # Восстанавливаем цвет через 0.08 секунды
        Clock.schedule_once(lambda dt: setattr(instance, 'md_bg_color', (0, 0, 1, 1)), 0.08)
        # Выполняем основное действие через 0.05 секунды
        Clock.schedule_once(lambda dt: self.main_action(), 0.05)

    def on_switch_button_pressed(self, instance):
        """
        Обработчик нажатия кнопки переключения режима
        """
        instance.md_bg_color = (0, 0, 0.8, 1)
        Clock.schedule_once(lambda dt: setattr(instance, 'md_bg_color', (0, 0, 1, 1)), 0.08)
        Clock.schedule_once(lambda dt: self.switch_mode(), 0.05)

    def on_guest_button_pressed(self, instance):
        """
        Обработчик нажатия кнопки входа как гостя
        """
        instance.md_bg_color = (0.3, 0.3, 0.3, 1)
        Clock.schedule_once(lambda dt: setattr(instance, 'md_bg_color', (0.5, 0.5, 0.5, 1)), 0.08)
        Clock.schedule_once(lambda dt: self.login_as_guest(), 0.05)

    def _build_form(self, register: bool):
        """
        Динамически строит форму в зависимости от режима

        Args:
            register (bool): Если True, строит форму регистрации, иначе - форму входа
        """
        fb = self.ids.form_box
        fb.clear_widgets()  # Очищаем контейнер

        self._reset_field_colors()  # Сбрасываем цвета полей

        # Определяем порядок элементов в зависимости от режима
        if register:
            # Порядок для регистрации
            order = [
                self.title_label,
                self.name_field,
                self.email,
                self.password,
                self.confirm_password,
                self.main_button,
                self.switch_button
            ]
        else:
            # Порядок для входа
            order = [
                self.title_label,
                self.email,
                self.password,
                self.main_button,
                self.switch_button,
                self.guest_button  # Добавляем кнопку гостя в режиме входа
            ]

        # Добавляем элементы в контейнер
        for w in order:
            fb.add_widget(w)

        if register:
            # Настраиваем элементы для режима регистрации
            self.title_label.text = "Регистрация"
            self.main_button.text = "Зарегистрироваться"
            self.switch_button.text = "Уже есть аккаунт? Войти"

            # Добавляем элементы отображения сложности пароля
            fb.add_widget(self.password_strength_label)
            fb.add_widget(self.password_strength_bar)

            # Обновляем отображение сложности пароля
            self.on_password_change(self.password, self.password.text)
        else:
            # Настраиваем элементы для режима входа
            self.title_label.text = "Вход в Health Diary"
            self.main_button.text = "Войти"
            self.switch_button.text = "Зарегистрироваться"
            self.guest_button.text = "Войти как гость"

        # Устанавливаем цвета кнопок
        self.main_button.md_bg_color = (0, 0, 1, 1)
        self.switch_button.md_bg_color = (0, 0, 1, 1)
        self.guest_button.md_bg_color = (0.5, 0.5, 0.5, 1)

        # Привязываем обработчики изменения текста
        self.password.bind(text=self.on_password_change)
        self.email.bind(text=self.on_email_change)

        # Для регистрации привязываем дополнительные обработчики
        if register:
            self.name_field.bind(text=self.on_name_change)
            self.confirm_password.bind(text=self.on_confirm_password_change)
        else:
            # Для входа отвязываем обработчики, если они были привязаны
            try:
                self.name_field.unbind(text=self.on_name_change)
                self.confirm_password.unbind(text=self.on_confirm_password_change)
            except:
                pass

    def _reset_field_colors(self):
        """Сбрасывает цвета всех полей ввода к стандартным"""
        default_color = (0, 0, 1, 1)  # Синий цвет

        self.email.line_color_normal = default_color
        self.email.text_color_normal = default_color
        self.password.line_color_normal = default_color
        self.password.text_color_normal = default_color
        self.name_field.line_color_normal = default_color
        self.name_field.text_color_normal = default_color
        self.confirm_password.line_color_normal = default_color
        self.confirm_password.text_color_normal = default_color

        # Сбрасываем индикатор сложности пароля
        self.password_strength_label.text = ""
        self.password_strength_bar.value = 0

    def switch_mode(self):
        """Переключает между режимами входа и регистрации"""
        self.mode = "register" if self.mode == "login" else "login"
        self._build_form(register=(self.mode == "register"))

    def main_action(self):
        """
        Выполняет основное действие в зависимости от режима:
        - Вход в систему
        - Регистрация нового пользователя
        """
        if self.mode == "login":
            self.login()
        else:
            self.register()

    def login_as_guest(self):
        """
        Вход в приложение как гость

        Гость имеет ограниченный функционал и использует только локальную базу данных
        """
        try:
            app = MDApp.get_running_app()

            # Создаем уникальный ID для гостя
            guest_id = -1  # Отрицательный ID для гостей
            guest_device_id = f"guest_{uuid.uuid4().hex[:8]}"

            # Устанавливаем флаг гостя и ID
            app.set_user_id(guest_id)
            app.is_guest = True
            app.guest_device_id = guest_device_id

            # Для гостя используем только локальную базу данных
            from database import set_force_local
            set_force_local(True)

            # Показываем сообщение об ограничениях
            UIUtils.show_message(
                "Гостевой режим",
                "Вы вошли как гость. Доступны ограниченные возможности:\n"
                "✓ Ввод и просмотр записей\n"
                "✗ Экспорт данных недоступен\n"
                "✗ Настройки профиля недоступны\n"
                "✗ Данные хранятся только на устройстве",
                callback=lambda: self.transition_to_options()
            )

        except Exception as e:
            UIUtils.show_message("Ошибка", f"Ошибка входа как гость: {str(e)}")

    def on_email_change(self, instance, value):
        """
        Обработчик изменения текста в поле email

        Выполняет валидацию email в реальном времени и меняет цвет поля

        Args:
            instance: Объект поля ввода
            value: Текущее значение поля
        """
        if not value:
            # Если поле пустое - стандартный цвет
            self.email.line_color_normal = (0, 0, 1, 1)
            self.email.text_color_normal = (0, 0, 1, 1)
            return

        try:
            # Пытаемся валидировать email
            validate_email(value)

            # Зеленый цвет - email валиден
            self.email.line_color_normal = (0, 1, 0, 1)
            self.email.text_color_normal = (0, 0, 0, 1)

        except ValueError:
            # Красный цвет - email невалиден
            self.email.line_color_normal = (1, 0, 0, 1)
            self.email.text_color_normal = (1, 0, 0, 1)

    def on_password_change(self, instance, value):
        """
        Обработчик изменения пароля

        Оценивает сложность пароля и проверяет совпадение с подтверждением

        Args:
            instance: Объект поля ввода
            value: Текущее значение поля
        """
        if self.mode != "register":
            # Для режима входа не показываем сложность пароля
            self.password_strength_label.text = ""
            self.password_strength_bar.value = 0
            self.password.line_color_normal = (0, 0, 1, 1)
            self.password.text_color_normal = (0, 0, 1, 1)
            return

        confirm_password = self.confirm_password.text.strip()

        if not value:
            # Пустой пароль
            self.password.line_color_normal = (0, 0, 1, 1)
            self.password.text_color_normal = (0, 0, 1, 1)
            self.password_strength_label.text = ""
            self.password_strength_bar.value = 0
        else:
            # Оцениваем сложность пароля
            strength, color = evaluate_password_strength(value)

            # Устанавливаем цвет в зависимости от сложности
            if strength == "Слабый":
                self.password.line_color_normal = (1, 0, 0, 1)  # Красный
                self.password.text_color_normal = (1, 0, 0, 1)
            elif strength == "Средний" or strength == "Сильный":
                self.password.line_color_normal = (0, 1, 0, 1)  # Зеленый
                self.password.text_color_normal = (0, 0, 0, 1)  # Черный текст

            # Обновляем label и прогресс-бар
            self.password_strength_label.text = f"Сложность: {strength}"
            self.password_strength_label.text_color = color

            progress = self.get_password_strength_progress(strength)
            self.password_strength_bar.value = progress

        # Проверяем совпадение паролей
        self._validate_password_match(value, confirm_password)

    def get_password_strength_progress(self, strength):
        """
        Преобразует текстовую оценку сложности в числовое значение для прогресс-бара

        Args:
            strength (str): Текстовая оценка сложности

        Returns:
            int: Значение от 0 до 100 для прогресс-бара
        """
        if strength == "Слабый":
            return 25
        elif strength == "Средний":
            return 50
        elif strength == "Сильный":
            return 75
        else:
            return 100

    def is_email_taken(self, email: str) -> bool:
        """
        Проверяет, занят ли email в базе данных

        Args:
            email (str): Email для проверки

        Returns:
            bool: True если email уже занят, иначе False
        """
        conn = get_connection()

        # Выполняем запрос к базе данных
        result = select_user_count_by_email(conn, email)

        conn.close()

        # Возвращаем True если найдено хотя бы одно совпадение
        if result:
            return result[0] > 0
        return False

    def on_name_change(self, instance, value):
        """
        Обработчик изменения имени пользователя

        Args:
            instance: Объект поля ввода
            value: Текущее значение поля
        """
        if not value:
            # Пустое поле - стандартный цвет
            self.name_field.line_color_normal = (0, 0, 1, 1)
            self.name_field.text_color_normal = (0, 0, 1, 1)
            return

        try:
            # Валидируем имя
            validate_name(value)
            # Зеленый цвет - имя валидно
            self.name_field.line_color_normal = (0, 1, 0, 1)
            self.name_field.text_color_normal = (0, 0, 0, 1)
        except ValueError:
            # Красный цвет - имя невалидно
            self.name_field.line_color_normal = (1, 0, 0, 1)
            self.name_field.text_color_normal = (1, 0, 0, 1)

    def on_confirm_password_change(self, instance, value):
        """
        Обработчик изменения поля подтверждения пароля

        Args:
            instance: Объект поля ввода
            value: Текущее значение поля
        """
        password = self.password.text.strip()
        self._validate_password_match(password, value)

    def _validate_password_match(self, password: str, confirm_password: str):
        """
        Проверяет совпадение пароля и подтверждения

        Args:
            password (str): Основной пароль
            confirm_password (str): Подтверждение пароля
        """
        # Оба поля пустые
        if not password and not confirm_password:
            self.password.line_color_normal = (0, 0, 1, 1)
            self.password.text_color_normal = (0, 0, 1, 1)
            self.confirm_password.line_color_normal = (0, 0, 1, 1)
            self.confirm_password.text_color_normal = (0, 0, 1, 1)
            return

        # Пароль есть, но нет подтверждения
        if password and not confirm_password:
            self.confirm_password.line_color_normal = (1, 0, 0, 1)
            self.confirm_password.text_color_normal = (1, 0, 0, 1)
            return

        # Пароля нет, но есть подтверждение
        if not password and confirm_password:
            self.password.line_color_normal = (1, 0, 0, 1)
            self.password.text_color_normal = (1, 0, 0, 1)
            self.confirm_password.line_color_normal = (1, 0, 0, 1)
            self.confirm_password.text_color_normal = (1, 0, 0, 1)
            return

        # Пароли не совпадают
        if password != confirm_password:
            self.password.line_color_normal = (1, 0, 0, 1)
            self.password.text_color_normal = (1, 0, 0, 1)
            self.confirm_password.line_color_normal = (1, 0, 0, 1)
            self.confirm_password.text_color_normal = (1, 0, 0, 1)
            return

        # Пароли совпадают и не пустые
        if password == confirm_password and password and confirm_password:
            # Проверяем сложность пароля
            strength, _ = evaluate_password_strength(password)
            if strength == "Слабый":
                # Слабый пароль - красный цвет
                self.password.line_color_normal = (1, 0, 0, 1)
                self.password.text_color_normal = (1, 0, 0, 1)
            else:
                # Хороший пароль - зеленый цвет
                self.password.line_color_normal = (0, 1, 0, 1)
                self.password.text_color_normal = (0, 0, 0, 1)

            # Подтверждение - зеленый цвет
            self.confirm_password.line_color_normal = (0, 1, 0, 1)
            self.confirm_password.text_color_normal = (0, 0, 0, 1)

    def hash_password(self, password: str) -> str:
        """
        Хеширует пароль с использованием соли (salt)

        Использует алгоритм PBKDF2-HMAC-SHA256 для безопасного хеширования

        Args:
            password (str): Пароль для хеширования

        Returns:
            str: Хеш пароля в формате hex(соль) + hex(хеш)
        """
        # Генерируем случайную соль длиной 32 байта
        salt = os.urandom(32)
        # Вычисляем хеш с использованием соли и 100000 итераций
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        # Возвращаем соль и хеш в шестнадцатеричном формате
        return salt.hex() + pwd_hash.hex()

    def verify_password(self, provided_password: str, stored_password_hash: str) -> bool:
        """
        Проверяет соответствие введенного пароля сохраненному хешу

        Args:
            provided_password (str): Введенный пароль
            stored_password_hash (str): Сохраненный хеш пароля

        Returns:
            bool: True если пароли совпадают, иначе False
        """
        try:
            # Проверяем длину хеша для определения формата
            if len(stored_password_hash) <= 64:
                # Старый формат без соли (для обратной совместимости)
                return stored_password_hash == provided_password

            # Извлекаем соль (первые 64 символа hex = 32 байта)
            salt = bytes.fromhex(stored_password_hash[:64])
            # Извлекаем хеш (оставшаяся часть)
            stored_hash = stored_password_hash[64:]

            # Вычисляем хеш для введенного пароля с той же солью
            pwd_hash = hashlib.pbkdf2_hmac(
                'sha256',
                provided_password.encode('utf-8'),
                salt,
                100000
            )

            # Сравниваем хеши
            return pwd_hash.hex() == stored_hash

        except (ValueError, binascii.Error, Exception) as e:
            # В случае ошибки возвращаем False
            print(f"Ошибка проверки пароля: {e}")
            return stored_password_hash == provided_password

    def login(self):
        """
        Выполняет вход пользователя в систему

        Проверяет email и пароль, устанавливает сессию пользователя
        """
        email = self.email.text.strip()
        password = self.password.text.strip()

        # Проверка на пустые поля
        if not email or not password:
            UIUtils.show_message("Ошибка", "Введите email и пароль")
            return

        try:
            # Валидация email
            validate_email(email)

            # Подключение к базе данных
            conn = get_connection()

            # Поиск пользователя по email с хешем пароля
            result = select_user_by_email(conn, email, pass_hash=True)

            if result:
                user_id, db_password_hash, is_admin = result

                # Проверка пароля
                if self.verify_password(password, db_password_hash):
                    app = MDApp.get_running_app()
                    app.set_user_id(user_id)  # Устанавливаем ID пользователя
                    app.is_guest = False  # Не гость
                    app.is_admin = bool(is_admin)  # Устанавливаем флаг администратора

                    # Сохраняем сессию для автоматического входа
                    app.save_user_session(user_id)

                    # Загружаем настройки пользователя
                    app.load_user_settings()

                    # Показываем сообщение об успешном входе
                    UIUtils.show_message(
                        "Успех",
                        f"Вход выполнен!{' (Администратор)' if is_admin else ''}",
                        callback=lambda: self.transition_to_options()
                    )
                else:
                    UIUtils.show_message("Ошибка", "Неверный пароль")
            else:
                UIUtils.show_message("Ошибка", "Пользователь не найден")

        except ValueError as e:
            # Ошибка валидации
            UIUtils.show_message("Ошибка", str(e))
        except Exception as e:
            # Ошибка базы данных
            UIUtils.show_message("Ошибка БД", f"Ошибка при входе: {str(e)}")
        finally:
            # Закрываем соединение с БД
            if 'conn' in locals() and conn:
                conn.close()

    def transition_to_options(self):
        """
        Переход на главный экран ввода данных

        Выполняется после успешной авторизации
        """
        app = MDApp.get_running_app()
        # Применяем настройки пользователя
        if hasattr(app, 'apply_user_settings_immediately'):
            app.apply_user_settings_immediately()

        # Анимированный переход на экран ввода данных
        self.manager.transition = SlideTransition(direction='left', duration=0.3)
        self.manager.current = "options"

    def register(self):
        """
        Регистрирует нового пользователя

        Проверяет все поля, хеширует пароль, сохраняет пользователя в БД
        """
        email = self.email.text.strip()
        name = self.name_field.text.strip()
        password = self.password.text.strip()
        confirm = self.confirm_password.text.strip()

        # Проверка на пустые поля
        if not email or not name or not password or not confirm:
            UIUtils.show_message("Ошибка", "Заполните все поля")
            return

        try:
            # Валидация всех полей
            validate_email(email)
            validate_name(name)
            validate_password(password, confirm)

            conn = get_connection()

            # Проверка на существующий email
            if select_user_by_email(conn, email, pass_hash=False):
                UIUtils.show_message("Ошибка", "Такой email уже зарегистрирован")
                return

            # Хеширование пароля
            password_hash = self.hash_password(password)

            # Сохранение пользователя в БД
            # Пользователь по умолчанию не администратор (is_admin=0)
            insert_user(conn, email, password_hash, name, is_admin=False)

            # Получение ID нового пользователя
            # ИСПРАВЛЕНО: получаем данные пользователя без хеша пароля
            user_data = select_user_by_email(conn, email, pass_hash=False)
            if user_data:
                user_id, is_admin = user_data
            else:
                UIUtils.show_message("Ошибка", "Не удалось получить ID пользователя")
                return

            app = MDApp.get_running_app()
            app.set_user_id(user_id)  # Устанавливаем ID в приложении
            app.is_guest = False  # Не гость
            app.is_admin = bool(is_admin)  # Устанавливаем флаг администратора

            # Сохраняем сессию
            app.save_user_session(user_id)

            # Загружаем настройки пользователя
            app.load_user_settings()

            # Сообщение об успешной регистрации
            UIUtils.show_message(
                "Успех",
                "Регистрация завершена!",
                callback=lambda: self.transition_to_options()
            )

        except ValueError as e:
            # Ошибка валидации
            UIUtils.show_message("Ошибка", str(e))
        except Exception as e:
            # Ошибка базы данных
            UIUtils.show_message("Ошибка БД", f"Ошибка при регистрации: {str(e)}")
        finally:
            # Закрываем соединение с БД
            if 'conn' in locals() and conn:
                conn.close()

    def switch_to_login_mode(self):
        """
        Переключает в режим входа

        Используется для возврата к экрану входа после логаута
        """
        self.mode = "login"
        self._build_form(register=False)
