"""
Модуль административной панели приложения "Дневник здоровья"
Содержит экраны для управления пользователями и просмотра записей
"""

import os
import platform
from datetime import datetime
import socket

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import TwoLineListItem, ThreeLineListItem
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout

from database import (
get_connection,
select_all_users,
select_user_records_by_admin,
select_all_records,
insert_admin_action,
update_user_admin_status,
get_user_statistics,
select_admin_actions
)

from kv import ADMIN_KV
# Builder.load_string(ADMIN_KV)


class AdminDashboard(Screen):
    """
    Административная панель - главный экран

    Позволяет администратору:
    1. Просматривать статистику приложения
    2. Переходить к управлению пользователями
    3. Переходить к просмотру записей
    4. Просматривать журнал действий администраторов
    """

    def on_pre_enter(self):
        """
        Метод, вызываемый перед переходом на экран

        Проверяет права администратора и загружает статистику
        """
        # Проверяем, является ли пользователь администратором
        app = MDApp.get_running_app()
        if not getattr(app, 'is_admin', False):
            self.show_message("Доступ запрещен", "Только администраторы могут просматривать эту страницу")
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'profile'), 0.5)
            return

        # Загружаем статистику
        self.load_statistics()

        # Записываем действие администратора
        self.log_admin_action("view_dashboard", "Просмотр административной панели")

    def load_statistics(self):
        """
        Загружает и отображает статистику приложения
        """
        try:
            conn = get_connection()
            stats = get_user_statistics(conn)

            # Отображаем статистику
            if stats:
                if hasattr(self.ids, 'stats_container'):
                    self.ids.stats_container.clear_widgets()

                    # Создаем карточки со статистикой
                    stats_cards = [
                        ("Пользователи", f"{stats.get('total_users', 0)}", "account-group"),
                        ("Записи", f"{stats.get('total_records', 0)}", "note-multiple"),
                        ("Администраторы", f"{stats.get('total_admins', 0)}", "shield-account"),
                        ("Сессии", f"{stats.get('total_sessions', 0)}", "login"),
                        ("Записей за 7 дней", f"{stats.get('records_last_7_days', 0)}", "calendar-week"),
                        ("Активных за 30 дней", f"{stats.get('active_users_30_days', 0)}", "account-check"),
                    ]

                    for title, value, icon in stats_cards:
                        card = self.create_stat_card(title, value, icon)
                        self.ids.stats_container.add_widget(card)

            conn.close()
        except Exception as e:
            print(f"Ошибка загрузки статистики: {e}")

    def create_stat_card(self, title, value, icon):
        """
        Создает карточку со статистикой

        Args:
            title: Заголовок карточки
            value: Значение
            icon: Иконка

        Returns:
            MDCard: Карточка со статистикой
        """
        card = MDCard(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10),
            size_hint=(None, None),
            size=(dp(150), dp(120)),
            elevation=3,
            ripple_behavior=True,
            radius=[dp(10), dp(10), dp(10), dp(10)]
        )

        # Заголовок
        title_layout = MDBoxLayout(orientation="horizontal", spacing=dp(10))
        title_layout.add_widget(MDLabel(
            text=title,
            theme_text_color="Secondary",
            font_style="Caption",
            halign="left",
            size_hint_x=0.8
        ))

        card.add_widget(title_layout)

        # Значение
        card.add_widget(MDLabel(
            text=value,
            theme_text_color="Primary",
            font_style="H5",
            halign="center",
            bold=True
        ))

        return card

    def go_to_users(self):
        """Переход к управлению пользователями"""
        self.manager.current = "admin_users"

    def go_to_records(self):
        """Переход к просмотру записей"""
        self.manager.current = "admin_records"

    def go_to_audit_log(self):
        """Переход к журналу действий"""
        self.manager.current = "admin_audit"

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
                    md_bg_color=(0, 0, 1, 1),
                    on_release=lambda _: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def log_admin_action(self, action_type, details, affected_user_id=None):
        """
        Записывает действие администратора в журнал

        Args:
            action_type: Тип действия
            details: Детали действия
            affected_user_id: ID затронутого пользователя
        """
        try:
            app = MDApp.get_running_app()
            user_id = app.get_user_id()

            # Получаем IP адрес
            ip_address = None
            try:
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
            except:
                ip_address = "unknown"

            conn = get_connection()
            insert_admin_action(
                conn,
                user_id,
                action_type,
                details,
                affected_user_id,
                ip_address
            )
            conn.close()
        except Exception as e:
            print(f"Ошибка записи действия администратора: {e}")

    def go_back(self):
        """Возврат к профилю пользователя"""
        self.manager.current = "profile"

