import sys
from PyQt6.QtWidgets import QApplication
from database.db_manager import DBManager
from utils.importer import CSVImporter
from gui.main_window import MainWindow

def main():
    # 1. Инициализируем БД
    db_manager = DBManager('travel_agency.db')
    
    # 2. Инициализируем импортер
    csv_importer = CSVImporter(db_manager)
    
    # 3. Запуск GUI окружения
    app = QApplication(sys.argv)
    
    # 4. Показ главного премиального окна
    window = MainWindow(db_manager, csv_importer)
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()