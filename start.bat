@echo off

start "City Twin FastAPI" cmd /k "cd /d C:\Users\GEORGE\OneDrive\Documents\Grad-school\projects\city-twin\city-twin-server && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
