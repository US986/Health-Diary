from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFloatingActionButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.app import App
from datetime import datetime
from base import get_connection
from story_window import StoryWindow
from profile import ProfileScreen
from kivymd.uix.progressbar import MDProgressBar
import hashlib
import os
import binascii
from kivy.clock import Clock
from rules import (
    validate_email,
    validate_name,
    validate_password,
    validate_weight,
    validate_pressure_systolic,
    validate_pressure_diastolic,
    validate_pulse,
    validate_temperature,
    validate_notes,
    evaluate_password_strength
)


class UIUtils:
    @staticmethod
    def create_text_field(hint_text, password=False):
        return MDTextField(
            hint_text=hint_text,
            mode="rectangle",
            password=password,
            size_hint=(None, None),
            width=dp(300),
            height=dp(48),
            pos_hint={"center_x": 0.5},
            line_color_normal=(0, 0, 1, 1),
            text_color_normal=(0, 0, 1, 1)
        )

    @staticmethod
    def show_message(title, text, callback=None):
        dialog = MDDialog(
            title=title,
            text=text,
            size_hint=(0.7, None),
            buttons=[
                MDRaisedButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    md_bg_color=(0, 0, 1, 1),
                    on_release=lambda x: (dialog.dismiss(), callback() if callback else None)
                )
            ]
        )
        dialog.open()
        return dialog


REG_KV = """
<RegistrationWindow>:
    name: "registration"
    FloatLayout:
        AnchorLayout:
            anchor_x: "center"
            anchor_y: "center"
            MDBoxLayout:
                id: form_box
                orientation: "vertical"
                adaptive_height: True
                spacing: dp(10)
                padding: dp(30)
                size_hint_x: None
                width: dp(360)
                pos_hint: {"center_x": 0.5, "center_y": 0.5}

<OptionsWindow>:
    name: 'options'
    BoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "15dp"

        MDLabel:
            text: "Ввод данных здоровья"
            halign: "center"
            theme_text_color: "Primary"
            font_style: "H4"
            size_hint_y: None
            height: dp(50)

        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                spacing: "12dp"
                padding: "10dp"

                MDTextField:
                    id: weight_input
                    hint_text: "Вес (кг)"
                    mode: "rectangle"
                    size_hint_x: None
                    width: dp(300)
                    height: dp(45)
                    pos_hint: {"center_x": 0.5}
                    line_color_normal: 0, 0, 1, 1

                MDTextField:
                    id: pressure_systolic_input
                    hint_text: "Систолическое давление"
                    mode: "rectangle"
                    size_hint_x: None
                    width: dp(300)
                    height: dp(45)
                    pos_hint: {"center_x": 0.5}
                    line_color_normal: 0, 0, 1, 1

                MDTextField:
                    id: pressure_diastolic_input
                    hint_text: "Диастолическое давление"
                    mode: "rectangle"
                    size_hint_x: None
                    width: dp(300)
                    height: dp(45)
                    pos_hint: {"center_x": 0.5}
                    line_color_normal: 0, 0, 1, 1

                MDTextField:
                    id: pulse_input
                    hint_text: "Пульс (уд/мин)"
                    mode: "rectangle"
                    size_hint_x: None
                    width: dp(300)
                    height: dp(45)
                    pos_hint: {"center_x": 0.5}
                    line_color_normal: 0, 0, 1, 1

                MDTextField:
                    id: temperature_input
                    hint_text: "Температура (°C)"
                    mode: "rectangle"
                    size_hint_x: None
                    width: dp(300)
                    height: dp(45)
                    pos_hint: {"center_x": 0.5}
                    line_color_normal: 0, 0, 1, 1

                MDTextField:
                    id: notes_input
                    hint_text: "Заметки"
                    mode: "rectangle"
                    size_hint_x: None
                    width: dp(300)
                    height: dp(60)
                    pos_hint: {"center_x": 0.5}
                    line_color_normal: 0, 0, 1, 1
                    multiline: True

        BoxLayout:
            size_hint_y: None
            height: "70dp"
            orientation: "horizontal"
            padding: "10dp"
            spacing: "15dp"
            pos_hint: {"center_x": 0.5}

            MDFloatingActionButton:
                icon: "content-save"
                md_bg_color: 0, 0.7, 0, 1
                on_release: root.save_data()
                tooltip_text: "Сохранить данные"

            MDFloatingActionButton:
                icon: "history"
                md_bg_color: 0, 0, 1, 1
                on_release: root.go_to_history()
                tooltip_text: "История записей"
"""

Builder.load_string(REG_KV)


class CustomMDRaisedButton(MDRaisedButton):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ripple_scale = 0