class AdminUsersScreen(Screen):
    """
    Экран управления пользователями для администратора
    """

    users_menu = None
    selected_user_id = None

    def on_pre_enter(self):
        """
        Метод, вызываемый перед переходом на экран
        """
        # Проверяем права администратора
        app = MDApp.get_running_app()
        if not getattr(app, 'is_admin', False):
            self.show_message("Доступ запрещен", "Только администраторы могут просматривать эту страницу")
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'profile'), 0.5)
            return

        # Загружаем пользователей
        self.load_users()

        # Записываем действие администратора
        app = MDApp.get_running_app()
        # Используем прямую запись в базу данных вместо app.admin_dashboard
        self.log_admin_action_direct("view_users", "Просмотр списка пользователей")

    def log_admin_action_direct(self, action_type, details, affected_user_id=None):
        """
        Прямая запись действия администратора в базу данных

        Args:
            action_type: Тип действия
            details: Детали действия
            affected_user_id: ID затронутого пользователя
        """
        try:
            app = MDApp.get_running_app()
            user_id = app.get_user_id()

            # Получаем IP адрес
            ip_address = None
            try:
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
            except:
                ip_address = "unknown"

            conn = get_connection()
            insert_admin_action(
                conn,
                user_id,
                action_type,
                details,
                affected_user_id,
                ip_address
            )
            conn.close()
        except Exception as e:
            print(f"Ошибка записи действия администратора: {e}")

    def load_users(self, search_query=None):
        """
        Загружает список пользователей

        Args:
            search_query: Текст для поиска пользователей
        """
        try:
            conn = get_connection()
            users = select_all_users(conn)

            if hasattr(self.ids, 'users_list'):
                self.ids.users_list.clear_widgets()

                if users:
                    # Фильтруем пользователей, если есть поисковый запрос
                    filtered_users = []
                    if search_query and search_query.strip():
                        query_lower = search_query.lower()
                        for user in users:
                            user_id, name, email, created_at, is_admin = user
                            if (query_lower in name.lower() or
                                    query_lower in email.lower() or
                                    query_lower in str(user_id)):
                                filtered_users.append(user)
                    else:
                        filtered_users = users

                    # Отображаем пользователей
                    for user in filtered_users:
                        user_id, name, email, created_at, is_admin = user

                        # Форматируем дату
                        try:
                            if isinstance(created_at, str):
                                created_date = datetime.strptime(created_at.split()[0], "%Y-%m-%d")
                            else:
                                created_date = created_at
                            formatted_date = created_date.strftime("%d.%m.%Y")
                        except:
                            formatted_date = str(created_at)

                        # Создаем элемент списка
                        item = ThreeLineListItem(
                            text=f"{name} ({'Администратор' if is_admin else 'Пользователь'})",
                            secondary_text=f"Email: {email}",
                            tertiary_text=f"ID: {user_id} | Создан: {formatted_date}",
                            bg_color=(0.9, 0.95, 1, 0.3) if is_admin else (1, 1, 1, 1)
                        )

                        # Привязываем обработчик для просмотра записей пользователя
                        item.bind(on_release=lambda x, uid=user_id: self.view_user_records(uid))

                        # Добавляем контекстное меню
                        item.bind(on_long_press=lambda x, uid=user_id, name=name, is_admin=is_admin:
                        self.show_user_menu(uid, name, is_admin, x))

                        self.ids.users_list.add_widget(item)
                else:
                    # Нет пользователей
                    self.ids.users_list.add_widget(MDLabel(
                        text="Пользователи не найдены",
                        halign="center",
                        theme_text_color="Secondary",
                        font_style="H6"
                    ))

            conn.close()
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка загрузки пользователей: {str(e)}")

    def on_search(self, instance, value):
        """
        Обработчик поиска пользователей

        Args:
            instance: Поле ввода
            value: Текст поиска
        """
        self.load_users(search_query=value)

    def show_user_menu(self, user_id, user_name, is_admin, list_item):
        """
        Показывает контекстное меню для пользователя

        Args:
            user_id: ID пользователя
            user_name: Имя пользователя
            is_admin: Статус администратора
            list_item: Элемент списка
        """
        # Создаем пункты меню
        menu_items = [
            {
                "text": "Просмотреть записи",
                "viewclass": "OneLineListItem",
                "on_release": lambda uid=user_id: self.view_user_records(uid)
            },
            {
                "text": "Сделать администратором" if not is_admin else "Убрать администратора",
                "viewclass": "OneLineListItem",
                "on_release": lambda uid=user_id, admin_status=not is_admin:
                self.toggle_admin_status(uid, admin_status, user_name)
            },
        ]

        # Создаем меню
        self.users_menu = MDDropdownMenu(
            caller=list_item,
            items=menu_items,
            width_mult=4,
        )

        # Сохраняем ID выбранного пользователя
        self.selected_user_id = user_id

        # Открываем меню
        self.users_menu.open()

    def view_user_records(self, user_id):
        """
        Переход к записям конкретного пользователя

        Args:
            user_id: ID пользователя
        """
        # Сохраняем ID пользователя в приложении для использования в AdminRecordsScreen
        app = MDApp.get_running_app()
        app.selected_user_id = user_id

        # Переходим к записям
        self.manager.current = "admin_records"

        # Записываем действие
        self.log_admin_action_direct("view_user_records", f"Просмотр записей пользователя ID: {user_id}", user_id)

    def toggle_admin_status(self, user_id, new_status, user_name):
        """
        Изменяет статус администратора пользователя

        Args:
            user_id: ID пользователя
            new_status: Новый статус (True - администратор, False - пользователь)
            user_name: Имя пользователя
        """
        # Закрываем меню
        if self.users_menu:
            self.users_menu.dismiss()

        # Подтверждение действия
        action = "назначить администратором" if new_status else "убрать из администраторов"

        dialog = MDDialog(
            title="Подтверждение",
            text=f"Вы уверены, что хотите {action} пользователя {user_name}?",
            buttons=[
                MDFlatButton(
                    text="Отмена",
                    theme_text_color="Custom",
                    text_color=(0.5, 0.5, 0.5, 1),
                    on_release=lambda _: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Подтвердить",
                    md_bg_color=(0.2, 0.6, 0.2, 1) if new_status else (0.8, 0.2, 0.2, 1),
                    on_release=lambda _: self.perform_toggle_admin(user_id, new_status, user_name, dialog)
                )
            ]
        )
        dialog.open()

    def perform_toggle_admin(self, user_id, new_status, user_name, dialog):
        """
        Выполняет изменение статуса администратора

        Args:
            user_id: ID пользователя
            new_status: Новый статус
            user_name: Имя пользователя
            dialog: Диалоговое окно
        """
        try:
            conn = get_connection()
            update_user_admin_status(conn, user_id, new_status)
            conn.close()

            dialog.dismiss()

            # Показываем сообщение об успехе
            status_text = "администратором" if new_status else "обычным пользователем"
            self.show_message("Успех", f"Пользователь {user_name} теперь {status_text}")

            # Обновляем список пользователей
            self.load_users()

            # Записываем действие
            action_details = f"Изменение статуса администратора для пользователя {user_name} (ID: {user_id}) на {status_text}"
            self.log_admin_action_direct("toggle_admin", action_details, user_id)

        except Exception as e:
            self.show_message("Ошибка", f"Ошибка изменения статуса: {str(e)}")

    def show_message(self, title, text):
        """Показывает диалоговое окно с сообщением"""
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    md_bg_color=(0, 0, 1, 1),
                    on_release=lambda _: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def go_back(self):
        """Возврат к административной панели"""
        self.manager.current = "admin_dashboard"

