import os
import logging
import random
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "buckshot-secret-key-2025")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
CORS(app)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///buckshot.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the database
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=True)
    balance = db.Column(db.Float, default=1000.0, nullable=False)
    
    def __init__(self, user_id, username=None, balance=1000.0):
        self.user_id = user_id
        self.username = username
        self.balance = balance
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'balance': self.balance
        }

class BuckshotSession(db.Model):
    __tablename__ = 'buckshot_sessions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chat_id = db.Column(db.Integer, unique=True, nullable=False)
    creator_id = db.Column(db.Integer, nullable=False)
    creator_username = db.Column(db.String(64), nullable=False)
    player2_id = db.Column(db.Integer, nullable=True)
    player2_username = db.Column(db.String(64), nullable=True)
    game_mode = db.Column(db.String(10), default='test')  # 'test' or 'real'
    stake = db.Column(db.Float, default=10.0)
    status = db.Column(db.String(20), default='waiting')  # 'waiting', 'playing', 'finished', 'closed'
    game_data = db.Column(db.Text, nullable=True)  # JSON string with game state
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    winner_id = db.Column(db.Integer, nullable=True)
    
    def __init__(self, chat_id, creator_id, creator_username, game_mode='test', stake=10.0):
        self.chat_id = chat_id
        self.creator_id = creator_id
        self.creator_username = creator_username
        self.game_mode = game_mode
        self.stake = stake
        self.status = 'waiting'
    
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
            'game_data': self.game_data,
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

# Game Logic
class BuckshotGameManager:
    def __init__(self):
        self.games = {}  # chat_id -> game_state
    
    def create_game(self, chat_id, player1_id, player1_username, mode='test'):
        """Create new game state"""
        shell_count = random.randint(3, 8)
        live_count = random.randint(1, shell_count - 1)
        blank_count = shell_count - live_count
        
        # Create shell array
        shells = ['live'] * live_count + ['blank'] * blank_count
        random.shuffle(shells)
        
        # Generate bonuses for each player
        def generate_bonuses():
            bonus_types = ['magnifying', 'beer', 'handcuffs', 'cigarettes', 'knife']
            bonus_count = random.randint(2, 3)
            bonuses = []
            for _ in range(bonus_count):
                bonus_type = random.choice(bonus_types)
                bonuses.append({'type': bonus_type, 'used': False})
            return bonuses
        
        game_state = {
            'players': [
                {
                    'id': str(player1_id),
                    'name': player1_username,
                    'health': 3,
                    'bonuses': generate_bonuses(),
                    'isHandcuffed': False
                },
                {
                    'id': 'waiting',
                    'name': 'Waiting for player...',
                    'health': 3,
                    'bonuses': generate_bonuses(),
                    'isHandcuffed': False
                }
            ],
            'currentPlayer': 0,
            'shells': shells,
            'currentShell': 0,
            'gamePhase': 'waiting',  # waiting, playing, round-end, finished
            'winner': None,
            'knifeBonusActive': False,
            'lastAction': '',
            'round': 1,
            'maxRounds': 5,
            'mode': mode
        }
        
        self.games[chat_id] = game_state
        return game_state
    
    def join_game(self, chat_id, player2_id, player2_username):
        """Join existing game"""
        if chat_id not in self.games:
            return None
        
        game = self.games[chat_id]
        if game['gamePhase'] != 'waiting':
            return None
        
        # Update player 2
        game['players'][1] = {
            'id': str(player2_id),
            'name': player2_username,
            'health': 3,
            'bonuses': game['players'][1]['bonuses'],  # Keep existing bonuses
            'isHandcuffed': False
        }
        
        game['gamePhase'] = 'playing'
        game['lastAction'] = f'{player2_username} joined the game!'
        
        return game
    
    def get_game(self, chat_id):
        """Get current game state"""
        return self.games.get(chat_id)
    
    def update_game(self, chat_id, game_data):
        """Update game state"""
        if chat_id in self.games:
            self.games[chat_id] = game_data
            return True
        return False
    
    def end_game(self, chat_id, winner_id=None):
        """End game and clean up"""
        if chat_id in self.games:
            game = self.games[chat_id]
            game['gamePhase'] = 'finished'
            if winner_id:
                game['winner'] = winner_id
            return True
        return False

# Initialize game manager
game_manager = BuckshotGameManager()

