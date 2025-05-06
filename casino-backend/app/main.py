from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import router
from .database import init_db

app = FastAPI(
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL вашего React приложения
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
def read_root():
    return {"message": "Casino API is running"} 
