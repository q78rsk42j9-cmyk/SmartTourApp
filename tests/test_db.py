import unittest
import os
from database.db_manager import DBManager

class TestTravelAgencyDB(unittest.TestCase):
    def setUp(self):
        """Создает чистую изолированную базу данных перед каждым тестом"""
        self.test_db_path = 'test_travel_agency.db'
        self.db = DBManager(self.test_db_path)

    def tearDown(self):
        """Удаляет тестовую базу данных после прохождения теста"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_calculate_cost(self):
        """Unit-тест: Проверка правильности расчета стоимости калькулятором"""
        cost = self.db.calculate_cost(price_per_night=2000.0, start_date='2026-06-01', end_date='2026-06-06')
        self.assertEqual(cost, 10000.0)

        invalid_cost = self.db.calculate_cost(price_per_night=2000.0, start_date='2026-06-10', end_date='2026-06-05')
        self.assertEqual(invalid_cost, 0.0)

    def test_room_filtering(self):
        """Интеграционный тест: Проверка работы SQL-фильтра свободных комнат"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Rooms (title, resort, rooms_count, price_per_night, image_url)
                VALUES ('Test Villa', 'Сочи', 3, 5000.0, 'images/1.jpg');
            ''')
            room_id = cursor.lastrowid
            conn.commit()

        # 1. Проверяем, что фильтр находит комнату
        found_rooms = self.db.find_available_rooms(resort='Сочи', rooms_count=3, start_date='2026-07-01', end_date='2026-07-05')
        self.assertEqual(len(found_rooms), 1)
        self.assertEqual(found_rooms[0][1], 'Test Villa')

        # 2. Имитируем бронирование этой комнаты
        user_id = self.db.add_user(login='test_user', password_hash='Pass!123', role='client')
        self.db.add_booking(user_id=user_id, room_id=room_id, start_date='2026-07-01', end_date='2026-07-05', total_cost=20000.0)

        # 3. Проверяем, что на эти даты комната больше НЕ выводится (занята)
        busy_rooms = self.db.find_available_rooms(resort='Сочи', rooms_count=3, start_date='2026-07-01', end_date='2026-07-05')
        self.assertEqual(len(busy_rooms), 0)

        # 4. Проверяем, что на другие даты она остается свободной
        free_rooms = self.db.find_available_rooms(resort='Сочи', rooms_count=3, start_date='2026-07-10', end_date='2026-07-15')
        self.assertEqual(len(free_rooms), 1)

if __name__ == '__main__':
    unittest.main()
