from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDFloatingActionButton
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivymd.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from base import get_connection
from kivy.clock import Clock
import os
from PIL import Image as PILImage
from kivy.utils import platform
from kivy.garden.filebrowser import FileBrowser
from kivy.uix.modalview import ModalView
from kivy.uix.scatter import Scatter
from kivy.graphics import Color, Ellipse, Rectangle, Line
import tempfile
import base64
from io import BytesIO
from kivy.properties import NumericProperty, ListProperty

KV = '''
<ProfileScreen>:
    name: 'profile'
    BoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "15dp"

        MDLabel:
            text: "Профиль"
            halign: "center"
            theme_text_color: "Primary"
            font_style: "H5"
            size_hint_y: None
            height: dp(40)

        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: dp(250)
            spacing: "10dp"
            pos_hint: {"center_x": 0.5}

            Image:
                id: profile_image
                source: ""
                size_hint: None, None
                size: dp(200), dp(200)
                pos_hint: {"center_x": 0.5}
                allow_stretch: True
                keep_ratio: True
                canvas.before:
                    Color:
                        rgba: 0.9, 0.9, 0.9, 1
                    Ellipse:
                        pos: self.pos
                        size: self.size

        MDLabel:
            id: user_info
            text: "Загрузка данных..."
            halign: "center"
            theme_text_color: "Secondary"
            font_style: "Subtitle1"
            size_hint_y: None
            height: dp(60)

        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: dp(100)
            spacing: "10dp"
            padding: "10dp"

            MDRaisedButton:
                text: "Изменить данные"
                size_hint_y: None
                height: dp(48)
                md_bg_color: app.theme_cls.primary_color
                text_color: 1, 1, 1, 1
                on_release: root.change_profile()

            MDRaisedButton:
                text: "Сменить фото"
                size_hint_y: None
                height: dp(48)
                md_bg_color: app.theme_cls.primary_color
                text_color: 1, 1, 1, 1
                on_release: root.show_photo_menu()

        BoxLayout:
            size_hint_y: None
            height: "60dp"
            orientation: "horizontal"
            padding: "8dp"
            spacing: "12dp"
            pos_hint: {"center_x": 0.5}

            MDFloatingActionButton:
                icon: "arrow-left"
                md_bg_color: app.theme_cls.primary_color
                on_release: root.go_back()

            MDFloatingActionButton:
                icon: "logout"
                md_bg_color: 1, 0, 0, 1
                on_release: root.logout()

<PhotoEditorDialog>:
    orientation: "vertical"
    spacing: "15dp"
    padding: "20dp"
    size_hint_y: None
    height: dp(600)

    BoxLayout:
        size_hint_y: None
        height: dp(400)
        padding: "10dp"

        RelativeLayout:
            id: crop_container
            size_hint: None, None
            size: dp(350), dp(350)
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            canvas:
                Color:
                    rgba: 0.95, 0.95, 0.95, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            Image:
                id: preview_image
                size_hint: None, None
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                allow_stretch: True
                keep_ratio: True

            Widget:
                id: crop_circle
                size_hint: None, None
                size: dp(120), dp(120)
                pos: (dp(350)-dp(120))/2, (dp(350)-dp(120))/2  
                canvas:
                    Color:
                        rgba: 0, 0, 0, 0.3
                    Ellipse:
                        pos: self.pos
                        size: self.size
                    Color:
                        rgba: 1, 1, 1, 1
                    Line:
                        ellipse: (self.pos[0], self.pos[1], self.size[0], self.size[1])
                        width: 2

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: "10dp"

        MDRaisedButton:
            text: "Повернуть вправо"
            size_hint_x: 0.5
            md_bg_color: app.theme_cls.primary_color
            on_release: root.rotate_image()

        MDRaisedButton:
            text: "Повернуть влево"
            size_hint_x: 0.5
            md_bg_color: app.theme_cls.primary_color
            on_release: root.rotate_image_counter_clockwise()

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: "10dp"

        MDRaisedButton:
            text: "Отмена"
            size_hint_x: 0.5
            md_bg_color: 0.7, 0.7, 0.7, 1
            text_color: 1, 1, 1, 1
            on_release: root.cancel()

        MDRaisedButton:
            text: "Сохранить"
            size_hint_x: 0.5
            md_bg_color: app.theme_cls.primary_color
            text_color: 1, 1, 1, 1
            on_release: root.save()
'''

Builder.load_string(KV)


