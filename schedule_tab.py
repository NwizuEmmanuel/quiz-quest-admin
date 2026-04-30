import json, os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDateTimeEdit, QFileDialog, QFrame, QMessageBox)
from PySide6.QtCore import QDateTime, Qt

class ScheduleTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.selected_sched_id = None
        self.embedded_json_content = ""
        self.setup_ui()

    def setup_ui(self):
        # MAIN LAYOUT
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)

        # --- STEP 1: FILE BINDING ---
        self.main_layout.addWidget(QLabel("<b>STEP 1: BIND QUIZ FILE</b>"))
        file_row = QHBoxLayout()
        self.file_display = QLineEdit()
        self.file_display.setPlaceholderText("No file selected...")
        self.file_display.setReadOnly(True)
        self.btn_browse = QPushButton("Browse JSON")
        self.btn_browse.clicked.connect(self.browse_quiz_file)
        file_row.addWidget(self.file_display)
        file_row.addWidget(self.btn_browse)
        self.main_layout.addLayout(file_row)

        # --- STEP 2: DETAILS ---
        self.main_layout.addWidget(QLabel("<b>STEP 2: SCHEDULE DETAILS</b>"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Quiz Title (e.g. Midterm Exam)")
        self.main_layout.addWidget(QLabel("Display Title:"))
        self.main_layout.addWidget(self.title_input)

        # add quiz code input
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("eg. prelim-cs-2")
        self.main_layout.addWidget(QLabel("Quiz Code"))
        self.main_layout.addWidget(self.code_input)

        # --- DATE TIME PICKERS ---
        dt_container = QHBoxLayout()
        
        # Start Date
        v_start = QVBoxLayout()
        self.start_dt = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_dt.setCalendarPopup(True)
        self.start_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        v_start.addWidget(QLabel("<b>Start Time:</b>"))
        v_start.addWidget(self.start_dt)
        
        # End Date
        v_end = QVBoxLayout()
        self.end_dt = QDateTimeEdit(QDateTime.currentDateTime().addDays(1))
        self.end_dt.setCalendarPopup(True)
        self.end_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        v_end.addWidget(QLabel("<b>End Time:</b>"))
        v_end.addWidget(self.end_dt)
        
        dt_container.addLayout(v_start)
        dt_container.addLayout(v_end)
        self.main_layout.addLayout(dt_container)

        # --- STEP 3: SAVE BUTTONS ---
        self.btn_save = QPushButton("Save Schedule")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_schedule)
        self.main_layout.addWidget(self.btn_save)

        self.main_layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine))

        # --- STEP 4: TABLE ---
        self.main_layout.addWidget(QLabel("<b>ACTIVE SCHEDULES</b>"))
        self.table = QTableWidget(0, 6) # Increased to 6 to show all columns
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Quiz File", "Quiz Code", "Start Time", "End Time"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemClicked.connect(self.load_schedule_data)
        self.main_layout.addWidget(self.table)

        self.btn_del = QPushButton("Delete Selected")
        self.btn_del.setStyleSheet("background-color: #e74c3c; color: white;")
        self.btn_del.clicked.connect(self.delete_schedule)
        self.main_layout.addWidget(self.btn_del)

        self.refresh_table()

    def browse_quiz_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Quiz", "", "JSON (*.json)")
        if path:
            try:
                with open(path, 'r') as f:
                    self.embedded_json_content = json.dumps(json.load(f))
                    self.file_display.setText(os.path.basename(path))
            except Exception as e:
                QMessageBox.critical(self, "File Error", f"Could not read JSON: {str(e)}")

    def save_schedule(self):
        title = self.title_input.text().strip()
        start = self.start_dt.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end = self.end_dt.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        quiz_code = self.code_input.text().strip().upper()

        if not title or not self.embedded_json_content:
            QMessageBox.warning(self, "Error", "Title and Quiz File are required.")
            return

        if not quiz_code:
            QMessageBox.warning(self, "Error", "Quiz code can't be empty.")
            return
        
        if self.selected_sched_id:
            sql = """UPDATE schedules SET quiz_title=?, quiz_name=?, quiz_data=?, 
                    quiz_code=?, start_time=?, end_time=? WHERE id=?"""
            self.db.execute(sql, (title, self.file_display.text(), self.embedded_json_content, 
                                quiz_code, start, end, self.selected_sched_id))
        else:
            sql = """INSERT INTO schedules (quiz_title, quiz_name, quiz_data, quiz_code, start_time, end_time) 
                    VALUES (?,?,?,?,?,?)"""
            self.db.execute(sql, (title, self.file_display.text(), self.embedded_json_content, quiz_code, start, end))

        self.refresh_table()
        self.clear_form()

    def load_schedule_data(self, item):
        row = item.row()
        self.selected_sched_id = self.table.item(row, 0).text()
        
        res = self.db.query("SELECT * FROM schedules WHERE id=?", (self.selected_sched_id,))
        
        if res:
            data = res[0]
            self.title_input.setText(data["quiz_title"])
            self.code_input.setText(data["quiz_code"])
            self.file_display.setText(data["quiz_name"])
            self.embedded_json_content = data["quiz_data"]
            
            # Note: format "yyyy-MM-dd HH:mm:ss" must match what was saved in save_schedule
            self.start_dt.setDateTime(QDateTime.fromString(data["start_time"], "yyyy-MM-dd HH:mm:ss"))
            self.end_dt.setDateTime(QDateTime.fromString(data["end_time"], "yyyy-MM-dd HH:mm:ss"))
            
            self.btn_save.setText("Update Selected Schedule")
            self.btn_save.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; height: 35px;")

    def delete_schedule(self):
        if self.selected_sched_id:
            self.db.execute("DELETE FROM schedules WHERE id=?", (self.selected_sched_id,))
            self.refresh_table()
            self.clear_form()
        else:
            QMessageBox.information(self, "Select", "Please select a schedule from the table first.")

    def clear_form(self):
        self.selected_sched_id = None
        self.embedded_json_content = ""
        self.title_input.clear()
        self.code_input.clear()
        self.file_display.clear()
        self.start_dt.setDateTime(QDateTime.currentDateTime())
        self.end_dt.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.btn_save.setText("Save Schedule")
        self.btn_save.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; height: 40px;")

    def refresh_table(self):
        self.table.setRowCount(0)
        res = self.db.query("SELECT id, quiz_title, quiz_name, quiz_code, start_time, end_time FROM schedules")
        for r_idx, row in enumerate(res): 
            self.table.insertRow(r_idx)
            self.table.setItem(r_idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r_idx, 1, QTableWidgetItem(str(row["quiz_title"])))
            self.table.setItem(r_idx, 2, QTableWidgetItem(str(row["quiz_name"])))
            self.table.setItem(r_idx, 3, QTableWidgetItem(str(row["quiz_code"])))
            self.table.setItem(r_idx, 4, QTableWidgetItem(str(row["start_time"])))
            self.table.setItem(r_idx, 5, QTableWidgetItem(str(row["end_time"])))