from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    balance = Column(Float, default=1000.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    games = relationship("Game", back_populates="user")
    history = relationship("History", back_populates="user")

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bet = Column(Float, nullable=False)
    win = Column(Float, nullable=False)
    result = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="games")

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_login = Column(String(50), nullable=False)
    bet = Column(Float, nullable=False)
    win = Column(Float, nullable=False)
    multiplier = Column(Float, nullable=True)
    game_type = Column(String(20), nullable=True)
    result = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="history") 