import sys
import multiprocessing
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from database import Database
from quiz_tab import QuizTab
from student_tab import StudentTab
from schedule_tab import ScheduleTab
from results_tab import ResultsTab
from server_tab import ServerTab


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quiz Architect Pro")
        self.setMinimumSize(1000, 800)
        
        # 1. Initialize Shared Database
        self.db = Database()

        # 2. Setup Central Tab Widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 3. Initialize and Add Tabs
        self.quiz_page = QuizTab()
        self.student_page = StudentTab(self.db)
        self.schedule_page = ScheduleTab(self.db)
        self.results_page = ResultsTab(self.db)

        self.tabs.addTab(self.quiz_page, "1. Quiz Creator")
        self.tabs.addTab(self.student_page, "2. Student Manager")
        self.tabs.addTab(self.schedule_page, "3. Quiz Scheduling")
        self.server_page = ServerTab()
        self.tabs.addTab(self.server_page, "4. Server Control")
        self.tabs.addTab(self.results_page, "5. Results")

    def closeEvent(self, event):
        """Handle unsaved changes in the Quiz Tab before exiting."""
        if self.quiz_page.has_unsaved_changes:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Unsaved Changes")
            msg_box.setText("The quiz has pending changes.")
            msg_box.setInformativeText("Do you want to save your changes before exiting?")
            
            # Standard Buttons
            save_btn = msg_box.addButton(QMessageBox.StandardButton.Save)
            discard_btn = msg_box.addButton(QMessageBox.StandardButton.Discard)
            cancel_btn = msg_box.addButton(QMessageBox.StandardButton.Cancel)
            
            msg_box.setDefaultButton(save_btn)
            msg_box.exec()
            
            clicked_button = msg_box.clickedButton()

            if clicked_button == save_btn:
                # Attempt to save to the current file or prompt for new one
                if self.quiz_page.quick_save():
                    event.accept()
                else:
                    # If user cancels the file dialog, don't close the app
                    event.ignore()
            
            elif clicked_button == discard_btn:
                event.accept()
            
            else: # Cancel button or 'X' clicked
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    # REQUIRED for the Stop/Start buttons to work on Windows
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    
    # Optional: Apply a global style for a cleaner look
    # app.setStyleSheet("""
    #     QMainWindow { background-color: #f5f5f5; }
    #     QPushButton { padding: 5px; border-radius: 3px; }
    #     QTableWidget { gridline-color: #dcdcdc; }
    # """)
    
    window = MainApp()
    window.show()
    sys.exit(app.exec())