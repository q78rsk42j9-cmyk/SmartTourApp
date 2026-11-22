import csv
import sqlite3

class CSVImporter:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def import_rooms_from_csv(self, file_path):
        imported_count = 0
        
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                
                with self.db_manager._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    for row in reader:
                        try:
                            # Очищаем данные от случайных пробелов
                            title = row['title'].strip()
                            resort = row['resort'].strip()
                            rooms_count = int(row['rooms_count'])
                            price_per_night = float(row['price_per_night'])
                            image_url = row['image_url'].strip()
                            
                            # Фикс SQL: Явно указываем имена колонок!
                            cursor.execute('''
                                INSERT INTO Rooms (title, resort, rooms_count, price_per_night, image_url)
                                VALUES (?, ?, ?, ?, ?);
                            ''', (title, resort, rooms_count, price_per_night, image_url))
                            
                            imported_count += 1
                        except (KeyError, ValueError) as e:
                            print(f"Ошибка в строке: {e}")
                            continue
                            
                    conn.commit()
                    
        except Exception as e:
            print(f"Критическая ошибка импорта: {e}")
            return -1
            
        return imported_count