# API Routes
@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create new Buckshot Roulette session"""
    try:
        data = request.json
        user_id = data.get('user_id')
        username = data.get('username')
        game_mode = data.get('mode', 'test')
        chat_id = data.get('chat_id')
        stake = data.get('stake')
        
        if not all([user_id, username, chat_id]):
            return jsonify({'error': 'Missing required data'}), 400
        
        # Check if session already exists for this chat
        existing_session = BuckshotSession.query.filter_by(chat_id=chat_id).first()
        if existing_session:
            if existing_session.status == 'waiting' and existing_session.creator_id == user_id:
                return jsonify({
                    'success': True,
                    'session': existing_session.to_dict(),
                    'game': game_manager.get_game(chat_id) or game_manager.create_game(chat_id, user_id, username, mode=game_mode)
                })
            elif existing_session.status not in ['closed', 'finished']:
                return jsonify({'error': 'Session already exists for this chat'}), 400
            else:
                db.session.delete(existing_session)
                db.session.commit()
        
        # Check user balance for test mode
        if game_mode == 'test':
            user = User.query.get(user_id)
            if not user:
                user = User(user_id=user_id, username=username, balance=1000.0)
                db.session.add(user)
                db.session.commit()
            
            if stake is None:
                stake = 10.0
            else:
                try:
                    stake = float(stake)
                except Exception:
                    stake = 10.0
                    
            if user.balance < stake:
                return jsonify({'error': f'Insufficient balance: {user.balance}, required: {stake}'}), 400
        else:
            if stake is None:
                stake = 0.01
            else:
                try:
                    stake = float(stake)
                except Exception:
                    stake = 0.01
        
        # Create new session
        session = BuckshotSession(
            chat_id=chat_id,
            creator_id=user_id,
            creator_username=username,
            game_mode=game_mode,
            stake=stake
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Create game in memory
        game = game_manager.create_game(chat_id, user_id, username, mode=game_mode)
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'game': game
        })
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sessions/<int:chat_id>/join', methods=['POST'])
def join_session(chat_id):
    """Join existing Buckshot Roulette session"""
    try:
        data = request.json
        user_id = data.get('user_id')
        username = data.get('username')
        
        if not all([user_id, username]):
            return jsonify({'error': 'Missing user data'}), 400
        
        # Get session from database
        session = BuckshotSession.query.filter_by(chat_id=chat_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if not session.can_join(user_id):
            return jsonify({'error': 'Cannot join this session'}), 400
        
        # Check user balance for test mode
        if session.game_mode == 'test':
            user = User.query.get(user_id)
            if not user:
                user = User(user_id=user_id, username=username, balance=1000.0)
                db.session.add(user)
                db.session.commit()
            
            if user.balance < session.stake:
                return jsonify({'error': f'Insufficient balance: {user.balance}, required: {session.stake}'}), 400
        
        # Update session
        session.player2_id = user_id
        session.player2_username = username
        session.status = 'playing'
        db.session.commit()
        
        # Join game in memory
        game = game_manager.join_game(chat_id, user_id, username)
        if not game:
            return jsonify({'error': 'Game not found or cannot join'}), 400
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'game': game
        })
        
    except Exception as e:
        logger.error(f"Error joining session: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sessions/<int:chat_id>')
def get_session(chat_id):
    """Get session and game state"""
    try:
        session = BuckshotSession.query.filter_by(chat_id=chat_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        game = game_manager.get_game(chat_id)
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'game': game
        })
        
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sessions/<int:chat_id>/close', methods=['POST'])
def close_session(chat_id):
    """Close session"""
    try:
        session = BuckshotSession.query.filter_by(chat_id=chat_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session.status = 'closed'
        session.finished_at = datetime.utcnow()
        db.session.commit()
        
        # Clean up game in memory
        game_manager.end_game(chat_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error closing session: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/game/<int:chat_id>/update', methods=['POST'])
def update_game(chat_id):
    """Update game state"""
    try:
        data = request.json
        game_data = data.get('game')
        user_id = data.get('user_id')
        
        if not game_data or not user_id:
            return jsonify({'error': 'Missing game data or user_id'}), 400
        
        # Verify user is part of the game
        session = BuckshotSession.query.filter_by(chat_id=chat_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if str(session.creator_id) != str(user_id) and str(session.player2_id) != str(user_id):
            return jsonify({'error': 'Not authorized'}), 403
        
        # Update game state
        success = game_manager.update_game(chat_id, game_data)
        if not success:
            return jsonify({'error': 'Game not found'}), 404
        
        # Update session if game is finished
        if game_data.get('gamePhase') == 'finished':
            winner = game_data.get('winner')
            if winner:
                session.winner_id = winner.get('id')
            session.status = 'finished'
            session.finished_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating game: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sessions')
def list_sessions():
    """List all active sessions"""
    try:
        sessions = BuckshotSession.query.filter_by(status='waiting').all()
        return jsonify({
            'success': True,
            'sessions': [session.to_dict() for session in sessions]
        })
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/<int:user_id>/balance')
def get_user_balance(user_id):
    """Get user balance"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'balance': user.balance
        })
    except Exception as e:
        logger.error(f"Error getting user balance: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/<int:user_id>/balance', methods=['POST'])
def update_user_balance(user_id):
    """Update user balance (for test mode)"""
    try:
        data = request.json
        new_balance = data.get('balance')
        
        if new_balance is None:
            return jsonify({'error': 'Missing balance'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.balance = float(new_balance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'balance': user.balance
        })
    except Exception as e:
        logger.error(f"Error updating user balance: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        logger.info("Database initialized")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True) 