class AdminRecordsScreen(Screen):
    """
    Экран просмотра записей всех пользователей для администратора
    """

    selected_filter = "all"  # all, specific_user
    search_query = ""

    def on_pre_enter(self):
        """
        Метод, вызываемый перед переходом на экран
        """
        # Проверяем права администратора
        app = MDApp.get_running_app()
        if not getattr(app, 'is_admin', False):
            self.show_message("Доступ запрещен", "Только администраторы могут просматривать эту страницу")
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'profile'), 0.5)
            return

        # Загружаем записи
        self.load_records()

        # Записываем действие администратора
        filter_type = "записей всех пользователей"
        if hasattr(app, 'selected_user_id') and app.selected_user_id:
            filter_type = f"записей пользователя ID: {app.selected_user_id}"

        # Используем прямое логирование
        self.log_admin_action_direct("view_records", f"Просмотр {filter_type}")

    def log_admin_action_direct(self, action_type, details, affected_user_id=None):
        """
        Прямая запись действия администратора в базу данных

        Args:
            action_type: Тип действия
            details: Детали действия
            affected_user_id: ID затронутого пользователя
        """
        try:
            app = MDApp.get_running_app()
            user_id = app.get_user_id()

            # Получаем IP адрес
            ip_address = None
            try:
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
            except:
                ip_address = "unknown"

            conn = get_connection()
            insert_admin_action(
                conn,
                user_id,
                action_type,
                details,
                affected_user_id,
                ip_address
            )
            conn.close()
        except Exception as e:
            print(f"Ошибка записи действия администратора: {e}")

    def load_records(self, search_query=None):
        """
        Загружает записи для администратора

        Args:
            search_query: Текст для поиска записей
        """
        try:
            conn = get_connection()

            # Определяем, загружать ли записи конкретного пользователя
            app = MDApp.get_running_app()
            user_id = getattr(app, 'selected_user_id', None)

            if user_id:
                records = select_user_records_by_admin(conn, user_id, limit=500)
                filter_text = f"записи пользователя ID: {user_id}"
            else:
                records = select_user_records_by_admin(conn, None, limit=500)
                filter_text = "записи всех пользователей"

            # Обновляем заголовок
            if hasattr(self.ids, 'title_label'):
                self.ids.title_label.text = f"Записи ({filter_text})"

            # Сохраняем все записи для поиска
            self.all_records = list(records) if records else []

            # Фильтруем записи, если есть поисковый запрос
            filtered_records = []
            if search_query and search_query.strip():
                query_lower = search_query.lower()
                for record in self.all_records:
                    # ИСПРАВЛЕНА ИНДЕКСАЦИЯ ПОЛЕЙ:
                    # record structure: (id, user_id, user_name, user_email, weight, pressure_systolic,
                    # pressure_diastolic, pulse, temperature, notes, record_date, created_at)
                    record_id = str(record[0]) if record[0] else ""
                    user_id_str = str(record[1]) if record[1] else ""
                    user_name = str(record[2]) if record[2] else ""
                    user_email = str(record[3]) if record[3] else ""
                    weight_str = str(record[4]) if record[4] else ""
                    pressure_sys_str = str(record[5]) if record[5] else ""
                    pressure_dia_str = str(record[6]) if record[6] else ""
                    pulse_str = str(record[7]) if record[7] else ""
                    temp_str = str(record[8]) if record[8] else ""
                    notes = str(record[9]) if record[9] else ""
                    record_date_str = str(record[10]) if record[10] else ""

                    # Ищем во всех полях
                    if (query_lower in user_name.lower() or
                            query_lower in user_email.lower() or
                            query_lower in notes.lower() or
                            query_lower in record_id.lower() or
                            query_lower in user_id_str.lower() or
                            query_lower in weight_str.lower() or
                            query_lower in pressure_sys_str.lower() or
                            query_lower in pressure_dia_str.lower() or
                            query_lower in pulse_str.lower() or
                            query_lower in temp_str.lower() or
                            query_lower in record_date_str.lower()):
                        filtered_records.append(record)
            else:
                filtered_records = self.all_records

            # Отображаем записи
            if hasattr(self.ids, 'records_list'):
                self.ids.records_list.clear_widgets()

                if filtered_records:
                    for record in filtered_records:
                        # ИСПРАВЛЕНА РАСПАКОВКА
                        try:
                            (record_id, user_id, user_name, user_email, weight,
                             pressure_sys, pressure_dia, pulse, temp, notes,
                             record_date, created_at) = record
                        except Exception as e:
                            print(f"Ошибка распаковки записи: {e}")
                            continue

                        # Форматируем дату
                        try:
                            if isinstance(record_date, str):
                                # Пробуем разные форматы
                                try:
                                    date_obj = datetime.strptime(record_date.split()[0], "%Y-%m-%d")
                                except:
                                    # Может быть уже в другом формате
                                    date_obj = datetime.now()
                            else:
                                date_obj = record_date
                            formatted_date = date_obj.strftime("%d.%m.%Y")
                        except:
                            formatted_date = str(record_date)

                        # Формируем текст
                        primary_text = f"{user_name} ({user_email}) - {formatted_date}"

                        # Формируем показатели
                        indicators = []
                        if weight:
                            indicators.append(f"Вес: {weight} кг")
                        if pressure_sys and pressure_dia:
                            indicators.append(f"Давление: {pressure_sys}/{pressure_dia}")
                        if pulse:
                            indicators.append(f"Пульс: {pulse}")
                        if temp:
                            indicators.append(f"Темп.: {temp}°C")

                        secondary_text = ", ".join(indicators) if indicators else "Нет показателей"

                        # Третичный текст для заметок
                        tertiary_text = ""
                        if notes:
                            if len(notes) > 100:
                                tertiary_text = notes[:100] + "..."
                            else:
                                tertiary_text = notes

                        # Создаем элемент списка
                        item = ThreeLineListItem(
                            text=primary_text,
                            secondary_text=secondary_text,
                            tertiary_text=tertiary_text if tertiary_text else "",
                            bg_color=(0.95, 0.95, 1, 0.3)
                        )

                        # Привязываем обработчик для просмотра деталей
                        item.bind(on_release=lambda x, rec=record: self.view_record_details(rec))

                        self.ids.records_list.add_widget(item)
                else:
                    # Нет записей
                    no_records_text = "Записи не найдены" if search_query else "Нет записей для отображения"
                    self.ids.records_list.add_widget(MDLabel(
                        text=no_records_text,
                        halign="center",
                        theme_text_color="Secondary",
                        font_style="H6"
                    ))

            conn.close()

        except Exception as e:
            print(f"Ошибка загрузки записей: {e}")
            self.show_message("Ошибка", f"Ошибка загрузки записей: {str(e)}")

    def on_search(self, instance, value):
        """
        Обработчик поиска записей

        Args:
            instance: Поле ввода
            value: Текст поиска
        """
        self.search_query = value
        self.load_records(search_query=value)

    def view_record_details(self, record):
        """
        Показывает детали записи

        Args:
            record: Данные записи
        """
        try:
            # ИСПРАВЛЕНА РАСПАКОВКА
            (record_id, user_id, user_name, user_email, weight,
             pressure_sys, pressure_dia, pulse, temp, notes,
             record_date, created_at) = record
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка обработки записи: {e}")
            return

        # Форматируем дату
        try:
            if isinstance(record_date, str):
                date_obj = datetime.strptime(record_date.split()[0], "%Y-%m-%d")
            else:
                date_obj = record_date
            formatted_date = date_obj.strftime("%d.%m.%Y")
        except:
            formatted_date = str(record_date)

        # Форматируем дату создания
        try:
            if isinstance(created_at, str):
                created_obj = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            else:
                created_obj = created_at
            formatted_created = created_obj.strftime("%d.%m.%Y %H:%M")
        except:
            formatted_created = str(created_at)

        # Создаем содержимое диалога
        details = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(15),
            adaptive_height=True
        )

        # Информация о пользователе
        details.add_widget(MDLabel(
            text=f"Пользователь: {user_name}",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(30)
        ))

        details.add_widget(MDLabel(
            text=f"Email: {user_email}",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(25)
        ))

        details.add_widget(MDLabel(
            text=f"ID пользователя: {user_id}",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(25)
        ))

        details.add_widget(MDLabel(
            text="",
            size_hint_y=None,
            height=dp(10)
        ))

        # Информация о записи
        details.add_widget(MDLabel(
            text=f"Дата записи: {formatted_date}",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(30)
        ))

        details.add_widget(MDLabel(
            text=f"Дата создания: {formatted_created}",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(25)
        ))

        details.add_widget(MDLabel(
            text=f"ID записи: {record_id}",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(25)
        ))

        details.add_widget(MDLabel(
            text="",
            size_hint_y=None,
            height=dp(10)
        ))

        # Показатели
        indicators_text = "Показатели:\n"
        if weight:
            indicators_text += f"• Вес: {weight} кг\n"
        if pressure_sys and pressure_dia:
            indicators_text += f"• Давление: {pressure_sys}/{pressure_dia} мм рт.ст.\n"
        if pulse:
            indicators_text += f"• Пульс: {pulse} уд/мин\n"
        if temp:
            indicators_text += f"• Температура: {temp}°C\n"

        if indicators_text != "Показатели:\n":
            details.add_widget(MDLabel(
                text=indicators_text.strip(),
                theme_text_color="Primary",
                size_hint_y=None,
                height=dp(100)
            ))

        # Заметки
        if notes:
            details.add_widget(MDLabel(
                text="Заметки:",
                theme_text_color="Primary",
                font_style="Subtitle1",
                size_hint_y=None,
                height=dp(30)
            ))

            notes_scroll = ScrollView(size_hint_y=None, height=dp(150))
            notes_label = MDLabel(
                text=notes,
                theme_text_color="Secondary",
                size_hint_y=None,
                valign="top"
            )
            notes_label.bind(texture_size=lambda instance, value: setattr(notes_label, 'height', value[1]))
            notes_scroll.add_widget(notes_label)
            details.add_widget(notes_scroll)

        # Диалог
        dialog = MDDialog(
            title="Детали записи",
            type="custom",
            content_cls=details,
            buttons=[
                MDRaisedButton(
                    text="Закрыть",
                    md_bg_color=(0, 0, 1, 1),
                    on_release=lambda _: dialog.dismiss()
                )
            ],
            size_hint=(0.9, 0.9)
        )
        dialog.open()

    def clear_user_filter(self):
        """
        Очищает фильтр по пользователю и показывает все записи
        """
        app = MDApp.get_running_app()
        if hasattr(app, 'selected_user_id'):
            app.selected_user_id = None

        # Загружаем все записи
        self.load_records()

        # Записываем действие
        self.log_admin_action_direct("view_records", "Просмотр записей всех пользователей")

    def show_message(self, title, text):
        """Показывает диалоговое окно с сообщением"""
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    md_bg_color=(0, 0, 1, 1),
                    on_release=lambda _: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def go_back(self):
        """Возврат к административной панели"""
        # Очищаем фильтр по пользователю
        app = MDApp.get_running_app()
        if hasattr(app, 'selected_user_id'):
            app.selected_user_id = None

        self.manager.current = "admin_dashboard"

