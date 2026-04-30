import sqlite3
import json

class Database:
    def __init__(self, db_name="quiz_system.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    # FIXED: query method now correctly defines its own cursor
    def query(self, sql, params=()):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            result = cursor.fetchall()
            return result
        finally:
            conn.close()

    # FIXED: execute method now correctly defines its own cursor
    def execute(self, sql, params=()):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def init_db(self):
        # 1. Students Table (UPDATED with missing columns)
        self.execute("""CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        firstname TEXT,
                        lastname TEXT,
                        section TEXT,
                        username TEXT UNIQUE,
                        password TEXT)""")

        # 2. Schedules Table
        self.execute("""CREATE TABLE IF NOT EXISTS schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        quiz_title TEXT,
                        quiz_name TEXT,
                        quiz_data TEXT,
                        quiz_code TEXT UNIQUE,
                        start_time TEXT,
                        end_time TEXT)""")

        # 3. Results Table
        # In database.py -> init_db
        self.execute("""CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                quiz_title TEXT,
                score INTEGER,
                total INTEGER,
                defeated_boss TEXT, 
                quiz_details TEXT, 
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")

        # Ensure at least one user exists
        users = self.query("SELECT * FROM students LIMIT 1")
        if not users:
            self.execute("INSERT INTO students (username, password) VALUES (?, ?)", ("admin", "admin123"))

    def repair_schema(self):
        """Run this once if you get 'no such column: quiz_details' errors."""
        try:
            self.execute("ALTER TABLE results ADD COLUMN quiz_details TEXT")
            print("Successfully added quiz_details column.")
        except Exception:
            # Column likely already exists
            pass