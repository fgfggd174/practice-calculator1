import sqlite3
import json
import logging

DB_FILE = "calc_history.db"

class DatabaseManager:
    """Управление базой данных SQLite для истории вычислений."""

    def __init__(self):
        self.conn = None
        self.init_db()

    def init_db(self):
        """Создание таблицы, если она отсутствует."""
        try:
            self.conn = sqlite3.connect(DB_FILE)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    figure_type TEXT NOT NULL,
                    params TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    area REAL,
                    perimeter REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
            logging.info("База данных инициализирована.")
        except sqlite3.Error as e:
            logging.error(f"Ошибка инициализации БД: {e}")

    def insert_record(self, figure_type, params, unit, area, perimeter):
        """Вставка новой записи с единицами измерения."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO history (figure_type, params, unit, area, perimeter) VALUES (?, ?, ?, ?, ?)",
                (figure_type, json.dumps(params), unit, area, perimeter)
            )
            self.conn.commit()
            logging.info(f"Добавлена запись: {figure_type}, площадь={area}, периметр={perimeter}, единицы={unit}")
            return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Ошибка вставки записи: {e}")
            return None

    def get_all_records(self):
        """Получение всех записей, отсортированных по времени."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, figure_type, params, unit, area, perimeter, timestamp FROM history ORDER BY timestamp DESC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения записей: {e}")
            return []

    def delete_record(self, record_id):
        """Удаление записи по id."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM history WHERE id = ?", (record_id,))
            self.conn.commit()
            logging.info(f"Удалена запись id={record_id}")
            return True
        except sqlite3.Error as e:
            logging.error(f"Ошибка удаления записи: {e}")
            return False

    def clear_history(self):
        """Очистка всей таблицы."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM history")
            self.conn.commit()
            logging.info("История очищена.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Ошибка очистки истории: {e}")
            return False

    def close(self):
        """Закрытие соединения с БД."""
        if self.conn:
            self.conn.close()
            logging.info("Соединение с БД закрыто.")
