import uvicorn
from fastapi import FastAPI
from app.routers import router
from app.database import init_db

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def on_startup():
    await init_db()

if __name__ == "__main__":
    uvicorn.run("app.__main__:app", host="0.0.0.0", port=8000, reload=True) 
