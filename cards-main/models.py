from db import db
from sqlalchemy import Integer, String, Float, Text, DateTime, Boolean
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(Integer, primary_key=True)
    username = db.Column(String(64), nullable=True)
    balance = db.Column(Float, default=1000.0, nullable=False)
    
    def __init__(self, user_id, username=None, balance=1000.0):
        self.user_id = user_id
        self.username = username
        self.balance = balance
    
    def __repr__(self):
        return f'<User {self.user_id}: {self.username}>'
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'balance': self.balance
        }

class GameSession(db.Model):
    __tablename__ = 'game_sessions'
    
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    chat_id = db.Column(Integer, unique=True, nullable=False)
    creator_id = db.Column(Integer, nullable=False)
    creator_username = db.Column(String(64), nullable=False)
    player2_id = db.Column(Integer, nullable=True)
    player2_username = db.Column(String(64), nullable=True)
    game_mode = db.Column(String(10), default='test')  # 'test' or 'real'
    stake = db.Column(Float, default=10.0)
    status = db.Column(String(20), default='waiting')  # 'waiting', 'playing', 'finished', 'closed'
    game_data = db.Column(Text, nullable=True)  # JSON string with game state
    created_at = db.Column(DateTime, default=datetime.utcnow)
    finished_at = db.Column(DateTime, nullable=True)
    winner_id = db.Column(Integer, nullable=True)
    
    def __init__(self, chat_id, creator_id, creator_username, game_mode='test', stake=10.0):
        self.chat_id = chat_id
        self.creator_id = creator_id
        self.creator_username = creator_username
        self.game_mode = game_mode
        self.stake = stake
        self.status = 'waiting'
    
    def __repr__(self):
        return f'<GameSession {self.chat_id}: {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'creator_id': self.creator_id,
            'creator_username': self.creator_username,
            'player2_id': self.player2_id,
            'player2_username': self.player2_username,
            'game_mode': self.game_mode,
            'stake': self.stake,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'winner_id': self.winner_id
        }
    
    def is_full(self):
        return self.player2_id is not None
    
    def is_active(self):
        return self.status in ['waiting', 'playing']
    
    def can_join(self, user_id):
        return not self.is_full() and self.creator_id != user_id and self.is_active()
    
    def close_session(self):
        self.status = 'closed'
        self.finished_at = datetime.utcnow()