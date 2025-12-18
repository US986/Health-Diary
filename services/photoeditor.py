import os
import base64
from io import BytesIO

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.properties import StringProperty

from kv import PHOTOEDITOR_KV

Builder.load_string(PHOTOEDITOR_KV)

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

class SimplePhotoEditor(BoxLayout):
    """
    Простой редактор фотографий для создания круглых аватаров

    Позволяет:
    1. Поворачивать изображение
    2. Обрезать изображение до круглой формы
    3. Сохранять результат в формате base64
    """

    def __init__(self, image_path, callback, **kwargs):
        """
        Инициализация редактора фотографий

        Args:
            image_path (str): Путь к исходному изображению
            callback (function): Функция обратного вызова для сохранения результата
        """
        super().__init__(**kwargs)
        self.image_path = image_path  # Путь к исходному изображению
        self.callback = callback  # Функция обратного вызова
        self.current_image = None  # Текущее изображение в памяти
        self.rotation = 0  # Текущий угол поворота
        self.temp_files = []  # Список временных файлов для очистки

        # Планируем загрузку изображения с небольшой задержкой
        Clock.schedule_once(self.load_image, 0.1)

    def load_image(self, dt):
        """
        Загружает изображение для редактирования

        Args:
            dt (float): Время задержки (не используется)
        """
        try:
            if os.path.exists(self.image_path):
                self.current_image = PILImage.open(self.image_path)
                self.ids.preview_image.source = self.image_path
        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")

    def rotate_image(self, angle):
        """
        Поворачивает изображение на заданный угол

        Args:
            angle (int): Угол поворота в градусах
        """
        if self.current_image:
            try:
                # Обновляем текущий угол поворота
                self.rotation = (self.rotation + angle) % 360

                # Поворачиваем изображение
                rotated_image = self.current_image.rotate(angle, expand=True)

                # Сохраняем во временный файл
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_path = temp_file.name
                temp_file.close()
                rotated_image.save(temp_path, "PNG")

                # Обновляем превью
                self.ids.preview_image.source = temp_path
                self.current_image = rotated_image
                self.temp_files.append(temp_path)
            except Exception as e:
                print(f"Ошибка поворота изображения: {e}")

    def create_circular_avatar(self):
        """
        Создает круглое изображение для аватара

        Returns:
            PIL.Image: Круглое изображение или None в случае ошибки
        """
        if not self.current_image:
            return None
        try:
            # Определяем минимальную сторону для создания квадрата
            size = min(self.current_image.size)

            # Координаты для обрезки квадрата
            left = (self.current_image.width - size) // 2
            top = (self.current_image.height - size) // 2
            right = left + size
            bottom = top + size

            # Обрезаем до квадрата
            cropped_square = self.current_image.crop((left, top, right, bottom))

            # Создаем маску для круга
            mask = PILImage.new('L', (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)

            # Конвертируем в RGBA если нужно
            if cropped_square.mode != 'RGBA':
                cropped_square = cropped_square.convert('RGBA')

            # Создаем круглое изображение
            circular_image = PILImage.new('RGBA', (size, size), (0, 0, 0, 0))
            circular_image.paste(cropped_square, (0, 0), mask)

            return circular_image
        except Exception as e:
            print(f"Ошибка создания круглого аватара: {e}")
            return None

    def cancel(self):
        """
        Отмена редактирования - закрывает редактор и очищает временные файлы
        """
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        self.callback(None)

    def save(self):
        """
        Сохраняет отредактированное изображение

        Конвертирует в круглую форму и кодирует в base64
        """
        try:
            # Создаем круглый аватар
            circular_image = self.create_circular_avatar()
            if circular_image:
                # Конвертируем в base64
                buffer = BytesIO()
                circular_image.save(buffer, format="PNG")
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                buffer.close()

                # Очищаем временные файлы
                for temp_file in self.temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                    except:
                        pass

                # Вызываем callback с результатом
                self.callback(image_data)
            else:
                self.callback(None)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            self.callback(None)