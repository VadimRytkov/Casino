from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import random
import string
import logging
from jose import JWTError, jwt
from . import models, schemas, database
from .database import SessionLocal, engine
from passlib.context import CryptContext
from .models import User, Game
from .database import get_db
from .auth import get_current_user

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем таблицы при запуске приложения
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Casino API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройки JWT
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # В продакшене использовать переменную окружения
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def generate_user_id():
    """Генерирует уникальный ID пользователя в формате VIP-XXXX-XXXX"""
    while True:
        # Генерируем случайную строку из 8 символов
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        # Форматируем ID как VIP-XXXX-XXXX
        user_id = f"VIP-{random_str[:4]}-{random_str[4:]}"
        return user_id

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(user_id=user_id)
    except jwt.JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.id == int(token_data.user_id)).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/check-user/{user_id}")
def check_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return {"message": "Пользователь существует"}

@app.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Начало регистрации пользователя: {user.username}")
        
        # Проверяем длину пароля
        if len(user.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Пароль должен содержать минимум 6 символов"
            )
        
        # Проверяем, существует ли пользователь с таким именем
        db_user = db.query(models.User).filter(models.User.username == user.username).first()
        if db_user:
            logger.warning(f"Попытка регистрации с существующим именем: {user.username}")
            raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")
        
        # Создаем нового пользователя
        logger.info("Создание нового пользователя")
        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            username=user.username,
            password=hashed_password,
            balance=1000  # Начальный баланс
        )
        
        logger.info("Сохранение пользователя в базу данных")
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Создаем токен
        logger.info("Создание токена доступа")
        access_token = create_access_token(data={"sub": str(db_user.id)})
        logger.info(f"Успешная регистрация пользователя: {user.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as he:
        logger.error(f"Ошибка HTTP при регистрации: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Неожиданная ошибка при регистрации: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при регистрации: {str(e)}"
        )

@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.username == user.username).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль"
            )
        if not verify_password(user.password, db_user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль"
            )
        access_token = create_access_token(data={"sub": str(db_user.id)})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Ошибка при входе: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера"
        )

@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )
    
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user

@app.get("/balance", response_model=schemas.Balance)
def get_balance(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )
    
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return {"balance": user.balance}

@app.post("/spin")
async def spin(bet: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Проверяем баланс
    if current_user.balance < bet:
        raise HTTPException(status_code=400, detail="Недостаточно средств")

    # Генерируем случайное число от 5 до 15
    win_chance = random.randint(5, 15)
    
    # Генерируем случайное число от 1 до 100
    roll = random.randint(1, 100)
    
    # Если выпало число меньше или равное шансу выигрыша, то это выигрыш
    is_win = roll <= win_chance
    
    # Генерируем символы для слотов
    symbols = ['🍒', '🍊', '🍋', '🍇', '7️⃣', '💎']
    result = []
    
    if is_win:
        # Если выигрыш, генерируем три одинаковых символа для центральной строки
        win_symbol = random.choice(symbols)
        # Генерируем первую строку
        result.extend([random.choice(symbols) for _ in range(3)])
        # Генерируем выигрышную центральную строку
        result.extend([win_symbol] * 3)
        # Генерируем последнюю строку
        result.extend([random.choice(symbols) for _ in range(3)])
        win_amount = bet * 3  # Выигрыш в 3 раза больше ставки
    else:
        # Если проигрыш, генерируем случайные символы
        result = [random.choice(symbols) for _ in range(9)]
        win_amount = 0

    # Обновляем баланс пользователя
    current_user.balance = current_user.balance - bet + win_amount
    
    # Создаем запись в истории
    history = History(
        player_id=current_user.id,
        player_login=current_user.username,
        bet=bet,
        win=win_amount,
        result=' '.join(result)
    )
    db.add(history)
    db.commit()
    
    return {
        "result": ' '.join(result),
        "bet": bet,
        "win": win_amount
    }

@app.post("/rocket/stop")
async def rocket_stop(
    bet: int,
    win: float,
    multiplier: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверяем баланс
    if current_user.balance < bet:
        raise HTTPException(status_code=400, detail="Недостаточно средств")

    # Обновляем баланс пользователя
    current_user.balance = current_user.balance - bet + win
    
    # Создаем запись в истории
    history = History(
        player_id=current_user.id,
        player_login=current_user.username,
        bet=bet,
        win=win,
        multiplier=multiplier,
        game_type='rocket'
    )
    db.add(history)
    db.commit()
    
    return {"balance": current_user.balance}

@app.post("/rocket/crash")
async def rocket_crash(
    bet: int,
    win: float,
    multiplier: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверяем баланс
    if current_user.balance < bet:
        raise HTTPException(status_code=400, detail="Недостаточно средств")

    # Обновляем баланс пользователя (проигрыш)
    current_user.balance = current_user.balance - bet
    
    # Создаем запись в истории
    history = History(
        player_id=current_user.id,
        player_login=current_user.username,
        bet=bet,
        win=0,
        multiplier=multiplier,
        game_type='rocket'
    )
    db.add(history)
    db.commit()
    
    return {"balance": current_user.balance}

@app.get("/history", response_model=List[schemas.GameHistoryOut])
def get_game_history(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )
    
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    games = db.query(models.Game).filter(models.Game.user_id == user.id).order_by(models.Game.created_at.desc()).all()
    return games 
