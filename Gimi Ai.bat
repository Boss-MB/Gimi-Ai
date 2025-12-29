@echo off
start cmd /k "python Gimi.py"
timeout /t 5 >nul
start chrome.exe --app=http://127.0.0.1:5000
exit