import csv
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDateTimeEdit, QFileDialog, QMessageBox,
                             QLineEdit, QDialog, QTextEdit)
from PySide6.QtCore import QDateTime, Qt

class ResultsTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- SEARCH & FILTERS ---
        top_controls = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        self.name_search = QLineEdit()
        self.name_search.setPlaceholderText("🔍 Search student by name...")
        self.name_search.textChanged.connect(self.filter_table_by_name)
        search_layout.addWidget(QLabel("<b>Search:</b>"))
        search_layout.addWidget(self.name_search)
        top_controls.addLayout(search_layout)

        filter_layout = QHBoxLayout()
        now = QDateTime.currentDateTime()
        self.start_filter = QDateTimeEdit(now.addDays(-7))
        self.start_filter.setCalendarPopup(True)
        self.start_filter.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        
        self.end_filter = QDateTimeEdit(now.addDays(1))
        self.end_filter.setCalendarPopup(True)
        self.end_filter.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        
        btn_refresh = QPushButton("Filter by Date")
        btn_refresh.clicked.connect(self.load_results)
        
        btn_export = QPushButton("Export Visible to CSV")
        btn_export.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_export.clicked.connect(self.export_csv)

        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.start_filter)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.end_filter)
        filter_layout.addWidget(btn_refresh)
        filter_layout.addWidget(btn_export)
        top_controls.addLayout(filter_layout)
        layout.addLayout(top_controls)

        # --- TABLE (Now 8 Columns) ---
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "First Name", "Last Name", "Section", "Quiz Title", "Quiz Code", "Defeated Boss", "Score", "Total", "Percentage (%)", "Details"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setColumnHidden(7, True) # Hidden JSON details
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self.show_scrollable_details)
        
        layout.addWidget(QLabel("<i>Double-click a row to view full question breakdown.</i>"))
        layout.addWidget(self.table)
        
        self.load_results()

    def load_results(self):
        start = self.start_filter.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end = self.end_filter.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        
        # Added r.defeated_boss to the SELECT query
        query = """
            SELECT s.firstname, s.lastname, s.section, r.quiz_title, r.quiz_code, r.defeated_boss, r.score, r.total, r.quiz_details 
            FROM results r
            JOIN students s ON r.student_id = s.id
            WHERE r.timestamp BETWEEN ? AND ?
            ORDER BY r.timestamp DESC
        """
        rows = self.db.query(query, (start, end))

        self.table.setRowCount(0)
        for row in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            score = row["score"]
            total = row["total"]
            perc = (score / total * 100) if total > 0 else 0
            
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row["firstname"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row["lastname"])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row["section"])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(row["quiz_title"])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(row["quiz_code"])))
            # NEW BOSS COLUMN
            boss_name = str(row["defeated_boss"]) if row["defeated_boss"] else "None"
            self.table.setItem(row_idx, 5, QTableWidgetItem(boss_name))
            
            self.table.setItem(row_idx, 6, QTableWidgetItem(str(score)))
            self.table.setItem(row_idx, 7, QTableWidgetItem(str(total)))
            self.table.setItem(row_idx, 8, QTableWidgetItem(f"{perc:.2f}%"))
            self.table.setItem(row_idx, 9, QTableWidgetItem(row["quiz_details"]))

    def filter_table_by_name(self):
        search_text = self.name_search.text().lower()
        for i in range(self.table.rowCount()):
            fname = self.table.item(i, 0).text().lower()
            lname = self.table.item(i, 1).text().lower()
            is_match = search_text in fname or search_text in lname
            self.table.setRowHidden(i, not is_match)

    def show_scrollable_details(self, item):
        row = item.row()
        fname = self.table.item(row, 0).text()
        lname = self.table.item(row, 1).text()
        json_str = self.table.item(row, 7).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Breakdown: {fname} {lname}")
        dialog.setMinimumSize(500, 400)
        d_layout = QVBoxLayout(dialog)
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        
        try:
            history = json.loads(json_str)
            content = f"<h3>Results for {fname} {lname}</h3><hr>"
            for i, entry in enumerate(history, 1):
                status_color = "🟢" if entry['status'].lower() == "correct" else "🔴"
                content += f"<b>{i}. {entry['question']}</b><br>"
                content += f"&nbsp;&nbsp;&nbsp;Student: {entry['student_answer']}<br>"
                content += f"&nbsp;&nbsp;&nbsp;Correct: {entry['correct_answer']}<br>"
                content += f"&nbsp;&nbsp;&nbsp;Status: {status_color} {entry['status']}<br><br>"
            text_area.setHtml(content)
        except:
            text_area.setText("No detailed history available.")

        d_layout.addWidget(text_area)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        d_layout.addWidget(close_btn)
        dialog.exec()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Results", "", "CSV Files (*.csv)")
        if not path: return
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                # Added Defeated Boss to CSV header
                writer.writerow(["First Name", "Last Name","Section", "Quiz Title", "Quiz Code", "Defeated Boss", "Score", "Total", "Percentage"])
                for r in range(self.table.rowCount()):
                    if not self.table.isRowHidden(r):
                        # Export columns 0 through 6 (skipping the hidden JSON column)
                        row_data = [self.table.item(r, c).text() for c in range(7)]
                        writer.writerow(row_data)
            QMessageBox.information(self, "Success", "Exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")