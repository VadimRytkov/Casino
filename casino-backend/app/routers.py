from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordRequestForm
from . import models, schemas, auth, deps
from .models import User, GameHistory
from .auth import get_password_hash, verify_password, create_access_token
from .schemas import UserCreate, UserOut, Token, SpinRequest, GameHistoryOut
from .deps import get_db, get_current_user
from typing import List
import random

router = APIRouter()

@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/balance", response_model=UserOut)
async def get_balance(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/spin")
async def spin(request: SpinRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bet = request.bet
    if bet <= 0 or bet > current_user.balance:
        raise HTTPException(status_code=400, detail="Invalid bet amount")
    
    symbols = ['🍒', '🍋', '🍊', '🍇', '7️⃣', '💎']
    # Генерируем три барабана по три символа
    reels = [
        [random.choice(symbols) for _ in range(3)],
        [random.choice(symbols) for _ in range(3)],
        [random.choice(symbols) for _ in range(3)],
    ]
    # Центральная линия — это второй символ каждого барабана
    center_line = [reels[0][1], reels[1][1], reels[2][1]]

    win = 0.0
    result_description = ""
    if center_line[0] == center_line[1] == center_line[2]:
        if center_line[0] == '7️⃣':
            win = bet * 10
            result_description = "Джекпот! Три семерки"
        elif center_line[0] == '💎':
            win = bet * 8
            result_description = "Три бриллианта"
        else:
            win = bet * 5
            result_description = "Три одинаковых символа"
    elif center_line[0] == center_line[1] or center_line[1] == center_line[2]:
        win = bet * 2
        result_description = "Два одинаковых символа"
    else:
        result_description = "Нет выигрышной комбинации"

    current_user.balance += win - bet
    game = GameHistory(
        user_id=current_user.id,
        bet=bet,
        win=win,
        result=f"{result_description} ({''.join(center_line)})"
    )
    db.add(game)
    await db.commit()
    await db.refresh(current_user)
    return {"result": center_line, "win": win, "balance": current_user.balance}

@router.get("/history")
async def get_history(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(GameHistory, User.username).join(User).where(GameHistory.user_id == current_user.id).order_by(GameHistory.timestamp.desc())
    result = await db.execute(query)
    games = result.all()
    return [
        {
            "id": game[0].id,
            "timestamp": game[0].timestamp,
            "bet": game[0].bet,
            "win": game[0].win,
            "result": game[0].result,
            "username": game[1]
        }
        for game in games
    ]

@router.put("/update-username")
async def update_username(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_username = request.get("new_username")
    if not new_username:
        raise HTTPException(
            status_code=400,
            detail="New username is required"
        )
    
    # Проверяем, не занят ли новый логин
    existing_user = await db.execute(
        select(User).where(User.username == new_username)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Обновляем логин
    current_user.username = new_username
    await db.commit()
    return {"message": "Username updated successfully"}

@router.put("/update-password")
async def update_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Проверяем текущий пароль
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )
    
    # Обновляем пароль
    current_user.hashed_password = get_password_hash(new_password)
    await db.commit()
    return {"message": "Password updated successfully"}

@router.put("/update-avatar")
async def update_avatar(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    avatar = request.get("avatar")
    if not avatar:
        raise HTTPException(
            status_code=400,
            detail="Avatar data is required"
        )
    
    # Проверяем, что это действительно base64 строка
    if not avatar.startswith('data:image/'):
        raise HTTPException(
            status_code=400,
            detail="Invalid avatar format"
        )
    
    # Обновляем аватар
    current_user.avatar = avatar
    await db.commit()
    return {"message": "Avatar updated successfully"} 