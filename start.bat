@echo off
echo Starting Casino Application...

:: Start backend server
start cmd /k "cd casino-backend && .\venv\Scripts\activate && cd app && python -m uvicorn __main__:app --reload"

:: Wait for backend to start
timeout /t 5

:: Start frontend server
start cmd /k "cd casino-frontend && npm start"

echo Casino Application is starting...
echo Backend will be available at http://localhost:8000
echo Frontend will be available at http://localhost:3000 