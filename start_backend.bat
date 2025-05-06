@echo off
cd casino-backend
call .\venv\Scripts\activate
cd app
python -m uvicorn __main__:app --reload 