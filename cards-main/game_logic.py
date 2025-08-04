import random
import logging

logger = logging.getLogger(__name__)

# Cards configuration
CARDS = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}
SUITS = ['♠', '♥', '♦', '♣']

def calculate_score(cards):
    """Calculate the score of a hand of cards"""
    if not cards:
        return 0
    
    score = sum(CARDS[card[:-1]] for card in cards)
    aces = sum(1 for card in cards if card[:-1] == 'A')
    
    # Adjust for aces
    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
    
    return score

def can_split(cards):
    """Check if cards can be split (same rank)"""
    if len(cards) != 2:
        return False
    
    # Get card ranks (without suits)
    rank1 = cards[0][:-1]
    rank2 = cards[1][:-1]
    
    # Same rank means can split
    return rank1 == rank2

def create_deck():
    """Create a shuffled deck of cards (6 decks)"""
    deck = []
    for _ in range(6):  # 6 decks for casino style
        for card in CARDS.keys():
            for suit in SUITS:
                deck.append(f"{card}{suit}")
    
    random.shuffle(deck)
    return deck

class GameManager:
    """Manages all active games"""
    
    def __init__(self):
        self.games = {}
    
    def create_game(self, chat_id, player1_id, player1_username, mode='test'):
        """Create a new game"""
        stake = 10.0 if mode == 'test' else 0.01
        
        self.games[chat_id] = {
            'player1': {
                'id': player1_id,
                'username': player1_username,
                'cards': [],
                'score': 0,
                'stand': False,
                'mode': mode,
                'split_hands': [],  # Додаткові руки для спліту
                'active_hand': 0    # Активна рука (0 = основна)
            },
            'player2': None,
            'stake': stake,
            'turn': player1_id,
            'status': 'waiting',
            'deck': create_deck()
        }
        
        return self.games[chat_id]
    
    def join_game(self, chat_id, player2_id, player2_username):
        """Add second player to game and start"""
        if chat_id not in self.games:
            return {'error': 'Game not found'}
        
        game = self.games[chat_id]
        
        if game['player2'] is not None:
            return {'error': 'Game is full'}
        
        if game['player1']['id'] == player2_id:
            return {'error': 'Cannot play against yourself'}
        
        # Add second player
        game['player2'] = {
            'id': player2_id,
            'username': player2_username,
            'cards': [],
            'score': 0,
            'stand': False,
            'mode': game['player1']['mode'],
            'split_hands': [],  # Додаткові руки для спліту
            'active_hand': 0    # Активна рука (0 = основна)
        }
        
        # Deal only one card to each player at the start
        game['player1']['cards'].append(game['deck'].pop())
        game['player2']['cards'].append(game['deck'].pop())
        
        # Calculate scores
        game['player1']['score'] = calculate_score(game['player1']['cards'])
        game['player2']['score'] = calculate_score(game['player2']['cards'])
        
        # Set game status
        game['status'] = 'playing'
        
        return game
    
    def hit(self, chat_id, user_id):
        """Player takes another card"""
        if chat_id not in self.games:
            return {'error': 'Game not found'}
        
        game = self.games[chat_id]
        
        if game['turn'] != user_id:
            return {'error': 'Not your turn'}
        
        if game['status'] != 'playing':
            return {'error': 'Game not active'}
        
        # Determine player
        if game['player1']['id'] == user_id:
            player_key = 'player1'
            opponent_key = 'player2'
        elif game['player2'] and game['player2']['id'] == user_id:
            player_key = 'player2'
            opponent_key = 'player1'
        else:
            return {'error': 'Player not found'}
        
        # Block hit if player has already stood
        if game[player_key]['stand']:
            return {'error': 'Ви вже натиснули "Пас" і не можете брати карти!'}
        
        # Deal card
        if len(game['deck']) == 0:
            return {'error': 'No more cards'}
        
        new_card = game['deck'].pop()
        
        player = game[player_key]
        current_score = 0
        
        # Deal card to the active hand
        if len(player['split_hands']) > 0:
            if player['active_hand'] == 0:
                # Playing main hand
                player['cards'].append(new_card)
                player['score'] = calculate_score(player['cards'])
                current_score = player['score']
            else:
                # Playing split hand
                player['split_hands'][0]['cards'].append(new_card)
                player['split_hands'][0]['score'] = calculate_score(player['split_hands'][0]['cards'])
                current_score = player['split_hands'][0]['score']
        else:
            # No split, normal play
            player['cards'].append(new_card)
            player['score'] = calculate_score(player['cards'])
            current_score = player['score']
        
        # Check for bust on current hand
        if current_score > 21:
            # If player has split hands, just mark current hand as bust and potentially switch
            if len(player['split_hands']) > 0:
                if player['active_hand'] == 0:
                    # Main hand bust, switch to split hand
                    player['active_hand'] = 1
                    return {
                        'success': True,
                        'result': 'hand_bust_switch',
                        'message': f"Перша рука перебрала! Грайте другою рукою.",
                        'game': game,
                        'new_card': new_card,
                        'active_hand': 1
                    }
                else:
                    # Split hand bust, check if all hands are done
                    # Both hands played, evaluate total result
                    return self._evaluate_split_hands(chat_id, player_key, opponent_key, new_card)
            else:
                # Regular bust - game over
                game['status'] = 'finished'
                winner_key = opponent_key
                
                return {
                    'success': True,
                    'result': 'bust',
                    'message': f"Перебор! {game[player_key]['username']} програв!",
                    'winner': game[winner_key]['username'],
                    'winner_id': game[winner_key]['id'],
                    'game': game,
                    'new_card': new_card
                }
        
        # Switch turn
        if game['player2']:
            game['turn'] = game['player2']['id'] if player_key == 'player1' else game['player1']['id']
        
        return {
            'success': True,
            'result': 'continue',
            'game': game,
            'new_card': new_card
        }
    
    def stand(self, chat_id, user_id):
        """Player stands (stops taking cards)"""
        if chat_id not in self.games:
            return {'error': 'Game not found'}
        
        game = self.games[chat_id]
        
        if game['turn'] != user_id:
            return {'error': 'Not your turn'}
        
        # Determine player
        if game['player1']['id'] == user_id:
            player_key = 'player1'
        elif game['player2'] and game['player2']['id'] == user_id:
            player_key = 'player2'
        else:
            return {'error': 'Player not found'}
        
        game[player_key]['stand'] = True
        
        # Check if both players have stood
        if game['player1']['stand'] and game['player2'] and game['player2']['stand']:
            return self._finish_game(chat_id)
        
        # Switch turn
        if game['player2']:
            game['turn'] = game['player2']['id'] if player_key == 'player1' else game['player1']['id']
        
        return {
            'success': True,
            'result': 'continue',
            'game': game
        }
    
    def split_hand(self, chat_id, user_id):
        """Split player's hand if they have matching cards"""
        if chat_id not in self.games:
            return {'error': 'Game not found'}
        
        game = self.games[chat_id]
        
        if game['turn'] != user_id:
            return {'error': 'Not your turn'}
        
        # Determine player
        if game['player1']['id'] == user_id:
            player_key = 'player1'
        elif game['player2'] and game['player2']['id'] == user_id:
            player_key = 'player2'
        else:
            return {'error': 'Player not found'}
        
        player = game[player_key]
        
        # Check if split is possible
        if not can_split(player['cards']):
            return {'error': 'Cannot split - cards must be same rank'}
        
        if len(player['split_hands']) > 0:
            return {'error': 'Already split once - multiple splits not allowed'}
        
        # Perform split
        original_cards = player['cards'].copy()
        
        # Create two hands with one card each
        player['cards'] = [original_cards[0]]  # First hand keeps first card
        player['split_hands'] = [{
            'cards': [original_cards[1]],      # Second hand gets second card
            'score': 0,
            'stand': False
        }]
        
        # Deal one card to each hand
        if len(game['deck']) >= 2:
            # Deal to first hand (current main hand)
            new_card1 = game['deck'].pop()
            player['cards'].append(new_card1)
            player['score'] = calculate_score(player['cards'])
            
            # Deal to second hand (split hand)
            new_card2 = game['deck'].pop()
            player['split_hands'][0]['cards'].append(new_card2)
            player['split_hands'][0]['score'] = calculate_score(player['split_hands'][0]['cards'])
            
            # Set active hand to first hand
            player['active_hand'] = 0
            
            logger.info(f"Player {user_id} split their hand. Original: {original_cards}, "
                       f"Hand 1: {player['cards']}, Hand 2: {player['split_hands'][0]['cards']}")
            
            return {
                'success': True,
                'result': 'split',
                'game': game,
                'new_cards': [new_card1, new_card2]
            }
        else:
            return {'error': 'Not enough cards in deck'}
    
    def switch_split_hand(self, chat_id, user_id):
        """Switch to next split hand if current hand is done"""
        if chat_id not in self.games:
            return {'error': 'Game not found'}
        
        game = self.games[chat_id]
        
        if game['turn'] != user_id:
            return {'error': 'Not your turn'}
        
        # Determine player
        if game['player1']['id'] == user_id:
            player_key = 'player1'
        elif game['player2'] and game['player2']['id'] == user_id:
            player_key = 'player2'
        else:
            return {'error': 'Player not found'}
        
        player = game[player_key]
        
        if len(player['split_hands']) == 0:
            return {'error': 'No split hands to switch to'}
        
        # If currently on main hand (0), switch to split hand (1)
        if player['active_hand'] == 0:
            player['active_hand'] = 1
            return {
                'success': True,
                'result': 'switched_hand',
                'active_hand': 1,
                'game': game
            }
        else:
            # All split hands done, end turn
            player['stand'] = True
            
            # Switch turn to other player or finish game
            if game['player1']['stand'] and game['player2'] and game['player2']['stand']:
                return self._finish_game(chat_id)
            
            # Switch turn
            if game['player2']:
                game['turn'] = game['player2']['id'] if player_key == 'player1' else game['player1']['id']
            
            return {
                'success': True,
                'result': 'turn_ended',
                'game': game
            }
    
    def _evaluate_split_hands(self, chat_id, player_key, opponent_key, new_card):
        """Evaluate result when split hands are complete"""
        game = self.games[chat_id]
        player = game[player_key]
        
        # Mark player as done with split hands
        player['stand'] = True
        
        # Switch turn to other player or finish game
        if game['player1']['stand'] and game['player2'] and game['player2']['stand']:
            return self._finish_game(chat_id)
        
        # Switch turn
        if game['player2']:
            game['turn'] = game['player2']['id'] if player_key == 'player1' else game['player1']['id']
        
        return {
            'success': True,
            'result': 'split_hands_complete',
            'message': f"Обидві руки завершені. Хід переходить до суперника.",
            'game': game,
            'new_card': new_card
        }
    
    def _finish_game(self, chat_id):
        """Finish the game and determine winner"""
        game = self.games[chat_id]
        game['status'] = 'finished'
        
        score1 = game['player1']['score']
        score2 = game['player2']['score']
        
        # Determine winner
        if score1 > 21 and score2 > 21:
            result = 'draw'
            message = "Нічия! Обидва гравці перебрали."
            winner = None
            winner_id = None
        elif score1 > 21:
            result = 'player2_wins'
            message = f"{game['player2']['username']} виграв!"
            winner = game['player2']
            winner_id = game['player2']['id']
        elif score2 > 21:
            result = 'player1_wins'
            message = f"{game['player1']['username']} виграв!"
            winner = game['player1']
            winner_id = game['player1']['id']
        elif score1 > score2:
            result = 'player1_wins'
            message = f"{game['player1']['username']} виграв! ({score1} vs {score2})"
            winner = game['player1']
            winner_id = game['player1']['id']
        elif score2 > score1:
            result = 'player2_wins'
            message = f"{game['player2']['username']} виграв! ({score2} vs {score1})"
            winner = game['player2']
            winner_id = game['player2']['id']
        else:
            result = 'draw'
            message = f"Нічия! ({score1} vs {score2})"
            winner = None
            winner_id = None
        
        return {
            'success': True,
            'result': 'finished',
            'game_result': result,
            'message': message,
            'winner': winner['username'] if winner else None,
            'winner_id': winner_id,
            'game': game
        }
    
    def get_game(self, chat_id):
        """Get game state"""
        return self.games.get(chat_id)
    
    def set_game(self, chat_id, game_data):
        """Set game state (for synchronization)"""
        self.games[chat_id] = game_data
    
    def list_games(self):
        """Get all games (for debugging)"""
        return self.games
    
    def remove_game(self, chat_id):
        """Remove finished game"""
        if chat_id in self.games:
            del self.games[chat_id]
