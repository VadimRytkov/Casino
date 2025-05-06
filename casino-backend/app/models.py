from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=1000.0)  # стартовый баланс
    avatar = Column(String, nullable=True)  # Будет хранить base64 строку изображения
    games = relationship("GameHistory", back_populates="user")

class GameHistory(Base):
    __tablename__ = 'game_history'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    bet = Column(Float, nullable=False)
    win = Column(Float, nullable=False)
    result = Column(String, nullable=False)  # строка с результатом слота
    user = relationship("User", back_populates="games") 