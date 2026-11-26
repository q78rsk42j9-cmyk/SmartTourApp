import requests
import re
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QDateEdit, 
                             QScrollArea, QFileDialog, QMessageBox, QFrame, 
                             QTabWidget, QStackedWidget)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QPixmap, QFont

MODERN_STYLE = """
    QMainWindow {
        background-color: #F5F5F7;
    }
    QWidget {
        font-family: Arial;
        color: #1D1D1F;
    }
    QFrame#card {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E5E5EA;
    }
    QFrame#auth_box {
        background-color: #FFFFFF;
        border-radius: 16px;
        border: 1px solid #E5E5EA;
    }
    QLineEdit {
        background-color: #FFFFFF;
        border: 1px solid #D1D1D6;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
    }
    QLineEdit:focus {
        border: 2px solid #007AFF;
    }
    QPushButton {
        background-color: #007AFF;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #0063CC;
    }
    QPushButton#btn_secondary {
        background-color: #E5E5EA;
        color: #007AFF;
    }
    QPushButton#btn_secondary:hover {
        background-color: #D1D1D6;
    }
    QPushButton#btn_like {
        background-color: transparent;
        font-size: 18px;
        border: none;
        padding: 0px;
    }
    QTabWidget::pane {
        border: none;
        background-color: #F5F5F7;
    }
    QTabBar::tab {
        background: #E5E5EA;
        padding: 10px 20px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: bold;
    }
    QTabBar::tab:selected {
        background: #FFFFFF;
        color: #007AFF;
    }
"""