class PhotoEditorDialog(BoxLayout):
    circle_x = NumericProperty(0)
    circle_y = NumericProperty(0)
    circle_size = NumericProperty(120)

    def __init__(self, image_path, callback, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.callback = callback
        self.current_image = None
        self.rotation = 0
        self.original_image = None
        self.image_widget = None
        self.crop_container = None
        self.circle_widget = None
        self.image_display_info = None
        self._touch_start_pos = None
        self._circle_start_pos = None

        Clock.schedule_once(self.load_image, 0.1)

    def load_image(self, dt):
        if os.path.exists(self.image_path):
            try:
                self.current_image = PILImage.open(self.image_path)
                self.original_image = self.current_image.copy()

                self.ids.preview_image.source = self.image_path

                self.image_widget = self.ids.preview_image
                self.crop_container = self.ids.crop_container
                self.circle_widget = self.ids.crop_circle

                self.center_circle()

                Clock.schedule_once(self.update_image_display_info, 0.2)

            except Exception as e:
                print(f"Ошибка загрузки изображения: {e}")

    def center_circle(self):
        container_size = 350
        circle_size = 120

        center_x = (container_size - circle_size) / 2
        center_y = (container_size - circle_size) / 2

        self.circle_widget.pos = (center_x, center_y)
        self.circle_x = center_x
        self.circle_y = center_y

    def update_image_display_info(self, dt=None):
        if not self.image_widget or not self.current_image:
            return

        img_width, img_height = self.current_image.size
        container_size = 350

        if self.image_widget.keep_ratio:
            img_ratio = img_width / img_height
            container_ratio = 1.0

            if img_ratio > container_ratio:
                displayed_width = container_size
                displayed_height = displayed_width / img_ratio
                offset_x = 0
                offset_y = (container_size - displayed_height) / 2
            else:
                displayed_height = container_size
                displayed_width = displayed_height * img_ratio
                offset_x = (container_size - displayed_width) / 2
                offset_y = 0
        else:
            displayed_width = container_size
            displayed_height = container_size
            offset_x = 0
            offset_y = 0

        self.image_display_info = {
            'displayed_width': displayed_width,
            'displayed_height': displayed_height,
            'offset_x': offset_x,
            'offset_y': offset_y,
            'img_width': img_width,
            'img_height': img_height,
            'container_size': container_size
        }

        self.image_widget.size = (displayed_width, displayed_height)

    def on_touch_down(self, touch):
        if self.circle_widget and self.crop_container:
            circle_pos = self.circle_widget.pos
            circle_size = self.circle_size

            container_x = self.crop_container.x
            container_y = self.crop_container.y
            local_x = touch.x - container_x
            local_y = touch.y - container_y

            if (circle_pos[0] <= local_x <= circle_pos[0] + circle_size and
                    circle_pos[1] <= local_y <= circle_pos[1] + circle_size):
                self._touch_start_pos = (touch.x, touch.y)
                self._circle_start_pos = (self.circle_x, self.circle_y)
                return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._touch_start_pos and self._circle_start_pos and self.image_display_info:
            dx = touch.x - self._touch_start_pos[0]
            dy = touch.y - self._touch_start_pos[1]

            new_x = self._circle_start_pos[0] + dx
            new_y = self._circle_start_pos[1] + dy

            info = self.image_display_info
            circle_size = self.circle_size

            min_x = info['offset_x']
            min_y = info['offset_y']
            max_x = min_x + info['displayed_width'] - circle_size
            max_y = min_y + info['displayed_height'] - circle_size

            new_x = max(min_x, min(new_x, max_x))
            new_y = max(min_y, min(new_y, max_y))

            self.circle_widget.pos = (new_x, new_y)
            self.circle_x = new_x
            self.circle_y = new_y

            return True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        self._touch_start_pos = None
        self._circle_start_pos = None
        return super().on_touch_up(touch)

    def rotate_image(self):
        if self.current_image:
            self.rotation = (self.rotation + 90) % 360
            rotated_image = self.current_image.rotate(-90, expand=True)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_path = temp_file.name
            temp_file.close()

            rotated_image.save(temp_path, "PNG")
            self.ids.preview_image.source = temp_path
            self.current_image = rotated_image

            Clock.schedule_once(self.update_image_display_info, 0.1)

    def rotate_image_counter_clockwise(self):
        if self.current_image:
            self.rotation = (self.rotation - 90) % 360
            rotated_image = self.current_image.rotate(90, expand=True)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_path = temp_file.name
            temp_file.close()

            rotated_image.save(temp_path, "PNG")
            self.ids.preview_image.source = temp_path
            self.current_image = rotated_image

            Clock.schedule_once(self.update_image_display_info, 0.1)

    def create_circular_avatar(self):
        if not self.current_image or not self.image_display_info:
            return None

        try:
            circle_x, circle_y = self.circle_widget.pos
            circle_size = self.circle_size

            info = self.image_display_info
            offset_x = info['offset_x']
            offset_y = info['offset_y']
            displayed_width = info['displayed_width']
            displayed_height = info['displayed_height']
            img_width = info['img_width']
            img_height = info['img_height']

            circle_rel_x = circle_x - offset_x
            circle_rel_y = circle_y - offset_y

            scale_x = img_width / displayed_width
            scale_y = img_height / displayed_height

            img_circle_x = circle_rel_x * scale_x
            img_circle_y = circle_rel_y * scale_y

            img_circle_size = circle_size * scale_x

            img_circle_x = max(0, min(img_circle_x, img_width - img_circle_size))
            img_circle_y = max(0, min(img_circle_y, img_height - img_circle_size))

            left = img_circle_x
            top = img_circle_y
            right = left + img_circle_size
            bottom = top + img_circle_size

            avatar_size = 400

            cropped_square = self.current_image.crop((left, top, right, bottom))

            cropped_square = cropped_square.resize((avatar_size, avatar_size), PILImage.Resampling.LANCZOS)

            mask = PILImage.new('L', (avatar_size, avatar_size), 0)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)

            if cropped_square.mode != 'RGBA':
                cropped_square = cropped_square.convert('RGBA')

            circular_image = PILImage.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
            circular_image.paste(cropped_square, (0, 0), mask)

            return circular_image

        except Exception as e:
            print(f"Ошибка создания круглого аватара: {e}")
            import traceback
            traceback.print_exc()
            return None

    def cancel(self):
        self.callback(None)

    def save(self):
        circular_image = self.create_circular_avatar()
        if circular_image:
            try:
                buffer = BytesIO()
                circular_image.save(buffer, format="PNG")
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                buffer.close()

                self.callback(image_data)
            except Exception as e:
                print(f"Ошибка сохранения изображения: {e}")
                self.callback(None)
        else:
            self.callback(None)


