@echo off
echo Starting Casino Backend and Frontend...

:: Start Backend
start cmd /k "cd /d D:\Casino\casino-backend && uvicorn app.main:app --reload"

:: Start Frontend
start cmd /k "cd /d D:\Casino\casino-frontend && npm start"

echo Casino is starting...
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:3000 