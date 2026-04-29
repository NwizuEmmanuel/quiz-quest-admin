import os
import json
import sqlite3
import threading
from flask import Flask, request, jsonify
from datetime import datetime
import sys

app = Flask(__name__)

# Improved path logic to find the DB next to the EXE or the script
if getattr(sys, 'frozen', False):
    # If running as a packaged EXE, look in the folder where the EXE is
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # If running as a script, look in the current folder
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "quiz_system.db")

def init_db_if_missing():
    conn = sqlite3.connect(DB_PATH)
    # This creates the table if it doesn't exist so the server won't crash
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT,
            lastname TEXT,
            section TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.close()

def get_db():
    init_db_if_missing() # Run the check
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- API: Student Login Authentication ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    db = get_db()
    user = db.execute("SELECT id, firstname, lastname, section FROM students WHERE username=? AND password=?", 
                      (username, password)).fetchone()
    db.close()

    if user:
        return jsonify({
            "status": "success",
            "student_id": user['id'],
            "name": f"{user['firstname']} {user['lastname']}",
            "section": user['section']
        }), 200
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

# --- API: Get Schedules (Filtered by current time) ---
@app.route('/api/get_schedules', methods=['GET'])
def get_schedules():
    db = get_db()
    # USE SECONDS: Matches the Admin App format exactly
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Checking for quizzes active at: {now}")

    query = """SELECT id, quiz_title, quiz_name FROM schedules 
               WHERE ? BETWEEN start_time AND end_time"""
    
    schedules = db.execute(query, (now,)).fetchall()
    db.close()
    return jsonify([dict(s) for s in schedules]), 200

# --- API: Get Full Quiz Data ---
@app.route('/api/get_full_quiz', methods=['POST'])
def get_full_quiz():
    data = request.json
    schedule_id = data.get('schedule_id')
    
    db = get_db()
    query = "SELECT quiz_title, quiz_data FROM schedules WHERE id=?"
    quiz = db.execute(query, (schedule_id,)).fetchone()
    db.close()
    
    if quiz:
        return jsonify({
            "title": quiz['quiz_title'],
            "questions": json.loads(quiz['quiz_data'])
        }), 200
    
    return jsonify({"status": "error", "message": "Quiz not found"}), 404

# --- API: Receive Quiz Results (Updated with Defeated Boss) ---
@app.route('/api/submit_results', methods=['POST'])
def submit_results():
    data = request.json
    db = get_db()
    
    student_id = data.get('student_id')
    quiz_title = data.get('quiz_title')
    
    try:
        # 1. Check if a record already exists for this student and this quiz
        check_query = "SELECT id FROM results WHERE student_id = ? AND quiz_title = ?"
        existing_record = db.execute(check_query, (student_id, quiz_title)).fetchone()
        
        if existing_record:
            db.close()
            # 403 Forbidden or 409 Conflict are good status codes for "Already Submitted"
            return jsonify({
                "status": "error", 
                "message": "You have already submitted a result for this quiz."
            }), 409

        # 2. If no record exists, proceed with the submission
        details_json = json.dumps(data.get('quiz_details', []))
        boss = data.get('defeated_boss', 'None')
        
        insert_query = """INSERT INTO results (student_id, quiz_title, score, total, defeated_boss, quiz_details) 
                          VALUES (?, ?, ?, ?, ?, ?)"""
        
        db.execute(insert_query, (
            student_id, 
            quiz_title, 
            data['score'], 
            data['total'], 
            boss,
            details_json
        ))
        
        db.commit()
        db.close()
        return jsonify({"status": "success"}), 201

    except Exception as e:
        if db: 
            db.close()
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Server Thread Management ---
class ServerThread(threading.Thread):
    def __init__(self, host='0.0.0.0', port=7777): # Set host to 0.0.0.0 for LAN access
        super().__init__()
        self.host = host
        self.port = port
        self.daemon = True

    def run(self):
        # We run the app defined in this same file
        app.run(host=self.host, port=self.port, debug=False, use_reloader=False)