class ProfileScreen(Screen):
    dialog = None
    photo_menu = None
    file_browser_view = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_info_label = None
        self.profile_image_widget = None

    def on_pre_enter(self):
        Clock.schedule_once(lambda dt: self.load_user_data(), 0.1)

    def on_kv_post(self, base_widget):
        if hasattr(self, 'ids'):
            self.user_info_label = self.ids.user_info
            self.profile_image_widget = self.ids.profile_image

    def is_mobile(self):
        return platform in ('android', 'ios')

    def show_photo_menu(self):
        if self.is_mobile():
            self.show_mobile_photo_chooser()
        else:
            self.open_file_browser()

    def show_mobile_photo_chooser(self):
        menu_items = [
            {
                "text": "Сделать фото",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="camera": self.select_photo_source(x),
            },
            {
                "text": "Выбрать из галереи",
                "viewclass": "OneLineListItem",
                "on_release": lambda x="gallery": self.select_photo_source(x),
            }
        ]

        self.photo_menu = MDDropdownMenu(
            caller=self.profile_image_widget,
            items=menu_items,
            width_mult=4,
        )
        self.photo_menu.open()

    def select_photo_source(self, source):
        if self.photo_menu:
            self.photo_menu.dismiss()

        if source == "camera":
            self.show_message("Инфо", "Функция камеры будет добавлена позже")
            self.open_file_browser()
        elif source == "gallery":
            self.open_file_browser()

    def open_file_browser(self):
        try:
            def file_selected(instance):
                if instance.selection:
                    selected_file = instance.selection[0]
                    self.file_browser_view.dismiss()
                    Clock.schedule_once(lambda dt: self.open_photo_editor(selected_file), 0.1)

            def file_canceled(instance):
                self.file_browser_view.dismiss()

            file_browser = FileBrowser(
                select_string='Выбрать',
                cancel_string='Отмена',
                filters=['*.png', '*.jpg', '*.jpeg'],
                multiselect=False
            )
            file_browser.bind(on_success=file_selected)
            file_browser.bind(on_canceled=file_canceled)

            self.file_browser_view = ModalView(size_hint=(0.9, 0.9))
            self.file_browser_view.add_widget(file_browser)
            self.file_browser_view.open()

        except Exception as e:
            self.show_message("Ошибка", f"Ошибка открытия файлового браузера: {str(e)}")
            print(f"FileBrowser error: {e}")

    def open_photo_editor(self, image_path):
        print(f"Opening photo editor with: {image_path}")
        if image_path and os.path.exists(image_path):
            try:
                editor = PhotoEditorDialog(image_path, self.on_photo_edited)

                self.dialog = MDDialog(
                    title="Выбор области для аватара",
                    type="custom",
                    content_cls=editor,
                    size_hint=(0.95, 0.95)
                )
                self.dialog.open()
            except Exception as e:
                self.show_message("Ошибка", f"Ошибка загрузки фото: {str(e)}")
                print(f"Photo editor error: {e}")
        else:
            self.show_message("Ошибка", f"Файл не найден: {image_path}")

    def on_photo_edited(self, image_data_base64):
        if self.dialog:
            self.dialog.dismiss()

        if image_data_base64:
            print("Photo edited, saving to database")
            self.save_profile_photo_to_db(image_data_base64)
            self.display_profile_image_from_base64(image_data_base64)
            self.show_message("Успех", "Фото профиля обновлено")
        else:
            print("Photo editing cancelled")

    def load_user_data(self):
        try:
            user_id = MDApp.get_running_app().get_user_id()
            if not user_id:
                self._set_user_info_text("Пользователь не авторизован")
                return

            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT name, email, created_at, profile_photo FROM users WHERE id = %s", (user_id,))
                user_data = cursor.fetchone()

            if user_data:
                name, email, created_at, profile_photo = user_data
                date_str = created_at.strftime('%d.%m.%Y') if created_at else "неизвестно"
                info_text = f"{name}\n{email}\nЗарегистрирован: {date_str}"
                self._set_user_info_text(info_text)

                if profile_photo:
                    self.display_profile_image_from_base64(profile_photo)

        except Exception as e:
            self._set_user_info_text(f"Ошибка загрузки: {str(e)}")
            print(f"Ошибка загрузки данных: {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def display_profile_image_from_base64(self, image_data_base64):
        try:
            if not image_data_base64:
                return

            image_data = base64.b64decode(image_data_base64)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_path = temp_file.name
            temp_file.write(image_data)
            temp_file.close()

            if self.profile_image_widget:
                self.profile_image_widget.source = temp_path
            elif hasattr(self, 'ids') and 'profile_image' in self.ids:
                self.ids.profile_image.source = temp_path

        except Exception as e:
            print(f"Ошибка отображения изображения: {e}")

    def _set_user_info_text(self, text):
        try:
            if self.user_info_label:
                self.user_info_label.text = text
            elif hasattr(self, 'ids') and 'user_info' in self.ids:
                self.ids.user_info.text = text
        except Exception as e:
            print(f"Ошибка установки текста: {e}")

    def save_profile_photo_to_db(self, image_data_base64):
        user_id = MDApp.get_running_app().get_user_id()
        if not user_id:
            return

        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET profile_photo = %s WHERE id = %s",
                    (image_data_base64, user_id)
                )
                conn.commit()
            print("Фото сохранено в базу данных")
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка сохранения фото: {str(e)}")
            print(f"Ошибка сохранения фото в базу: {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def change_profile(self):
        user_id = MDApp.get_running_app().get_user_id()
        if not user_id:
            self.show_message("Ошибка", "Пользователь не авторизован")
            return

        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT name, email FROM users WHERE id = %s", (user_id,))
                user_data = cursor.fetchone()
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

        self.dialog = MDDialog(
            title="Редактировать профиль",
            type="custom",
            content_cls=edit_box,
            buttons=[
                MDRaisedButton(
                    text="Отмена",
                    md_bg_color=(0.7, 0.7, 0.7, 1),
                    text_color=(1, 1, 1, 1),
                    on_release=lambda _: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Сохранить",
                    md_bg_color=MDApp.get_running_app().theme_cls.primary_color,
                    text_color=(1, 1, 1, 1),
                    on_release=lambda _: self.save_profile_changes(
                        name_input.text,
                        email_input.text
                    )
                ),
            ],
        )
        self.dialog.open()

    def save_profile_changes(self, name, email):
        user_id = MDApp.get_running_app().get_user_id()

        if not name.strip():
            self.show_message("Ошибка", "Имя не может быть пустым")
            return

        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET name = %s, email = %s WHERE id = %s",
                    (name.strip(), email.strip(), user_id)
                )
                conn.commit()

            self.show_message("Успех", "Профиль обновлен")
            self.dialog.dismiss()
            self.load_user_data()

        except Exception as e:
            self.show_message("Ошибка", f"Ошибка сохранения: {str(e)}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def logout(self):
        app = MDApp.get_running_app()
        app.set_user_id(None)
        app.root.current = "registration"

    def go_back(self):
        self.manager.current = "story"

    def show_message(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    md_bg_color=MDApp.get_running_app().theme_cls.primary_color,
                    text_color=(1, 1, 1, 1),
                    on_release=lambda _: dialog.dismiss()
                )
            ]
        )
        dialog.open()

