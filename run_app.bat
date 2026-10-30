@echo off
echo ========================================================
echo Starting HCLTech AI Daily Banking Assistant Dashboard...
echo ========================================================
cd /d "%~dp0\daily_banking_assistant"
"C:\Users\saine\OneDrive\Documents\New folder\python_env\python.exe" -m streamlit run app.py
pause

