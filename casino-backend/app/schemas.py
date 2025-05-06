from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    balance: float
    avatar: Optional[str] = None
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class GameHistoryOut(BaseModel):
    id: int
    timestamp: datetime
    bet: float
    win: float
    result: str
    username: str
    class Config:
        orm_mode = True

class SpinRequest(BaseModel):
    bet: float 