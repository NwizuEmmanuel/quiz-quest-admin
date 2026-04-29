Remove-Item -Recurse -Force dist, build;
pyinstaller --noconsole --onefile --add-data "server_worker.py;." --add-data "database.py;." --name "QuizQuestAdmin" .\main.py