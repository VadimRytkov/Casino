from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Пароль пользователя")

class UserLogin(UserBase):
    password: str = Field(..., description="Пароль пользователя")

class UserOut(UserBase):
    id: int
    balance: float
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

class GameBase(BaseModel):
    bet: float = Field(..., gt=0, description="Ставка в игре")
    win: float = Field(..., ge=0, description="Выигрыш в игре")
    result: str = Field(..., description="Результат игры")

class GameCreate(GameBase):
    pass

class Game(BaseModel):
    id: int
    user_id: int
    bet: float
    win: float
    result: str
    created_at: datetime

    class Config:
        orm_mode = True

class GameHistoryOut(BaseModel):
    id: int
    bet: float
    win: float
    result: str
    created_at: datetime

    class Config:
        orm_mode = True

class SpinRequest(BaseModel):
    bet: float

class Balance(BaseModel):
    balance: float 