class RegistrationWindow(Screen):
    mode = "login"

    def on_kv_post(self, base_widget):
        self.title_label = MDLabel(
            text="Вход в Health Diary",
            halign="center",
            font_style="H5",
            theme_text_color="Custom",
            text_color=(0, 0, 1, 1),
            size_hint_y=None,
            height=dp(40)
        )
        self.email = UIUtils.create_text_field("Введите email")
        self.password = UIUtils.create_text_field("Введите пароль", password=True)
        self.name_field = UIUtils.create_text_field("Введите имя")
        self.confirm_password = UIUtils.create_text_field("Повторите пароль", password=True)

        self.main_button = CustomMDRaisedButton(
            text="Войти",
            size_hint_x=None,
            width=dp(200),
            pos_hint={"center_x": 0.5},
            md_bg_color=(0, 0, 1, 1),
            text_color=(1, 1, 1, 1)
        )

        self.switch_button = CustomMDRaisedButton(
            text="Зарегистрироваться",
            size_hint_x=None,
            width=dp(200),
            pos_hint={"center_x": 0.5},
            md_bg_color=(0, 0, 1, 1),
            text_color=(1, 1, 1, 1)
        )

        self.main_button.bind(on_release=self.on_main_button_pressed)
        self.switch_button.bind(on_release=self.on_switch_button_pressed)

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

        self._build_form(register=False)

    def on_main_button_pressed(self, instance):
        instance.md_bg_color = (0, 0, 0.8, 1)
        Clock.schedule_once(lambda dt: setattr(instance, 'md_bg_color', (0, 0, 1, 1)), 0.08)
        Clock.schedule_once(lambda dt: self.main_action(), 0.05)

    def on_switch_button_pressed(self, instance):
        instance.md_bg_color = (0, 0, 0.8, 1)
        Clock.schedule_once(lambda dt: setattr(instance, 'md_bg_color', (0, 0, 1, 1)), 0.08)
        Clock.schedule_once(lambda dt: self.switch_mode(), 0.05)

    def _build_form(self, register: bool):
        fb = self.ids.form_box
        fb.clear_widgets()

        self._reset_field_colors()

        if register:
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
            order = [
                self.title_label,
                self.email,
                self.password,
                self.main_button,
                self.switch_button
            ]

        for w in order:
            fb.add_widget(w)

        if register:
            self.title_label.text = "Регистрация"
            self.main_button.text = "Зарегистрироваться"
            self.switch_button.text = "Уже есть аккаунт? Войти"

            fb.add_widget(self.password_strength_label)
            fb.add_widget(self.password_strength_bar)

            self.on_password_change(self.password, self.password.text)
        else:
            self.title_label.text = "Вход в Health Diary"
            self.main_button.text = "Войти"
            self.switch_button.text = "Зарегистрироваться"

        self.main_button.md_bg_color = (0, 0, 1, 1)
        self.switch_button.md_bg_color = (0, 0, 1, 1)

        self.password.bind(text=self.on_password_change)
        self.email.bind(text=self.on_email_change)

        if register:
            self.name_field.bind(text=self.on_name_change)
            self.confirm_password.bind(text=self.on_confirm_password_change)
        else:
            try:
                self.name_field.unbind(text=self.on_name_change)
                self.confirm_password.unbind(text=self.on_confirm_password_change)
            except:
                pass

    def _reset_field_colors(self):
        default_color = (0, 0, 1, 1)

        self.email.line_color_normal = default_color
        self.email.text_color_normal = default_color
        self.password.line_color_normal = default_color
        self.password.text_color_normal = default_color
        self.name_field.line_color_normal = default_color
        self.name_field.text_color_normal = default_color
        self.confirm_password.line_color_normal = default_color
        self.confirm_password.text_color_normal = default_color

        self.password_strength_label.text = ""
        self.password_strength_bar.value = 0

    def switch_mode(self):
        self.mode = "register" if self.mode == "login" else "login"
        self._build_form(register=(self.mode == "register"))

    def main_action(self):
        if self.mode == "login":
            self.login()
        else:
            self.register()

    def on_email_change(self, instance, value):
        if not value:
            self.email.line_color_normal = (0, 0, 1, 1)
            self.email.text_color_normal = (0, 0, 1, 1)
            return

        try:
            validate_email(value)

            if self.mode == "register" and self.is_email_taken(value):
                self.email.line_color_normal = (1, 0, 0, 1)
                self.email.text_color_normal = (1, 0, 0, 1)
            elif self.mode == "register":
                self.email.line_color_normal = (0, 1, 0, 1)
                self.email.text_color_normal = (0, 0, 0, 1)
            else:
                self.email.line_color_normal = (0, 0, 1, 1)
                self.email.text_color_normal = (0, 0, 1, 1)

        except ValueError:
            if self.mode == "login":
                self.email.line_color_normal = (0, 0, 1, 1)
                self.email.text_color_normal = (0, 0, 1, 1)
            else:
                self.email.line_color_normal = (1, 0, 0, 1)
                self.email.text_color_normal = (1, 0, 0, 1)

    def on_password_change(self, instance, value):
        if self.mode != "register":
            self.password_strength_label.text = ""
            self.password_strength_bar.value = 0
            self.password.line_color_normal = (0, 0, 1, 1)
            self.password.text_color_normal = (0, 0, 1, 1)
            return

        confirm_password = self.confirm_password.text.strip()

        if not value:
            self.password.line_color_normal = (0, 0, 1, 1)
            self.password.text_color_normal = (0, 0, 1, 1)
            self.password_strength_label.text = ""
            self.password_strength_bar.value = 0
        else:
            strength, color = evaluate_password_strength(value)

            if strength == "Слабый":
                self.password.line_color_normal = (1, 0, 0, 1)
                self.password.text_color_normal = (1, 0, 0, 1)
            elif strength == "Средний" or strength == "Сильный":
                self.password.line_color_normal = (0, 1, 0, 1)
                self.password.text_color_normal = (0, 0, 0, 1)

            self.password_strength_label.text = f"Сложность: {strength}"
            self.password_strength_label.text_color = color

            progress = self.get_password_strength_progress(strength)
            self.password_strength_bar.value = progress

        self._validate_password_match(value, confirm_password)

    def get_password_strength_progress(self, strength):
        if strength == "Слабый":
            return 25
        elif strength == "Средний":
            return 50
        elif strength == "Сильный":
            return 75
        else:
            return 100

    def is_email_taken(self, email: str) -> bool:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return result[0] > 0

    def on_name_change(self, instance, value):
        if not value:
            self.name_field.line_color_normal = (0, 0, 1, 1)
            self.name_field.text_color_normal = (0, 0, 1, 1)
            return

        try:
            validate_name(value)
            self.name_field.line_color_normal = (0, 1, 0, 1)
            self.name_field.text_color_normal = (0, 0, 0, 1)
        except ValueError:
            self.name_field.line_color_normal = (1, 0, 0, 1)
            self.name_field.text_color_normal = (1, 0, 0, 1)

    def on_confirm_password_change(self, instance, value):
        password = self.password.text.strip()
        self._validate_password_match(password, value)

    def _validate_password_match(self, password: str, confirm_password: str):

        if not password and not confirm_password:
            self.password.line_color_normal = (0, 0, 1, 1)
            self.password.text_color_normal = (0, 0, 1, 1)
            self.confirm_password.line_color_normal = (0, 0, 1, 1)
            self.confirm_password.text_color_normal = (0, 0, 1, 1)
            return

        if password and not confirm_password:
            self.confirm_password.line_color_normal = (1, 0, 0, 1)
            self.confirm_password.text_color_normal = (1, 0, 0, 1)
            return

        if not password and confirm_password:
            self.password.line_color_normal = (1, 0, 0, 1)
            self.password.text_color_normal = (1, 0, 0, 1)
            self.confirm_password.line_color_normal = (1, 0, 0, 1)
            self.confirm_password.text_color_normal = (1, 0, 0, 1)
            return

        if password != confirm_password:
            self.password.line_color_normal = (1, 0, 0, 1)
            self.password.text_color_normal = (1, 0, 0, 1)
            self.confirm_password.line_color_normal = (1, 0, 0, 1)
            self.confirm_password.text_color_normal = (1, 0, 0, 1)
            return

        if password == confirm_password and password and confirm_password:
            strength, _ = evaluate_password_strength(password)
            if strength == "Слабый":
                self.password.line_color_normal = (1, 0, 0, 1)
                self.password.text_color_normal = (1, 0, 0, 1)
            else:
                self.password.line_color_normal = (0, 1, 0, 1)
                self.password.text_color_normal = (0, 0, 0, 1)

            self.confirm_password.line_color_normal = (0, 1, 0, 1)
            self.confirm_password.text_color_normal = (0, 0, 0, 1)

    def hash_password(self, password: str) -> str:
        salt = os.urandom(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + pwd_hash.hex()

    def verify_password(self, provided_password: str, stored_password_hash: str) -> bool:
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

        except (ValueError, binascii.Error, Exception) as e:
            print(f"Ошибка проверки пароля: {e}")
            return stored_password_hash == provided_password

    def login(self):
        email = self.email.text.strip()
        password = self.password.text.strip()

        if not email or not password:
            UIUtils.show_message("Ошибка", "Введите email и пароль")
            return

        try:
            validate_email(email)

            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, password_hash FROM users WHERE email=%s", (email,))
                result = cursor.fetchone()

            if result:
                user_id, db_password_hash = result

                if self.verify_password(password, db_password_hash):
                    app = MDApp.get_running_app()
                    app.set_user_id(user_id)

                    UIUtils.show_message(
                        "Успех",
                        "Вход выполнен!",
                        callback=lambda: self.transition_to_options()
                    )
                else:
                    UIUtils.show_message("Ошибка", "Неверный пароль")
            else:
                UIUtils.show_message("Ошибка", "Пользователь не найден")

        except ValueError as e:
            UIUtils.show_message("Ошибка", str(e))
        except Exception as e:
            UIUtils.show_message("Ошибка БД", f"Ошибка при входе: {str(e)}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def transition_to_options(self):
        self.manager.transition = SlideTransition(direction='left', duration=0.3)
        self.manager.current = "options"

    def register(self):
        email = self.email.text.strip()
        name = self.name_field.text.strip()
        password = self.password.text.strip()
        confirm = self.confirm_password.text.strip()

        if not email or not name or not password or not confirm:
            UIUtils.show_message("Ошибка", "Заполните все поля")
            return

        try:
            validate_email(email)
            validate_name(name)
            validate_password(password, confirm)

            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
                if cursor.fetchone():
                    UIUtils.show_message("Ошибка", "Такой email уже зарегистрирован")
                    return

                password_hash = self.hash_password(password)
                cursor.execute(
                    "INSERT INTO users (email, password_hash, name) VALUES (%s, %s, %s)",
                    (email, password_hash, name)
                )
                conn.commit()

                cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
                user_id = cursor.fetchone()[0]
                app = MDApp.get_running_app()
                app.set_user_id(user_id)

            UIUtils.show_message(
                "Успех",
                "Регистрация завершена, теперь войдите",
                callback=lambda: self.switch_to_login_mode()
            )

        except ValueError as e:
            UIUtils.show_message("Ошибка", str(e))
        except Exception as e:
            UIUtils.show_message("Ошибка БД", f"Ошибка при регистрации: {str(e)}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def switch_to_login_mode(self):
        self.mode = "login"
        self._build_form(register=False)


class OptionsWindow(Screen):
    def go_to_history(self):
        self.manager.current = "story"

    def save_data(self):
        weight = self.ids.weight_input.text.strip()
        pressure_systolic = self.ids.pressure_systolic_input.text.strip()
        pressure_diastolic = self.ids.pressure_diastolic_input.text.strip()
        pulse = self.ids.pulse_input.text.strip()
        temperature = self.ids.temperature_input.text.strip()
        notes = self.ids.notes_input.text.strip()

        user_id = App.get_running_app().get_user_id()

        if not weight or not pressure_systolic or not pressure_diastolic or not pulse or not temperature:
            UIUtils.show_message("Ошибка", "Пожалуйста, заполните все поля!")
            return

        try:
            validate_weight(weight)
            validate_pressure_systolic(pressure_systolic)
            validate_pressure_diastolic(pressure_diastolic)
            validate_pulse(pulse)
            validate_temperature(temperature)
            validate_notes(notes)
        except ValueError as e:
            UIUtils.show_message("Ошибка", str(e))
            return

        record_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO records (user_id, weight, pressure_systolic, pressure_diastolic, pulse, temperature, notes, record_date) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (user_id, weight, pressure_systolic, pressure_diastolic, pulse, temperature, notes, record_date)
                )
                conn.commit()
                UIUtils.show_message("Успех", "Данные сохранены успешно!")
                self.clear_form()
        except Exception as e:
            UIUtils.show_message("Ошибка", f"Ошибка при сохранении данных: {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def clear_form(self):
        self.ids.weight_input.text = ""
        self.ids.pressure_systolic_input.text = ""
        self.ids.pressure_diastolic_input.text = ""
        self.ids.pulse_input.text = ""
        self.ids.temperature_input.text = ""
        self.ids.notes_input.text = ""


class HealthDiaryApp(MDApp):
    user_id = None

    def build(self):
        sm = ScreenManager()
        sm.add_widget(RegistrationWindow(name="registration"))
        sm.add_widget(OptionsWindow(name="options"))
        sm.add_widget(StoryWindow(name="story"))
        sm.add_widget(ProfileScreen(name="profile"))

        return sm

    def get_user_id(self):
        return self.user_id

    def set_user_id(self, user_id):
        self.user_id = user_id


if __name__ == "__main__":
    HealthDiaryApp().run()