class MainWindow(QMainWindow):
    def __init__(self, db_manager, csv_importer):
        super().__init__()
        self.db_manager = db_manager
        self.csv_importer = csv_importer
        self.current_user_id = None
        self.current_user_role = "client"

        self.setWindowTitle("SmartTour Premium")
        self.resize(950, 650)
        self.setStyleSheet(MODERN_STYLE)

        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        self.init_auth_screen()
        self.init_main_screen()

        self.central_stack.setCurrentIndex(0)

    def init_auth_screen(self):
        auth_widget = QWidget()
        auth_layout = QVBoxLayout(auth_widget)
        auth_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        box = QFrame()
        box.setObjectName("auth_box")
        box.setFixedSize(360, 430)
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(30, 30, 30, 30)
        box_layout.setSpacing(12)

        title = QLabel("SmartTour")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #007AFF; margin-bottom: 10px;")

        self.auth_login = QLineEdit()
        self.auth_login.setPlaceholderText("Логин")
        
        self.auth_password = QLineEdit()
        self.auth_password.setPlaceholderText("Пароль")
        self.auth_password.setEchoMode(QLineEdit.EchoMode.Password)

        btn_login = QPushButton("Войти")
        btn_login.clicked.connect(self.handle_login)

        btn_register = QPushButton("Зарегистрироваться")
        btn_register.setObjectName("btn_secondary")
        btn_register.clicked.connect(self.handle_register)

        box_layout.addWidget(title)
        box_layout.addWidget(QLabel("<b>Вход в систему</b>"))
        box_layout.addWidget(self.auth_login)
        box_layout.addWidget(self.auth_password)
        box_layout.addWidget(btn_login)
        box_layout.addWidget(btn_register)

        lbl_hint = QLabel("Пароль: от 6 симв., 1 цифра, 1 спецсимвол (!@#$%*)")
        lbl_hint.setStyleSheet("color: #8E8E93; font-size: 11px;")
        lbl_hint.setWordWrap(True)
        box_layout.addWidget(lbl_hint)

        auth_layout.addWidget(box)
        self.central_stack.addWidget(auth_widget)

    def handle_login(self):
        login = self.auth_login.text().strip()
        password = self.auth_password.text().strip()
        if not login or not password:
            QMessageBox.warning(self, "Внимание", "Заполните все поля!")
            return

        user_data = self.db_manager.check_user_credentials(login, password)
        if user_data:
            self.current_user_id = int(user_data[0])
            self.current_user_role = str(user_data[1])
            self.central_stack.setCurrentIndex(1)
            self.search_rooms()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль")

    def handle_register(self):
        login = self.auth_login.text().strip()
        password = self.auth_password.text().strip()
        
        if not login or not password:
            QMessageBox.warning(self, "Внимание", "Заполните все поля!")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Слабый пароль", "Пароль должен быть длиннее 6 символов!")
            return
            
        if not re.search(r"\d", password):
            QMessageBox.warning(self, "Слабый пароль", "Пароль должен содержать хотя бы одну цифру!")
            return

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            QMessageBox.warning(self, "Слабый пароль", "Пароль должен содержать хотя бы один специальный символ (!@#$%^&*...)!")
            return

        user_id = self.db_manager.add_user(login, password, role="client")
        if user_id:
            QMessageBox.information(self, "Успех", "Регистрация успешна! Теперь вы можете войти.")
        else:
            QMessageBox.critical(self, "Ошибка", "Этот логин уже занят другим пользователем!")

    def init_main_screen(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.handle_tab_change)

        self.tab_search = QWidget()
        self.init_search_tab()
        self.tabs.addTab(self.tab_search, "🔍 Поиск туров")

        self.tab_favorites = QWidget()
        self.init_favorites_tab()
        self.tabs.addTab(self.tab_favorites, "❤️ Избранное")

        self.tab_bookings = QWidget()
        self.init_bookings_tab()
        self.tabs.addTab(self.tab_bookings, "🧳 Мои бронирования")

        main_layout.addWidget(self.tabs)
        self.central_stack.addWidget(main_widget)

    def init_search_tab(self):
        layout = QVBoxLayout(self.tab_search)

        filter_box = QFrame()
        filter_box.setObjectName("card")
        filter_layout = QHBoxLayout(filter_box)

        self.input_resort = QLineEdit()
        self.input_resort.setPlaceholderText("Курорт (напр. Сочи)")
        
        self.input_rooms = QLineEdit()
        self.input_rooms.setPlaceholderText("Комнат")
        self.input_rooms.setFixedWidth(80)
        self.input_rooms.setText("1")

        self.date_start = QDateEdit(QDate.currentDate())
        self.date_start.setCalendarPopup(True)
        self.date_end = QDateEdit(QDate.currentDate().addDays(7))
        self.date_end.setCalendarPopup(True)

        btn_search = QPushButton("Найти")
        btn_search.clicked.connect(self.search_rooms)

        btn_import = QPushButton("Импорт CSV")
        btn_import.setObjectName("btn_secondary")
        btn_import.clicked.connect(self.import_csv)

        filter_layout.addWidget(self.input_resort)
        filter_layout.addWidget(self.input_rooms)
        filter_layout.addWidget(self.date_start)
        filter_layout.addWidget(self.date_end)
        filter_layout.addWidget(btn_search)
        filter_layout.addWidget(btn_import)

        layout.addWidget(filter_box)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

    def init_favorites_tab(self):
        layout = QVBoxLayout(self.tab_favorites)
        self.fav_scroll = QScrollArea()
        self.fav_scroll.setWidgetResizable(True)
        self.fav_scroll_widget = QWidget()
        self.fav_scroll_layout = QVBoxLayout(self.fav_scroll_widget)
        self.fav_scroll.setWidget(self.fav_scroll_widget)
        layout.addWidget(self.fav_scroll)

    def init_bookings_tab(self):
        self.bookings_layout = QVBoxLayout(self.tab_bookings)
        self.bookings_scroll = QScrollArea()
        self.bookings_scroll.setWidgetResizable(True)
        self.bookings_scroll_widget = QWidget()
        self.bookings_scroll_layout = QVBoxLayout(self.bookings_scroll_widget)
        self.bookings_scroll.setWidget(self.bookings_scroll_widget)
        self.bookings_layout.addWidget(self.bookings_scroll)

    def handle_tab_change(self, index):
        if index == 1:
            self.load_favorite_rooms()
        elif index == 2:
            self.load_user_bookings()

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть таблицу", "", "CSV Files (*.csv)")
        if file_path:
            count = self.csv_importer.import_rooms_from_csv(file_path)
            if count >= 0:
                QMessageBox.information(self, "Успех", f"Успешно импортировано объектов: {count}")
                self.search_rooms()
            else:
                QMessageBox.critical(self, "Ошибка", "Сбой импорта.")

    def search_rooms(self):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        resort = self.input_resort.text().strip()
        start_dt = self.date_start.date().toString(Qt.DateFormat.ISODate)
        end_dt = self.date_end.date().toString(Qt.DateFormat.ISODate)
        
        try:
            rooms_cnt = int(self.input_rooms.text().strip())
        except ValueError:
            rooms_cnt = 1

        rooms = self.db_manager.find_available_rooms(resort, rooms_cnt, start_dt, end_dt, self.current_user_id)

        if not rooms:
            lbl_empty = QLabel("Ничего не найдено. Попробуйте изменить фильтры.")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(lbl_empty)
            return

        for r_id, title, res, r_count, price, img_path, is_fav in rooms:
            card = QFrame()
            card.setObjectName("card")
            card_layout = QHBoxLayout(card)

            lbl_img = QLabel()
            lbl_img.setFixedSize(140, 105)
            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # --- ЧТЕНИЕ ИЗ СИСТЕМНОЙ ПАПКИ PICTURES/SMARTTOUR ---
            file_name = os.path.basename(img_path) if img_path else ""
            home_path = os.path.expanduser("~")
            full_img_path = os.path.join(home_path, "Pictures", "smarttour", file_name)
            
            if file_name and os.path.exists(full_img_path):
                pixmap = QPixmap(full_img_path)
                lbl_img.setPixmap(pixmap.scaled(lbl_img.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            else:
                lbl_img.setText("🏨")
                lbl_img.setStyleSheet("background-color: #E5E5EA; border-radius: 8px; font-size: 32px;")
            
            card_layout.addWidget(lbl_img)

            info_layout = QVBoxLayout()
            lbl_title = QLabel(f"{title}")
            lbl_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            info_layout.addWidget(lbl_title)
            info_layout.addWidget(QLabel(f"📍 {res}  •  🛏 Комнат: {r_count}"))
            info_layout.addWidget(QLabel(f"<b>{price} руб.</b> / ночь"))
            card_layout.addLayout(info_layout)

            btn_like = QPushButton("❤️" if is_fav else "🤍")
            btn_like.setObjectName("btn_like")
            btn_like.clicked.connect(lambda _, rid=r_id, btn=btn_like: self.toggle_like(rid, btn))
            card_layout.addWidget(btn_like)

            btn_book = QPushButton("Рассчитать стоимость")
            btn_book.clicked.connect(lambda _, rid=r_id, pr=price: self.book_room(rid, pr))
            card_layout.addWidget(btn_book)

            self.scroll_layout.addWidget(card)

    def toggle_like(self, room_id, button):
        is_liked = self.db_manager.toggle_favorite(self.current_user_id, room_id)
        button.setText("❤️" if is_liked else "🤍")

    def book_room(self, room_id, price_per_night):
        start_dt = self.date_start.date().toString(Qt.DateFormat.ISODate)
        end_dt = self.date_end.date().toString(Qt.DateFormat.ISODate)

        total_cost = self.db_manager.calculate_cost(price_per_night, start_dt, end_dt)

        if total_cost <= 0:
            QMessageBox.warning(self, "Внимание", "Неверный диапазон дат!")
            return

        reply = QMessageBox.question(
            self, "Калькулятор SmartTour", 
            f"Итоговая цена за тур:\n\n💳 {total_cost} руб.\n\nОформить бронирование?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db_manager.add_booking(self.current_user_id, room_id, start_dt, end_dt, total_cost)
            QMessageBox.information(self, "Успех", "Тур успешно добавлен в ваши бронирования!")
            self.search_rooms()

        for i in reversed(range(self.fav_scroll_layout.count())): 
            if self.fav_scroll_layout.itemAt(i).widget():
                self.fav_scroll_layout.itemAt(i).widget().setParent(None)

        all_rooms = self.db_manager.find_available_rooms("", 1, "2000-01-01", "3000-01-01", self.current_user_id)
        fav_rooms = [r for r in all_rooms if r[6] == 1] 

        if not fav_rooms:
            lbl_empty = QLabel("У вас пока нет избранных отелей. Нажмите ❤️ на карточке отеля!")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.fav_scroll_layout.addWidget(lbl_empty)
            return

        for r_id, title, res, r_count, price, img_path, _ in fav_rooms:
            card = QFrame()
            card.setObjectName("card")
            card_layout = QHBoxLayout(card)

            lbl_img = QLabel()
            lbl_img.setFixedSize(140, 105)
            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            file_name = os.path.basename(img_path) if img_path else ""
            home_path = os.path.expanduser("~")
            full_img_path = os.path.join(home_path, "Pictures", "smarttour", file_name)
            
            if file_name and os.path.exists(full_img_path):
                pixmap = QPixmap(full_img_path)
                lbl_img.setPixmap(pixmap.scaled(lbl_img.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            else:
                lbl_img.setText("🏨")
                lbl_img.setStyleSheet("background-color: #E5E5EA; border-radius: 8px; font-size: 32px;")
            card_layout.addWidget(lbl_img)

            info = QVBoxLayout()
            lbl_title = QLabel(f"{title}")
            lbl_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            info.addWidget(lbl_title)
            info.addWidget(QLabel(f"📍 {res}  •  🛏 Номер: {r_count}-комн."))
            info.addWidget(QLabel(f"<b>{price} руб.</b> / ночь"))
            card_layout.addLayout(info)

            btn_unlike = QPushButton("Убрать")
            btn_unlike.setObjectName("btn_secondary")
            btn_unlike.clicked.connect(lambda _, rid=r_id: self.remove_from_fav(rid))
            card_layout.addWidget(btn_unlike)

            self.fav_scroll_layout.addWidget(card)
    def load_favorite_rooms(self):
        for i in reversed(range(self.fav_scroll_layout.count())): 
            item = self.fav_scroll_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.spacerItem():
                self.fav_scroll_layout.removeItem(item)

        all_rooms = self.db_manager.find_available_rooms("", 1, "2000-01-01", "3000-01-01", self.current_user_id)
        fav_rooms = [r for r in all_rooms if r[6] == 1] 

        if not fav_rooms:
            lbl_empty = QLabel("У вас пока нет избранных отелей. Нажмите ❤️ на карточке отеля!")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.fav_scroll_layout.addWidget(lbl_empty)
            self.fav_scroll_layout.addStretch()
            return

        for r_id, title, res, r_count, price, img_path, _ in fav_rooms:
            card = QFrame()
            card.setObjectName("card")
            card.setFixedHeight(130)  # Фиксируем аккуратную высоту карточки
            card_layout = QHBoxLayout(card)

            lbl_img = QLabel()
            lbl_img.setFixedSize(140, 105)
            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            file_name = os.path.basename(img_path) if img_path else ""
            home_path = os.path.expanduser("~")
            full_img_path = os.path.join(home_path, "Pictures", "smarttour", file_name)
            
            if file_name and os.path.exists(full_img_path):
                pixmap = QPixmap(full_img_path)
                lbl_img.setPixmap(pixmap.scaled(lbl_img.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            else:
                lbl_img.setText("🏨")
                lbl_img.setStyleSheet("background-color: #E5E5EA; border-radius: 8px; font-size: 32px;")
            card_layout.addWidget(lbl_img)

            info = QVBoxLayout()
            lbl_title = QLabel(f"{title}")
            lbl_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            info.addWidget(lbl_title)
            info.addWidget(QLabel(f"📍 {res}  •  🛏 Номер: {r_count}-комн."))
            info.addWidget(QLabel(f"<b>{price} руб.</b> / ночь"))
            card_layout.addLayout(info)

            btn_unlike = QPushButton("Убрать")
            btn_unlike.setObjectName("btn_secondary")
            btn_unlike.clicked.connect(lambda _, rid=r_id: self.remove_from_fav(rid))
            card_layout.addWidget(btn_unlike)

            self.fav_scroll_layout.addWidget(card)

        self.fav_scroll_layout.addStretch()  # Прижимает карточки к верху экрана

    def remove_from_fav(self, room_id):
        self.db_manager.toggle_favorite(self.current_user_id, room_id)
        self.load_favorite_rooms()

    def load_user_bookings(self):
        for i in reversed(range(self.bookings_scroll_layout.count())): 
            item = self.bookings_scroll_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            elif item.spacerItem():
                self.bookings_scroll_layout.removeItem(item)

        if self.auth_login.text().strip().lower() == "admin" or self.current_user_role == "manager":
            with self.db_manager._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT b.id, u.login, r.title, b.start_date, b.end_date, b.total_cost
                    FROM Bookings b
                    JOIN Rooms r ON b.room_id = r.id
                    JOIN Users u ON b.user_id = u.id;
                ''')
                bookings = cursor.fetchall()

            if not bookings:
                lbl_empty = QLabel("В панели отельера пока нет бронирований от клиентов.")
                lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.bookings_scroll_layout.addWidget(lbl_empty)
                self.bookings_scroll_layout.addStretch()
                return

            for b_id, c_login, title, s_date, e_date, cost in bookings:
                b_card = QFrame()
                b_card.setObjectName("card")
                b_card.setFixedHeight(90)  # Фиксируем высоту карточки отельера
                b_layout = QHBoxLayout(b_card)

                info = QVBoxLayout()
                lbl_t = QLabel(f"👤 Клиент: {c_login}  —  🏨 Объект: {title}")
                lbl_t.setFont(QFont("Arial", 14, QFont.Weight.Bold))
                info.addWidget(lbl_t)
                info.addWidget(QLabel(f"📅 Сроки заезда: {s_date} — {e_date}"))
                
                b_layout.addLayout(info)
                
                lbl_cost = QLabel(f"<b>Получено: {cost} руб.</b>")
                lbl_cost.setStyleSheet("color: #007AFF; font-size: 14px;")
                b_layout.addWidget(lbl_cost)

                self.bookings_scroll_layout.addWidget(b_card)

            self.bookings_scroll_layout.addStretch()

        else:
            bookings = self.db_manager.get_user_bookings(self.current_user_id)

            if not bookings:
                lbl_empty = QLabel("У вас пока нет активных бронирований.")
                lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.bookings_scroll_layout.addWidget(lbl_empty)
                self.bookings_scroll_layout.addStretch()
                return

            for b_id, title, resort, s_date, e_date, cost in bookings:
                b_card = QFrame()
                b_card.setObjectName("card")
                b_card.setFixedHeight(90)  # Фиксируем аккуратную высоту брони
                b_layout = QHBoxLayout(b_card)

                info = QVBoxLayout()
                lbl_t = QLabel(f"✈️ {title} ({resort})")
                lbl_t.setFont(QFont("Arial", 14, QFont.Weight.Bold))
                info.addWidget(lbl_t)
                info.addWidget(QLabel(f"📅 Сроки: {s_date} — {e_date}"))
                
                b_layout.addLayout(info)
                
                lbl_cost = QLabel(f"<b>{cost} руб.</b>")
                lbl_cost.setStyleSheet("color: #34C759; font-size: 16px;")
                b_layout.addWidget(lbl_cost)

                self.bookings_scroll_layout.addWidget(b_card)

            self.bookings_scroll_layout.addStretch()
