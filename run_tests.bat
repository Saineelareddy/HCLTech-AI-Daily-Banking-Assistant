@echo off
echo ========================================================
echo Running HCLTech AI Daily Banking Assistant Unit Tests...
echo ========================================================
cd /d "%~dp0\daily_banking_assistant"
"C:\Users\saine\OneDrive\Documents\New folder\python_env\python.exe" -m unittest discover -s tests -p "test_*.py" -v
pause

