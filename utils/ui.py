from kivy.metrics import dp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton

class UIUtils:
    """
    Вспомогательный класс для создания UI-компонентов
    Содержит статические методы для часто используемых элементов интерфейса
    """

    @staticmethod
    def create_text_field(hint_text, password=False):
        """
        Создает стандартное текстовое поле ввода

        Args:
            hint_text (str): Подсказка в поле ввода
            password (bool): Если True, скрывает вводимый текст

        Returns:
            MDTextField: Сконфигурированное поле ввода
        """
        return MDTextField(
            hint_text=hint_text,
            mode="rectangle",
            password=password,
            size_hint=(None, None),
            width=dp(300),
            height=dp(48),
            pos_hint={"center_x": 0.5},
            line_color_normal=(0, 0, 1, 1),  # Синий цвет для светлой темы
            text_color_normal=(0, 0, 1, 1)
        )

    @staticmethod
    def show_message(title, text, callback=None):
        """
        Показывает диалоговое окно с сообщением

        Args:
            title (str): Заголовок окна
            text (str): Текст сообщения
            callback (function, optional): Функция, вызываемая при нажатии OK

        Returns:
            MDDialog: Созданное диалоговое окно
        """
        dialog = MDDialog(
            title=title,
            text=text,
            size_hint=(0.7, None),
            buttons=[
                MDRaisedButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),  # Белый текст
                    md_bg_color=(0, 0, 1, 1),  # Синий фон
                    on_release=lambda x: (dialog.dismiss(), callback() if callback else None)
                )
            ]
        )
        dialog.open()
        return dialog

class CustomMDRaisedButton(MDRaisedButton):
    """
    Кастомная кнопка с отключенным эффектом ripple (волны при нажатии)
    Наследуется от стандартной кнопки MDRaisedButton
    """

    def __init__(self, **kwargs):
        """Инициализация кастомной кнопки с отключенным ripple-эффектом"""
        super().__init__(**kwargs)
        self.ripple_scale = 0  # Отключаем эффект волны

