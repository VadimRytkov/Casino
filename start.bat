@echo off
echo Starting Casino application...

:: Запуск бэкенда
start cmd /k "cd casino-backend && uvicorn app.main:app --reload"

:: Ждем 5 секунд, чтобы бэкенд успел запуститься
timeout /t 5

:: Запуск фронтенда
start cmd /k "cd casino-frontend && npm start"

echo Casino application is starting...
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:3000
echo.
echo Press any key to close all windows...
pause > nul

:: Закрываем все окна командной строки
taskkill /F /IM cmd.exe 