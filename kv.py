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
                size_hint_y: None
                height: self.minimum_height
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
            do_scroll_x: False
            do_scroll_y: True
            MDBoxLayout:
                id: inputs_container
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
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
            height: dp(70)
            orientation: "horizontal"
            padding: "10dp"
            spacing: "15dp"
            pos_hint: {"center_x": 0.5}

            MDFloatingActionButton:
                icon: "content-save"
                md_bg_color: 0, 0.7, 0, 1  # Зеленый цвет
                on_release: root.save_data()
                tooltip_text: "Сохранить данные"

            MDFloatingActionButton:
                icon: "history"
                md_bg_color: 0, 0, 1, 1  # Синий цвет
                on_release: root.go_to_history()
                tooltip_text: "История записей"
"""

SETTINGS_KV = '''
<SettingsScreen>:
    name: 'settings'
    theme_display: 'Синий'
    date_format_display: 'ДД-ММ-ГГГГ'
    reminder_time_display: '20:00'

    BoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "15dp"

        MDLabel:
            text: "Настройки приложения"
            halign: "center"
            theme_text_color: "Primary"
            font_style: "H4"
            size_hint_y: None
            height: dp(50)

        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            MDBoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: "30dp"
                spacing: "15dp"

                # Внешний вид
                MDLabel:
                    text: "Внешний вид"
                    theme_text_color: "Primary"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(40)

                TwoLineListItem:
                    text: "Цветовая тема"
                    secondary_text: root.theme_display
                    on_release: root.open_theme_menu(self)

                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: "10dp"
                    size_hint_y: None
                    height: dp(50)

                    MDLabel:
                        text: "Темный режим"
                        size_hint_x: 0.8

                    MDSwitch:
                        id: dark_mode_switch
                        size_hint_x: 0.2
                        active: False
                        on_active: root.on_dark_mode_change


                # Разделитель
                MDSeparator:
                    height: dp(1)
                    color: [0.8, 0.8, 0.8, 1]

                # Экспорт данных
                MDLabel:
                    text: "Экспорт данных"
                    theme_text_color: "Primary"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(40)

                TwoLineListItem:
                    text: "Формат даты"
                    secondary_text: root.date_format_display
                    on_release: root.open_date_format_menu(self)

                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: "10dp"
                    size_hint_y: None
                    height: dp(50)

                    MDLabel:
                        text: "Авто-экспорт в облако"
                        size_hint_x: 0.8

                    MDSwitch:
                        id: auto_export_switch
                        size_hint_x: 0.2
                        active: False
                        on_active: root.on_auto_export_change

                # Разделитель
                MDSeparator:
                    height: dp(1)
                    color: [0.8, 0.8, 0.8, 1]

                # Безопасность и вход
                MDLabel:
                    text: "Безопасность и вход"
                    theme_text_color: "Primary"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(40)

                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: "10dp"
                    size_hint_y: None
                    height: dp(50)

                    MDLabel:
                        text: "Автоматический вход"
                        size_hint_x: 0.8

                    MDSwitch:
                        id: auto_login_switch
                        size_hint_x: 0.2
                        active: True
                        on_active: root.on_auto_login_change

                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: "10dp"
                    size_hint_y: None
                    height: dp(50)

                    MDLabel:
                        text: "Автоматический выход"
                        size_hint_x: 0.8

                    MDSwitch:
                        id: auto_logout_switch
                        size_hint_x: 0.2
                        active: False
                        on_active: root.on_auto_logout_change

                # Кнопки действий
                BoxLayout:
                    orientation: "vertical"
                    spacing: "15dp"
                    size_hint_y: None
                    height: dp(120)
                    padding: [0, "20dp", 0, 0]

                    MDRaisedButton:
                        text: "Сохранить настройки"
                        size_hint_y: None
                        height: dp(48)
                        md_bg_color: app.theme_cls.primary_color
                        text_color: 1, 1, 1, 1
                        on_release: root.save_all_settings()

        BoxLayout:
            size_hint_y: None
            height: dp(70)
            orientation: "horizontal"
            padding: "10dp"
            spacing: "15dp"
            pos_hint: {"center_x": 0.5}

            MDFloatingActionButton:
                icon: "arrow-left"
                md_bg_color: app.theme_cls.primary_color
                on_release: root.go_back()

            MDFloatingActionButton:
                icon: "restore"
                md_bg_color: 0.7, 0.7, 0.2, 1
                on_release: root.reset_to_default()
                tooltip_text: "Сбросить настройки"
'''

PROFILE_KV = '''
<ProfileScreen>:
    name: 'profile'
    avatar_source: ""

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
                source: root.avatar_source
                size_hint: None, None
                size: dp(200), dp(200)
                pos_hint: {"center_x": 0.5}
                allow_stretch: True
                keep_ratio: True
                canvas.before:
                    Color:
                        rgba: 0.9, 0.9, 0.9, 1 if root.avatar_source == "" else 0
                    Ellipse:
                        pos: self.pos
                        size: self.size

        MDLabel:
            id: user_info
            text: ""
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
                icon: "cog"
                md_bg_color: 0.3, 0.5, 0.7, 1
                on_release: root.open_settings()

            MDFloatingActionButton:
                icon: "logout"
                md_bg_color: 1, 0, 0, 1
                on_release: root.logout()
                
            MDFloatingActionButton:
                icon: "shield-account"
                id: admin_btn
                md_bg_color: 0.8, 0.2, 0.2, 1
                on_release: root.open_admin_panel()
                tooltip_text: "Административная панель"
                opacity: 1 if app.is_admin else 0
                disabled: not app.is_admin
'''

PHOTOEDITOR_KV = '''
<SimplePhotoEditor>:
    orientation: 'vertical'
    padding: 20
    spacing: 15
    
    Image:
        id: preview_image
        size_hint: 1, 0.7
        allow_stretch: True
        keep_ratio: True
        source: ''  # Будет установлено в Python коде
    
    BoxLayout:
        size_hint: 1, 0.2
        spacing: 10
        padding: [0, 10, 0, 0]
        
        MDRaisedButton:
            text: 'Повернуть налево'
            size_hint_x: 0.25
            on_press: root.rotate_image(-90)
            md_bg_color: app.theme_cls.primary_color
        
        MDRaisedButton:
            text: 'Повернуть направо'
            size_hint_x: 0.25
            on_press: root.rotate_image(90)
            md_bg_color: app.theme_cls.primary_color
        
        MDRaisedButton:
            text: 'Сохранить'
            size_hint_x: 0.25
            on_press: root.save()
            md_bg_color: app.theme_cls.primary_color
        
        MDRaisedButton:
            text: 'Отмена'
            size_hint_x: 0.25
            on_press: root.cancel()
            md_bg_color: 0.7, 0.7, 0.7, 1
'''

STORY_KV = '''
<StoryWindow>:
    name: 'story'
    
    BoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "10dp"
    
        MDLabel:
            text: "История записей"
            halign: "center"
            theme_text_color: "Primary"
            font_style: "H5"
            size_hint_y: None
            height: dp(40)
    
        # Поле поиска
        MDTextField:
            id: search_field
            hint_text: "Поиск записей..."
            mode: "rectangle"
            size_hint_y: None
            height: dp(45)
            padding: [10, 0, 10, 0]
            on_text: root.on_search(self, self.text)
            icon_right: "magnify"
            icon_right_color: app.theme_cls.primary_color
    
        ScrollView:
            MDList:
                id: container
    
        MDBoxLayout:
            id: button_box
            size_hint_y: None
            height: "50dp" if app.is_android else "60dp"
            orientation: "horizontal"
            padding: "5dp" if app.is_android else "8dp"
            spacing: "8dp" if app.is_android else "12dp"
            pos_hint: {"center_x": 0.5}
            adaptive_width: True
    
            MDFloatingActionButton:
                icon: "plus"
                md_bg_color: 0, 0.7, 0, 1
                on_release: root.add_new_record()
                tooltip_text: "Добавить запись"
                size: (dp(32), dp(32)) if app.is_android else (dp(48), dp(48))
    
            MDFloatingActionButton:
                icon: "account"
                md_bg_color: 0, 0, 1, 1
                on_release: root.on_arrow_pressed()
                tooltip_text: "Профиль"
                size: (dp(32), dp(32)) if app.is_android else (dp(48), dp(48))
    
            MDFloatingActionButton:
                icon: "file-word"
                md_bg_color: 0.2, 0.4, 0.7, 1
                on_release: root.export_to_word()
                tooltip_text: "Экспорт в Word"
                size: (dp(32), dp(32)) if app.is_android else (dp(48), dp(48))
    
            MDFloatingActionButton:
                icon: "chart-line"
                md_bg_color: 0.3, 0.6, 0.3, 1
                on_release: root.show_excel_export_dialog()
                tooltip_text: "Экспорт в Excel с графиками"
                size: (dp(32), dp(32)) if app.is_android else (dp(48), dp(48))
    
            MDFloatingActionButton:
                icon: "delete"
                md_bg_color: 1, 0.2, 0.2, 1
                on_release: root.delete_selected_records()
                tooltip_text: "Удалить выбранные записи"
                size: (dp(32), dp(32)) if app.is_android else (dp(48), dp(48))
    
            MDFloatingActionButton:
                icon: "folder-open"
                md_bg_color: 0.7, 0.5, 0.2, 1
                on_release: root.open_export_folder()
                tooltip_text: "Открыть папку экспорта"
                size: (dp(32), dp(32)) if app.is_android else (dp(48), dp(48))
'''

ADMIN_KV = '''
<AdminDashboard>:
    name: 'admin_dashboard'
    
    BoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "10dp"
    
        MDLabel:
            id: title_label
            text: "Административная панель"
            halign: "center"
            theme_text_color: "Primary"
            font_style: "H5"
            size_hint_y: None
            height: dp(40)
        
        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                spacing: "15dp"
                padding: "10dp"
                adaptive_height: True
                
                MDLabel:
                    text: "Статистика приложения"
                    theme_text_color: "Primary"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(40)
                
                MDGridLayout:
                    id: stats_container
                    cols: 2
                    spacing: "10dp"
                    adaptive_height: True
                    padding: "5dp"
                
                MDLabel:
                    text: "Быстрые действия"
                    theme_text_color: "Primary"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(40)
                
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: "10dp"
                    adaptive_height: True
                    
                    MDRaisedButton:
                        text: "Управление пользователями"
                        icon: "account-group"
                        size_hint_y: None
                        height: dp(48)
                        md_bg_color: 0.2, 0.4, 0.8, 1
                        on_release: root.go_to_users()
                    
                    MDRaisedButton:
                        text: "Просмотр записей"
                        icon: "note-multiple"
                        size_hint_y: None
                        height: dp(48)
                        md_bg_color: 0.2, 0.6, 0.2, 1
                        on_release: root.go_to_records()
                    
                    MDRaisedButton:
                        text: "Журнал действий"
                        icon: "history"
                        size_hint_y: None
                        height: dp(48)
                        md_bg_color: 0.7, 0.5, 0.2, 1
                        on_release: root.go_to_audit_log()
    
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
                tooltip_text: "Назад к профилю"
            
<AdminUsersScreen>:
    name: 'admin_users'
    
    BoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "10dp"
    
        MDLabel:
            text: "Управление пользователями"
            halign: "center"
            theme_text_color: "Primary"
            font_style: "H5"
            size_hint_y: None
            height: dp(40)
        
        MDTextField:
            id: search_field
            hint_text: "Поиск пользователей..."
            mode: "rectangle"
            size_hint_y: None
            height: dp(45)
            padding: [10, 0, 10, 0]
            on_text: root.on_search(self, self.text)
            icon_right: "magnify"
            icon_right_color: app.theme_cls.primary_color
        
        ScrollView:
            MDList:
                id: users_list
        
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
                tooltip_text: "Назад"
            
<AdminRecordsScreen>:
    name: 'admin_records'
    
    BoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "10dp"
    
        MDLabel:
            id: title_label
            text: "Записи пользователей"
            halign: "center"
            theme_text_color: "Primary"
            font_style: "H5"
            size_hint_y: None
            height: dp(40)
        
        MDBoxLayout:
            orientation: "horizontal"
            spacing: "10dp"
            size_hint_y: None
            height: dp(45)
            
            MDTextField:
                id: search_field
                hint_text: "Поиск записей..."
                mode: "rectangle"
                size_hint_x: 0.8
                on_text: root.on_search(self, self.text)
                icon_right: "magnify"
                icon_right_color: app.theme_cls.primary_color
            
            MDFloatingActionButton:
                icon: "filter-remove"
                size_hint_x: None
                width: dp(48)
                md_bg_color: 0.7, 0.3, 0.3, 1
                on_release: root.clear_user_filter()
                tooltip_text: "Очистить фильтр"
        
        ScrollView:
            MDList:
                id: records_list
        
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
                tooltip_text: "Назад"
        
<AdminAuditScreen>:
    name: 'admin_audit'
    
    BoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "10dp"
    
        MDLabel:
            text: "Журнал действий администраторов"
            halign: "center"
            theme_text_color: "Primary"
            font_style: "H5"
            size_hint_y: None
            height: dp(40)
        
        ScrollView:
            MDList:
                id: audit_list
        
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
                tooltip_text: "Назад"
'''