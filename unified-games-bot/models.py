from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(64), nullable=True)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    language = Column(String(2), default='uk')  # uk, ru, en
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.user_id}: {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///unified_games.db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Ініціалізувати базу даних"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Отримати сесію бази даних"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_by_id(db, user_id: int) -> User:
    """Отримати користувача за ID"""
    return db.query(User).filter(User.user_id == user_id).first()

def create_or_update_user(db, user_id: int, username: str = None, 
                         first_name: str = None, last_name: str = None,
                         language: str = 'uk') -> User:
    """Створити або оновити користувача"""
    user = get_user_by_id(db, user_id)
    
    if user:
        # Оновити існуючого користувача
        if username is not None:
            user.username = username
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if language is not None:
            user.language = language
        user.updated_at = datetime.utcnow()
    else:
        # Створити нового користувача
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    return user

def update_user_language(db, user_id: int, language: str) -> bool:
    """Оновити мову користувача"""
    user = get_user_by_id(db, user_id)
    if user:
        user.language = language
        user.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False

def get_user_language(db, user_id: int) -> str:
    """Отримати мову користувача"""
    user = get_user_by_id(db, user_id)
    return user.language if user else 'uk' 