class AdminAuditScreen(Screen):
    """
    Экран просмотра журнала действий администраторов
    """

    def on_pre_enter(self):
        """
        Метод, вызываемый перед переходом на экран
        """
        # Проверяем права администратора
        app = MDApp.get_running_app()
        if not getattr(app, 'is_admin', False):
            self.show_message("Доступ запрещен", "Только администраторы могут просматривать эту страницу")
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'profile'), 0.5)
            return

        # Загружаем журнал действий
        self.load_audit_log()

        # Записываем действие администратора
        # Используем прямое логирование
        self.log_admin_action_direct("view_audit_log", "Просмотр журнала действий администраторов")

    def log_admin_action_direct(self, action_type, details, affected_user_id=None):
        """
        Прямая запись действия администратора в базу данных

        Args:
            action_type: Тип действия
            details: Детали действия
            affected_user_id: ID затронутого пользователя
        """
        try:
            app = MDApp.get_running_app()
            user_id = app.get_user_id()

            # Получаем IP адрес
            ip_address = None
            try:
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
            except:
                ip_address = "unknown"

            conn = get_connection()
            insert_admin_action(
                conn,
                user_id,
                action_type,
                details,
                affected_user_id,
                ip_address
            )
            conn.close()
        except Exception as e:
            print(f"Ошибка записи действия администратора: {e}")

    def load_audit_log(self, limit=100):
        """
        Загружает журнал действий администраторов

        Args:
            limit: Ограничение количества записей
        """
        try:
            conn = get_connection()
            actions = select_admin_actions(conn, None, limit)

            if hasattr(self.ids, 'audit_list'):
                self.ids.audit_list.clear_widgets()

                if actions:
                    for action in actions:
                        action_id, admin_id, admin_name, action_type, action_details, affected_user_id, affected_user_name, ip_address, created_at = action

                        # Форматируем дату
                        try:
                            if isinstance(created_at, str):
                                date_obj = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                            else:
                                date_obj = created_at
                            formatted_date = date_obj.strftime("%d.%m.%Y %H:%M:%S")
                        except:
                            formatted_date = str(created_at)

                        # Формируем текст
                        primary_text = f"{admin_name} ({action_type})"
                        secondary_text = f"Дата: {formatted_date}"

                        if affected_user_name:
                            tertiary_text = f"Пользователь: {affected_user_name} | Детали: {action_details}"
                        else:
                            tertiary_text = f"Детали: {action_details}"

                        # Создаем элемент списка
                        item = ThreeLineListItem(
                            text=primary_text,
                            secondary_text=secondary_text,
                            tertiary_text=tertiary_text
                        )

                        self.ids.audit_list.add_widget(item)
                else:
                    # Нет действий
                    self.ids.audit_list.add_widget(MDLabel(
                        text="Журнал действий пуст",
                        halign="center",
                        theme_text_color="Secondary",
                        font_style="H6"
                    ))

            conn.close()
        except Exception as e:
            self.show_message("Ошибка", f"Ошибка загрузки журнала действий: {str(e)}")

    def show_message(self, title, text):
        """Показывает диалоговое окно с сообщением"""
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    md_bg_color=(0, 0, 1, 1),
                    on_release=lambda _: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def go_back(self):
        """Возврат к административной панели"""
        self.manager.current = "admin_dashboard"
