
import os
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from db import db, Base
from werkzeug.middleware.proxy_fix import ProxyFix
import random
import json
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "blackjack-secret-key-2025")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
CORS(app)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///blackjack.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import game logic
from game_logic import GameManager, CARDS, SUITS, calculate_score

game_manager = GameManager()

game_manager = GameManager()

# --- Telegram notification helper ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
def send_telegram_message(user_id, text):
    if not BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": user_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=3)
    except Exception as e:
        logger.warning(f"Failed to send Telegram message: {e}")

# --- Rematch logic ---
rematch_requests = {}

@app.route('/api/rematch/request/<int:chat_id>/<int:user_id>', methods=['POST'])
def request_rematch(chat_id, user_id):
    """Гравець хоче реванш"""
    rematch_requests.setdefault(chat_id, set()).add(user_id)
    return jsonify({'success': True, 'message': 'Rematch requested'})

@app.route('/api/rematch/accept/<int:chat_id>/<int:user_id>', methods=['POST'])
def accept_rematch(chat_id, user_id):
    """Гравець погодився на реванш"""
    rematch_requests.setdefault(chat_id, set()).add(user_id)
    game = game_manager.get_game(chat_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    player1 = game['player1']['id']
    player2 = game['player2']['id']
    if player1 in rematch_requests[chat_id] and player2 in rematch_requests[chat_id]:
        # Both players agreed - create new game
        username1 = game['player1']['username']
        username2 = game['player2']['username']
        mode = game['player1']['mode']
        stake = game['stake']
        
        # Deduct stakes from both players for test mode
        if mode == 'test':
            from models import User
            user1 = User.query.get(player1)
            user2 = User.query.get(player2)
            
            if user1 and user1.balance >= stake:
                user1.balance -= stake
            else:
                return jsonify({'error': 'Player 1 insufficient balance'}), 400
                
            if user2 and user2.balance >= stake:
                user2.balance -= stake
            else:
                return jsonify({'error': 'Player 2 insufficient balance'}), 400
                
            db.session.commit()
        
        # Create new game with same stake
        new_game = game_manager.create_game(chat_id, player1, username1, mode=mode)
        new_game['stake'] = stake  # Set the same stake
        join_result = game_manager.join_game(chat_id, player2, username2)
        
        rematch_requests.pop(chat_id, None)
        
        if 'error' not in join_result:
            return jsonify({'success': True, 'rematch': True, 'message': 'Rematch started', 'game': join_result})
        else:
            return jsonify({'error': join_result['error']}), 400
            
    return jsonify({'success': True, 'rematch': False, 'message': 'Waiting for opponent'})

@app.route('/api/rematch/decline/<int:chat_id>/<int:user_id>', methods=['POST'])
def decline_rematch(chat_id, user_id):
    """Гравець відмовився від реваншу"""
    rematch_requests.pop(chat_id, None)
    return jsonify({'success': True, 'rematch': False, 'message': 'Rematch declined'})

# Routes
@app.route('/')
def index():
    return render_template('blackjack.html')

@app.route('/webapp')
def webapp():
    return render_template('blackjack.html')

@app.route('/join/<int:chat_id>')
def join_game_page(chat_id):
    """Page for joining a game via link"""
    return render_template('join_game.html', chat_id=chat_id)

# API Routes
@app.route('/api/game/<int:chat_id>')
def get_game(chat_id):
    """Get current game state"""
    try:
        game = game_manager.get_game(chat_id)
        if not game:
            return jsonify({'error': 'Game not found', 'message': 'Гра не знайдена'}), 404
        
        return jsonify({
            'success': True,
            'game': game,
            'player1': game['player1'],
            'player2': game['player2'],
            'turn': game['turn'],
            'status': game['status']
        })
    except Exception as e:
        logger.error(f"Error getting game {chat_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/split/<int:chat_id>/<int:user_id>', methods=['POST'])
def split_hand(chat_id, user_id):
    """Split player's hand if possible"""
    try:
        result = game_manager.split_hand(chat_id, user_id)
        if 'error' in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in split_hand for game {chat_id}, user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/hit/<int:chat_id>/<int:user_id>', methods=['POST'])
def hit(chat_id, user_id):
    """Player hits (takes another card)"""
    try:
        from models import User
        result = game_manager.hit(chat_id, user_id)
        if 'error' in result:
            return jsonify(result), 400
        
        # Update database if game finished
        if result.get('result') == 'finished' or result.get('result') == 'bust':
            game = result['game']
            # Close session in DB
            from models import GameSession
            session = GameSession.query.filter_by(chat_id=chat_id).first()
            if session:
                session.status = 'closed'
                from datetime import datetime
                session.finished_at = datetime.utcnow()
                session.winner_id = result.get('winner_id')
            
            # Handle rewards for test mode
            if game['player1']['mode'] == 'test':
                stake = game['stake']
                winner_id = result.get('winner_id')
                
                # Get both players
                player1 = User.query.get(game['player1']['id'])
                player2 = User.query.get(game['player2']['id'])
                
                if winner_id:
                    # Winner gets both stakes
                    winner = User.query.get(winner_id)
                    if winner:
                        winner.balance += stake * 2
                        logger.info(f"Winner {winner_id} received {stake * 2} coins")
                else:
                    # Draw - return stakes to both players
                    if player1:
                        player1.balance += stake
                    if player2:
                        player2.balance += stake
                    logger.info(f"Draw - returned {stake} coins to both players")
                    
            db.session.commit()
            # --- Send Telegram notifications ---
            try:
                p1 = game['player1']
                p2 = game['player2']
                winner = result.get('winner_id')
                if p1 and p2:
                    if winner == p1['id']:
                        send_telegram_message(p1['id'], f"🏆 Ви виграли гру BlackJack! Ставка: {game['stake']}")
                        send_telegram_message(p2['id'], f"❌ Ви програли гру BlackJack. Ставка: {game['stake']}")
                    elif winner == p2['id']:
                        send_telegram_message(p2['id'], f"🏆 Ви виграли гру BlackJack! Ставка: {game['stake']}")
                        send_telegram_message(p1['id'], f"❌ Ви програли гру BlackJack. Ставка: {game['stake']}")
                    else:
                        send_telegram_message(p1['id'], "🤝 Нічия у грі BlackJack!")
                        send_telegram_message(p2['id'], "🤝 Нічия у грі BlackJack!")
            except Exception as e:
                logger.warning(f"Failed to send Telegram notifications: {e}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in hit for game {chat_id}, user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stand/<int:chat_id>/<int:user_id>', methods=['POST'])
def stand(chat_id, user_id):
    """Player stands (stops taking cards)"""
    try:
        from models import User
        result = game_manager.stand(chat_id, user_id)
        if 'error' in result:
            return jsonify(result), 400
        
        # Update database if game finished
        if result.get('result') == 'finished':
            game = result['game']
            # Close session in DB
            from models import GameSession
            session = GameSession.query.filter_by(chat_id=chat_id).first()
            if session:
                session.status = 'closed'
                from datetime import datetime
                session.finished_at = datetime.utcnow()
                session.winner_id = result.get('winner_id')
            
            # Handle rewards for test mode
            if game['player1']['mode'] == 'test':
                stake = game['stake']
                winner_id = result.get('winner_id')
                
                # Get both players
                player1 = User.query.get(game['player1']['id'])
                player2 = User.query.get(game['player2']['id'])
                
                if winner_id:
                    # Winner gets both stakes
                    winner = User.query.get(winner_id)
                    if winner:
                        winner.balance += stake * 2
                        logger.info(f"Winner {winner_id} received {stake * 2} coins")
                else:
                    # Draw - return stakes to both players
                    if player1:
                        player1.balance += stake
                    if player2:
                        player2.balance += stake
                    logger.info(f"Draw - returned {stake} coins to both players")
                    
            db.session.commit()
            # --- Send Telegram notifications ---
            try:
                p1 = game['player1']
                p2 = game['player2']
                winner = result.get('winner_id')
                if p1 and p2:
                    if winner == p1['id']:
                        send_telegram_message(p1['id'], f"🏆 Ви виграли гру BlackJack! Ставка: {game['stake']}")
                        send_telegram_message(p2['id'], f"❌ Ви програли гру BlackJack. Ставка: {game['stake']}")
                    elif winner == p2['id']:
                        send_telegram_message(p2['id'], f"🏆 Ви виграли гру BlackJack! Ставка: {game['stake']}")
                        send_telegram_message(p1['id'], f"❌ Ви програли гру BlackJack. Ставка: {game['stake']}")
                    else:
                        send_telegram_message(p1['id'], "🤝 Нічия у грі BlackJack!")
                        send_telegram_message(p2['id'], "🤝 Нічия у грі BlackJack!")
            except Exception as e:
                logger.warning(f"Failed to send Telegram notifications: {e}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in stand for game {chat_id}, user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sync_game', methods=['POST'])
def sync_game():
    """Synchronize game state from bot"""
    try:
        data = request.json
        chat_id = data.get('chat_id')
        game_data = data.get('game_data')
        
        if chat_id and game_data:
            game_manager.set_game(int(chat_id), game_data)
            return jsonify({'success': True})
        
        return jsonify({'error': 'Invalid data'}), 400
    except Exception as e:
        logger.error(f"Error syncing game: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/games')
def list_games():
    """List active games (for debugging)"""
    try:
        games = game_manager.list_games()
        return jsonify({
            'games': list(games.keys()),
            'total': len(games)
        })
    except Exception as e:
        logger.error(f"Error listing games: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/<int:user_id>/balance')
def get_user_balance(user_id):
    """Get user balance"""
    try:
        from models import User
        user = User.query.get(user_id)
        if not user:
            # Create new user with default balance
            user = User(user_id=user_id, balance=1000.0)
            db.session.add(user)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'balance': user.balance,
            'user_id': user.user_id
        })
    except Exception as e:
        logger.error(f"Error getting balance for user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/<int:user_id>/balance', methods=['POST'])
def update_user_balance(user_id):
    """Update user balance"""
    try:
        from models import User
        data = request.json
        amount = data.get('amount', 0)
        
        user = User.query.get(user_id)
        if not user:
            user = User(user_id=user_id, balance=1000.0)
            db.session.add(user)
        
        user.balance += amount
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_balance': user.balance
        })
    except Exception as e:
        logger.error(f"Error updating balance for user {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/create-demo-game', methods=['POST'])
def create_demo_game():
    """Create a demo game for browser testing"""
    try:
        data = request.json
        chat_id = data.get('chat_id')
        user_id = data.get('user_id') 
        username = data.get('username')
        
        if not all([chat_id, user_id, username]):
            return jsonify({'error': 'Missing required data'}), 400
        
        # Create game using game manager
        game = game_manager.create_game(chat_id, user_id, username, mode='test')
        
        # Add second demo player and start game
        demo_player2_id = user_id + 1
        demo_player2_username = 'ШІ Гравець'
        
        result = game_manager.join_game(chat_id, demo_player2_id, demo_player2_username)
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify({
            'success': True,
            'message': 'Demo game created',
            'game': result
        })
    except Exception as e:
        logger.error(f"Error creating demo game: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create new game session"""
    try:
        from models import User, GameSession
        data = request.json
        user_id = data.get('user_id')
        username = data.get('username')
        game_mode = data.get('mode', 'test')
        chat_id = data.get('chat_id')
        stake = data.get('stake')
        
        if not all([user_id, username, chat_id]):
            return jsonify({'error': 'Missing required data'}), 400
        
        # Check if session already exists for this chat
        existing_session = GameSession.query.filter_by(chat_id=chat_id).first()
        if existing_session:
            # For inline games, if session exists and is waiting, return it
            if existing_session.status == 'waiting' and existing_session.creator_id == user_id:
                return jsonify({
                    'success': True,
                    'session': existing_session.to_dict(),
                    'game': game_manager.get_game(chat_id) or game_manager.create_game(chat_id, user_id, username, mode=game_mode)
                })
            # Allow new session only if previous is closed or finished
            elif existing_session.status not in ['closed', 'finished']:
                return jsonify({'error': 'Session already exists for this chat'}), 400
            else:
                # If previous session is closed/finished, delete it to avoid UNIQUE constraint
                db.session.delete(existing_session)
                db.session.commit()
        
        # Check user balance for test mode
        if game_mode == 'test':
            user = User.query.get(user_id)
            if not user:
                user = User(user_id=user_id, username=username, balance=1000.0)
                db.session.add(user)
                db.session.commit()
            # Ставка за замовчуванням 10, або кастомна
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
            # Для реального режиму можна додати перевірку stake тут
            if stake is None:
                stake = 0.01
            else:
                try:
                    stake = float(stake)
                except Exception:
                    stake = 0.01
        # Create new session
        session = GameSession(
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
    """Join existing game session"""
    try:
        from models import User, GameSession
        import json
        
        data = request.json
        user_id = data.get('user_id')
        username = data.get('username')
        
        if not all([user_id, username]):
            return jsonify({'error': 'Missing user data'}), 400
        
        # Get session from database
        session = GameSession.query.filter_by(chat_id=chat_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if not session.can_join(user_id):
            if session.creator_id == user_id:
                # Creator trying to rejoin their own game - allow it
                game = game_manager.get_game(chat_id)
                if game:
                    return jsonify({
                        'success': True,
                        'session': session.to_dict(),
                        'game': game
                    })
                else:
                    return jsonify({'error': 'Game session expired'}), 400
            elif session.is_full():
                return jsonify({'error': 'Session is full'}), 400
            else:
                return jsonify({'error': 'Session is not available'}), 400
        
        # Check balance for test mode
        if session.game_mode == 'test':
            user = User.query.get(user_id)
            if not user:
                user = User(user_id=user_id, username=username, balance=1000.0)
                db.session.add(user)
                db.session.commit()
            
            if user.balance < session.stake:
                return jsonify({'error': f'Insufficient balance: {user.balance}, required: {session.stake}'}), 400
            
            # Deduct stakes from both players
            creator = User.query.get(session.creator_id)
            if creator:
                creator.balance -= session.stake
            user.balance -= session.stake
            db.session.commit()
        
        # Update session with second player
        session.player2_id = user_id
        session.player2_username = username
        session.status = 'playing'
        db.session.commit()
        
        # Join game in memory
        result = game_manager.join_game(chat_id, user_id, username)
        if 'error' in result:
            return jsonify(result), 400
        
        # Save game state to database
        session.game_data = json.dumps(result)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'game': result
        })
        
    except Exception as e:
        logger.error(f"Error joining session {chat_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sessions/<int:chat_id>/close', methods=['POST'])
def close_session(chat_id):
    """Close game session"""
    try:
        from models import GameSession
        
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        session = GameSession.query.filter_by(chat_id=chat_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Only creator can close the session
        if session.creator_id != user_id:
            return jsonify({'error': 'Only session creator can close the session'}), 403
        
        # Close the session
        session.status = 'closed'
        session.close_session() if hasattr(session, 'close_session') else None
        db.session.commit()
        
        # Remove game from memory
        game_manager.remove_game(chat_id)
        
        return jsonify({
            'success': True,
            'message': 'Session closed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error closing session {chat_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sessions/<int:chat_id>')
def get_session(chat_id):
    """Get session information"""
    try:
        from models import GameSession
        
        logger.info(f"Getting session info for chat_id: {chat_id}")
        session = GameSession.query.filter_by(chat_id=chat_id).first()
        if not session:
            logger.warning(f"Session not found for chat_id: {chat_id}")
            return jsonify({'error': 'Session not found'}), 404
        
        session_data = session.to_dict()
        logger.info(f"Found session: {session_data}")
        
        return jsonify({
            'success': True,
            'session': session_data
        })
        
    except Exception as e:
        logger.error(f"Error getting session {chat_id}: {e}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/sessions')
def list_sessions():
    """List all active sessions"""
    try:
        from models import GameSession
        
        sessions = GameSession.query.filter(GameSession.status.in_(['waiting', 'playing'])).all()
        
        return jsonify({
            'success': True,
            'sessions': [session.to_dict() for session in sessions],
            'total': len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Initialize database tables
def init_db():
    """Initialize database tables"""
    with app.app_context():
        # Import models here to avoid circular import
        from models import User, GameSession
        db.create_all()
        logger.info("Database tables created successfully")

# Initialize database when app starts
init_db()

if __name__ == '__main__':
    app.run(debug=True)
