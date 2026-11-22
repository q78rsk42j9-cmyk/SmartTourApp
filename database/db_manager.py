import sqlite3
from datetime import datetime

class DBManager:
    def __init__(self, db_path='travel_agency.db'):
        self.db_path = db_path
        self.create_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def create_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Таблица Пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'client'
                );
            ''')
            
            # 2. Таблица Номеров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    resort TEXT NOT NULL,
                    rooms_count INTEGER NOT NULL,
                    price_per_night REAL NOT NULL,
                    image_url TEXT
                );
            ''')
            
            # 3. Таблица Бронирований
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    room_id INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    total_cost REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
                    FOREIGN KEY (room_id) REFERENCES Rooms(id) ON DELETE CASCADE
                );
            ''')

            # 4. НОВАЯ ТАБЛИЦА: Лайки / Избранное (Фича "на 10 баллов")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Favorites (
                    user_id INTEGER NOT NULL,
                    room_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, room_id),
                    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
                    FOREIGN KEY (room_id) REFERENCES Rooms(id) ON DELETE CASCADE
                );
            ''')
            conn.commit()

    # --- УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (РЕГИСТРАЦИЯ И ВХОД) ---
    def add_user(self, login, password_hash, role='client'):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO Users (login, password_hash, role) VALUES (?, ?, ?)', 
                               (login, password_hash, role))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def check_user_credentials(self, login, password_hash):
        """Проверяет логин и пароль. Возвращает (user_id, role) или None"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, role FROM Users WHERE login = ? AND password_hash = ?', (login, password_hash))
            return cursor.fetchone()

    # --- ФИЧА №1: Поиск свободных отелей ---
    def find_available_rooms(self, resort, rooms_count, start_date, end_date, user_id=None):
        """Возвращает отели и флаг, лайкнул ли их текущий пользователь"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Сложный SQL, который сразу подтягивает информацию о лайках через LEFT JOIN
            query = '''
                SELECT r.id, r.title, r.resort, r.rooms_count, r.price_per_night, r.image_url,
                       CASE WHEN f.user_id IS NOT NULL THEN 1 ELSE 0 END as is_favorite
                FROM Rooms r
                LEFT JOIN Favorites f ON r.id = f.room_id AND f.user_id = ?
                WHERE r.resort LIKE ? 
                  AND r.rooms_count >= ?
                  AND r.id NOT IN (
                      SELECT room_id FROM Bookings
                      WHERE NOT (end_date <= ? OR start_date >= ?)
                  );
            '''
            cursor.execute(query, (user_id, f"%{resort}%", rooms_count, start_date, end_date))
            return cursor.fetchall()

    # --- ФИЧА №2: Бронирование ---
    def calculate_cost(self, price_per_night, start_date, end_date):
        try:
            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")
            nights = (d2 - d1).days
            return float(nights * price_per_night) if nights > 0 else 0.0
        except:
            return 0.0

    def add_booking(self, user_id, room_id, start_date, end_date, total_cost):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Bookings (user_id, room_id, start_date, end_date, total_cost)
                VALUES (?, ?, ?, ?, ?);
            ''', (user_id, room_id, start_date, end_date, total_cost))
            conn.commit()

    def get_user_bookings(self, user_id):
        """Получить список всех бронирований пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.id, r.title, r.resort, b.start_date, b.end_date, b.total_cost
                FROM Bookings b
                JOIN Rooms r ON b.room_id = r.id
                WHERE b.user_id = ?;
            ''', (user_id,))
            return cursor.fetchall()

    # --- СИСТЕМА ЛАЙКОВ ---
    def toggle_favorite(self, user_id, room_id):
        """Если лайк есть — удаляет, если нет — ставит"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM Favorites WHERE user_id = ? AND room_id = ?', (user_id, room_id))
            if cursor.fetchone():
                cursor.execute('DELETE FROM Favorites WHERE user_id = ? AND room_id = ?', (user_id, room_id))
                status = False
            else:
                cursor.execute('INSERT INTO Favorites (user_id, room_id) VALUES (?, ?)', (user_id, room_id))
                status = True
            conn.commit()
            return status
