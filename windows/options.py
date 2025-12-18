from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.app import App

# Импорт компонентов KivyMD (Material Design)
from kivymd.app import MDApp

# Импорт пользовательских модулей
from database import get_connection, insert_record
from utils.ui import UIUtils
from utils.rules import (
    validate_weight,  # Валидация веса
    validate_pressure_systolic,  # Валидация систолического давления
    validate_pressure_diastolic,  # Валидация диастолического давления
    validate_pulse,  # Валидация пульса
    validate_temperature,  # Валидация температуры
    validate_notes  # Валидация заметок
)

class OptionsWindow(Screen):
    """
    Главный экран приложения - ввод данных о здоровье

    Позволяет пользователю вводить:
    - Вес
    - Артериальное давление (систолическое и диастолическое)
    - Пульс
    - Температуру тела
    - Заметки
    """

    def on_pre_enter(self):
        """
        Метод, вызываемый перед переходом на этот экран

        Применяет настройки пользователя (тему) перед показом экрана
        """
        app = MDApp.get_running_app()
        if hasattr(app, 'apply_user_settings_immediately'):
            app.apply_user_settings_immediately()

    def go_to_history(self):
        """
        Переход к экрану истории записей

        Вызывается при нажатии кнопки "История записей"
        """
        self.manager.current = "story"

    def save_data(self):
        """
        Сохраняет введенные данные о здоровье в базу данных

        Выполняет валидацию всех полей перед сохранением
        """
        # Получаем значения из полей ввода
        weight = self.ids.weight_input.text.strip()
        pressure_systolic = self.ids.pressure_systolic_input.text.strip()
        pressure_diastolic = self.ids.pressure_diastolic_input.text.strip()
        pulse = self.ids.pulse_input.text.strip()
        temperature = self.ids.temperature_input.text.strip()
        notes = self.ids.notes_input.text.strip()

        # Получаем ID текущего пользователя
        user_id = App.get_running_app().get_user_id()

        # Проверка обязательных полей
        if not weight or not pressure_systolic or not pressure_diastolic or not pulse or not temperature:
            UIUtils.show_message("Ошибка", "Пожалуйста, заполните все поля!")
            return

        try:
            # Валидация всех полей
            validate_weight(weight)
            validate_pressure_systolic(pressure_systolic)
            validate_pressure_diastolic(pressure_diastolic)
            validate_pulse(pulse)
            validate_temperature(temperature)
            validate_notes(notes)
        except ValueError as e:
            # Ошибка валидации
            UIUtils.show_message("Ошибка", str(e))
            return

        # Текущая дата и время для записи
        record_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = None
        try:
            # Сохранение в базу данных
            conn = get_connection()
            insert_record(conn, user_id, weight, pressure_systolic, pressure_diastolic, pulse, temperature, notes, record_date)
            UIUtils.show_message("Успех", "Данные сохранены успешно!")
            self.clear_form()  # Очищаем форму после успешного сохранения
        except Exception as e:
            UIUtils.show_message("Ошибка", f"Ошибка при сохранении данных: {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def clear_form(self):
        """
        Очищает все поля формы ввода

        Вызывается после успешного сохранения данных
        """
        self.ids.weight_input.text = ""
        self.ids.pressure_systolic_input.text = ""
        self.ids.pressure_diastolic_input.text = ""
        self.ids.pulse_input.text = ""
        self.ids.temperature_input.text = ""
        self.ids.notes_input.text = ""
