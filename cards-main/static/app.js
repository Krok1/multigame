// Telegram WebApp initialization
let tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
    tg.expand();
    tg.ready();
}

// Get data from Telegram
let initData = tg ? tg.initDataUnsafe : {};
let chatId = null;
let userId = initData.user?.id;
let username = initData.user?.username || initData.user?.first_name || 'Гравець';

// Try to get chat_id from various sources
if (initData.chat?.id) {
    chatId = initData.chat.id;
} else if (initData.start_param) {
    const params = initData.start_param.split('_');
    if (params.length >= 2) {
        chatId = parseInt(params[1]);
    }
} else if (tg && tg.initData) {
    const urlParams = new URLSearchParams(tg.initData);
    const startParam = urlParams.get('start_param');
    if (startParam) {
        const params = startParam.split('_');
        if (params.length >= 2) {
            chatId = parseInt(params[1]);
        }
    }
}

// If still no chat_id, try from URL
if (!chatId) {
    const urlParams = new URLSearchParams(window.location.search);
    const chatParam = urlParams.get('chat_id');
    if (chatParam) {
        chatId = parseInt(chatParam);
    }
}

console.log('Init data:', initData);
console.log('Chat ID:', chatId, 'User ID:', userId, 'Username:', username);

// Game state
let gameState = null;
let isMyTurn = false;
let gameUpdateInterval = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    if (chatId) {
        // First check if game already exists
        checkExistingGame();
    } else {
        // Show demo mode for browser testing
        showDemoMode();
    }
});

// Check if game already exists before showing stake input
async function checkExistingGame() {
    try {
        const response = await fetch(`/api/game/${chatId}`);
        const data = await response.json();
        
        if (data.success && data.game) {
            // Game exists, check if user is part of it
            const game = data.game;
            const isPlayer1 = game.player1 && game.player1.id == userId;
            const isPlayer2 = game.player2 && game.player2.id == userId;
            
            if (isPlayer1 || isPlayer2) {
                // User is already in the game, start playing
                gameState = game;
                updateGameDisplay();
                gameUpdateInterval = setInterval(fetchGame, 3000);
                return;
            } else if (!game.player2) {
                // Game exists but needs second player, try to join
                await tryJoinExistingGame();
                return;
            } else {
                // Game is full, show error
                showError('Гра вже заповнена двома гравцями');
                return;
            }
        }
        
        // No game exists, show stake input for creating new game
        showStakeInput();
        
    } catch (error) {
        console.error('Error checking existing game:', error);
        // If error checking, show stake input as fallback
        showStakeInput();
    }
}

// Try to join existing game automatically
async function tryJoinExistingGame() {
    try {
        const response = await fetch(`/api/sessions/${chatId}/join`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                username: username
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Successfully joined, start game
            gameState = data.game;
            updateGameDisplay();
            gameUpdateInterval = setInterval(fetchGame, 3000);
            showMessage('Ви успішно приєдналися до гри!', 'success');
        } else {
            showError(data.error || 'Не вдалося приєднатися до гри');
        }
        
    } catch (error) {
        console.error('Error joining existing game:', error);
        showError('Помилка приєднання до гри');
    }
}

// Show stake input before starting game
function showStakeInput() {
    document.getElementById('gameInfo').innerHTML = 'Введіть ставку для нової гри:';
    document.getElementById('gameContent').innerHTML = `
        <div class="stake-input-container">
            <input id="stakeInput" type="number" min="1" max="100000" value="10" class="stake-input" placeholder="Ставка (монети)">
            <button class="btn btn-primary" onclick="startGameWithStake()">Стартувати гру</button>
        </div>
    `;
}

async function startGameWithStake() {
    const stake = parseFloat(document.getElementById('stakeInput').value) || 10;
    // Create session via API
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                username: username,
                mode: 'test',
                chat_id: chatId,
                stake: stake
            })
        });
        const data = await response.json();
        if (data.success) {
            fetchGame();
            gameUpdateInterval = setInterval(fetchGame, 3000);
        } else {
            showError(data.error || 'Помилка створення гри');
        }
    } catch (error) {
        showError('Помилка створення гри');
    }
}

// Main functions
async function fetchGame() {
    if (!chatId) {
        showError('Помилка: не вдалося отримати ID чату');
        return;
    }

    try {
        const response = await fetch(`/api/game/${chatId}`);
        const data = await response.json();
        
        if (data.error) {
            showError(data.message || data.error);
            return;
        }
        
        gameState = data.game;
        updateGameDisplay();
    } catch (error) {
        console.error('Fetch error:', error);
        showError('Помилка завантаження гри');
    }
}

async function hit() {
    if (!isMyTurn) return;
    
    try {
        const response = await fetch(`/api/hit/${chatId}/${userId}`, { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        gameState = data.game;
        updateGameDisplay();
        
        if (data.result === 'bust') {
            showMessage(data.message, 'error');
            if (tg) tg.showAlert(data.message);
        } else if (data.result === 'finished') {
            showMessage(data.message, 'success');
            if (tg) tg.showAlert(data.message);
            clearInterval(gameUpdateInterval);
        }
    } catch (error) {
        console.error('Hit error:', error);
        showError('Помилка при взятті карти');
    }
}

async function stand() {
    if (!isMyTurn) return;
    
    try {
        const response = await fetch(`/api/stand/${chatId}/${userId}`, { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        gameState = data.game;
        updateGameDisplay();
        
        if (data.result === 'finished') {
            showMessage(data.message, 'success');
            if (tg) tg.showAlert(data.message);
            clearInterval(gameUpdateInterval);
        }
    } catch (error) {
        console.error('Stand error:', error);
        showError('Помилка при зупинці');
    }
}

function updateGameDisplay() {
    if (!gameState) return;

    const { player1, player2, turn, status, stake } = gameState;
    
    // Determine who I am
    const isPlayer1 = player1.id == userId;
    const myPlayer = isPlayer1 ? player1 : player2;
    const opponent = isPlayer1 ? player2 : player1;
    
    isMyTurn = (turn == userId) && (status === 'playing');

    // Update game info
    if (myPlayer) {
        const modeText = myPlayer.mode === 'test' ? 'Тестовий режим' : 'Режим на гроші';
        const currency = myPlayer.mode === 'test' ? 'монет' : 'TON';
        document.getElementById('gameInfo').innerHTML = `${modeText} • Ставка: ${stake} ${currency}`;
    }

    // Create game HTML
    let gameHTML = '';

    if (!player2) {
        gameHTML = `
            <div class="status-message warning">
                ⏳ Очікуємо другого гравця...
            </div>
        `;
    } else if (!myPlayer) {
        gameHTML = `
            <div class="status-message error">
                ❌ Ви не є учасником цієї гри
            </div>
        `;
    } else {
        const myCards = renderPlayerCards(myPlayer);
        const opponentCards = renderPlayerCards(opponent);
        
        gameHTML = `
            <div class="game-meta">
                <div class="stakes">Ставка: <span class="stakes-amount">${gameState.stake} ${gameState.player1.mode === 'test' ? 'монет' : 'TON'}</span></div>
                <div class="turn-indicator">${isMyTurn ? 'Ваш хід' : 'Хід суперника'}</div>
            </div>
            
            <div class="players-container">
                <div class="player-section ${isMyTurn ? 'current-turn' : ''} ${status === 'finished' && getWinner() === myPlayer.username ? 'winner' : ''}">
                    <div class="player-header">
                        <div class="player-name">👤 ${myPlayer.username} (Ви)</div>
                        <div class="player-score ${myPlayer.score > 21 ? 'bust' : myPlayer.score === 21 ? 'blackjack' : ''}">
                            ${myPlayer.score}
                        </div>
                    </div>
                    ${myCards}
                </div>
                
                <div class="player-section ${!isMyTurn && status === 'playing' ? 'current-turn' : ''} ${status === 'finished' && getWinner() === opponent.username ? 'winner' : ''}">
                    <div class="player-header">
                        <div class="player-name">👤 ${opponent.username}</div>
                        <div class="player-score ${opponent.score > 21 ? 'bust' : opponent.score === 21 ? 'blackjack' : ''}">
                            ${opponent.score}
                        </div>
                    </div>
                    ${opponentCards}
                </div>
            </div>
            
            <div class="status-message ${getStatusClass()}">
                ${getStatusMessage()}
            </div>
            
            <div class="controls">
                ${renderControls()}
            </div>
        `;
    }

    document.getElementById('gameContent').innerHTML = gameHTML;
}

function renderCards(cards) {
    if (!cards || cards.length === 0) return '';
    
    return cards.map(card => {
        const suit = card.slice(-1);
        const value = card.slice(0, -1);
        const suitClass = (suit === '♥' || suit === '♦') ? 'red' : 'black';
        return `<div class="card ${suitClass}">${value}${suit}</div>`;
    }).join('');
}

function renderPlayerCards(player) {
    if (!player) return '';
    
    let cardsHTML = '';
    
    // Check if player has split hands
    if (player.split_hands && player.split_hands.length > 0) {
        cardsHTML = `
            <div class="split-hands">
                <div class="split-hand ${player.active_hand === 0 ? 'active' : ''}">
                    <div class="split-hand-label">Рука 1</div>
                    <div class="cards">${renderCards(player.cards)}</div>
                    <div class="cards-container">Очки: ${player.score}</div>
                </div>
                <div class="split-hand ${player.active_hand === 1 ? 'active' : ''}">
                    <div class="split-hand-label">Рука 2</div>
                    <div class="cards">${renderCards(player.split_hands[0].cards)}</div>
                    <div class="cards-container">Очки: ${player.split_hands[0].score}</div>
                </div>
            </div>
        `;
    } else {
        // Normal single hand
        cardsHTML = `
            <div class="cards-container">
                <div class="cards">${renderCards(player.cards)}</div>
            </div>
        `;
    }
    
    return cardsHTML;
}

function renderControls() {
    if (gameState.status !== 'playing') {
        // Show rematch and end buttons if game finished
        return `
            <div class="control-row">
                <button class="btn btn-primary" onclick="requestRematch()">
                    ♻️ Реванш
                </button>
                <button class="btn btn-secondary" onclick="endGame()">
                    ❌ Кінець
                </button>
            </div>
        `;
    }

// Rematch logic
let rematchRequested = false;
let waitingRematch = false;

async function requestRematch() {
    if (!chatId || !userId) return;
    rematchRequested = true;
    showMessage('Очікуємо відповідь суперника на реванш...', 'info');
    try {
        const response = await fetch(`/api/rematch/request/${chatId}/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        await response.json();
        // Poll for rematch status
        pollRematchStatus();
    } catch (error) {
        showMessage('Помилка запиту реваншу', 'error');
    }
}

async function pollRematchStatus() {
    // Poll game state every 2s to check if rematch started or declined
    waitingRematch = true;
    const poll = async () => {
        if (!waitingRematch) return;
        try {
            const response = await fetch(`/api/game/${chatId}`);
            const data = await response.json();
            if (data && data.game && data.game.status === 'playing' && 
                data.game.player1 && data.game.player2 && 
                data.game.player1.cards.length <= 2 && data.game.player2.cards.length <= 2) {
                // New game started (both players have fresh cards)
                waitingRematch = false;
                gameState = data.game;
                updateGameDisplay();
                showMessage('Реванш почався!', 'success');
                gameUpdateInterval = setInterval(fetchGame, 3000);
                return;
            }
        } catch {}
        setTimeout(poll, 2000);
    };
    poll();
}

async function endGame() {
    try {
        // Clear any intervals
        if (gameUpdateInterval) {
            clearInterval(gameUpdateInterval);
            gameUpdateInterval = null;
        }
        
        // Clear rematch requests
        rematchRequested = false;
        waitingRematch = false;
        
        // Show final message
        showMessage('Гра завершена. Дякуємо за гру!', 'info');
        
        // Hide controls
        const controlsElement = document.querySelector('.controls');
        if (controlsElement) {
            controlsElement.innerHTML = `
                <div class="control-row">
                    <button class="btn btn-primary" onclick="location.reload()">
                        🔄 Нова гра
                    </button>
                </div>
            `;
        }
        
        // Close Telegram WebApp if available
        if (tg && tg.close) {
            setTimeout(() => {
                tg.close();
            }, 2000);
        }
        
    } catch (error) {
        console.error('End game error:', error);
        showMessage('Гра завершена', 'info');
    }
}

// Listen for rematch requests from opponent (polling in fetchGame)
let lastRematchPrompt = false;
function updateGameDisplay() {
    // ...existing code...

    // Rematch prompt logic
    if (gameState.status === 'finished' && !rematchRequested && !lastRematchPrompt) {
        // Check if opponent requested rematch (simulate by checking a flag or add custom logic if needed)
        // For now, just show prompt if game finished and not requested
        // In production, you may want to add a rematch_requests state to backend/gameState
        // and check if opponent requested
        // Example prompt:
        // showRematchPrompt();
    }
}

function showRematchPrompt() {
    if (lastRematchPrompt) return;
    lastRematchPrompt = true;
    const promptDiv = document.createElement('div');
    promptDiv.className = 'status-message info temporary-message';
    promptDiv.innerHTML = `Суперник хоче реванш!<br><button class="btn btn-primary" onclick="acceptRematch()">✅ Прийняти</button> <button class="btn btn-secondary" onclick="declineRematch()">❌ Відмовитись</button>`;
    document.getElementById('gameContent').prepend(promptDiv);
}

async function acceptRematch() {
    try {
        const response = await fetch(`/api/rematch/accept/${chatId}/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        
        if (data.error) {
            showMessage(data.error, 'error');
            return;
        }
        
        if (data.rematch && data.game) {
            // Rematch started immediately
            gameState = data.game;
            updateGameDisplay();
            showMessage('Реванш почався!', 'success');
            // Start polling for game updates
            gameUpdateInterval = setInterval(fetchGame, 3000);
        } else if (data.success && !data.rematch) {
            // Waiting for other player
            showMessage('Очікуємо відповідь суперника...', 'info');
            pollRematchStatus();
        } else {
            showMessage('Помилка при прийнятті реваншу', 'error');
        }
    } catch (error) {
        console.error('Accept rematch error:', error);
        showMessage('Помилка при прийнятті реваншу', 'error');
    }
}

async function declineRematch() {
    try {
        await fetch(`/api/rematch/decline/${chatId}/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        showMessage('Ви відмовились від реваншу. Гра завершена.', 'info');
        document.querySelector('.controls').innerHTML = '';
    } catch (error) {
        showMessage('Помилка при відмові від реваншу', 'error');
    }
}

    if (isMyTurn) {
        const myPlayer = gameState.player1.id == userId ? gameState.player1 : gameState.player2;
        const canSplit = myPlayer && myPlayer.cards && myPlayer.cards.length === 2 && 
                        myPlayer.cards[0].slice(0, -1) === myPlayer.cards[1].slice(0, -1) &&
                        (!myPlayer.split_hands || myPlayer.split_hands.length === 0);
        
        return `
            <div class="control-row">
                <button class="btn btn-primary" onclick="hit()">
                    🃏 Взяти карту
                </button>
                <button class="btn btn-secondary" onclick="stand()">
                    ✋ Пас
                </button>
                ${canSplit ? `<button class="btn btn-success" onclick="splitHand()">✂️ Спліт</button>` : ''}
            </div>
        `;
    } else {
        return `
            <div class="game-status">
                <div class="status-text">⏳ Очікуйте хід суперника...</div>
            </div>
        `;
    }
}

function getStatusMessage() {
    if (!gameState.player2) {
        return '⏳ Очікуємо другого гравця...';
    }

    if (gameState.status === 'finished') {
        const winner = getWinner();
        if (winner) {
            return `🏆 ${winner} виграв гру!`;
        } else {
            return '🤝 Нічия!';
        }
    }

    if (isMyTurn) {
        return '🎯 Ваш хід! Виберіть дію.';
    } else {
        const opponentName = gameState.player1.id == userId ? gameState.player2.username : gameState.player1.username;
        return `⏳ Хід гравця ${opponentName}...`;
    }
}

function getStatusClass() {
    if (gameState.status === 'finished') {
        const winner = getWinner();
        const myPlayer = gameState.player1.id == userId ? gameState.player1 : gameState.player2;
        if (winner === myPlayer.username) {
            return 'success';
        } else if (winner) {
            return 'error';
        } else {
            return 'warning';
        }
    }
    return '';
}

function getWinner() {
    if (!gameState || !gameState.player2) return null;
    
    const score1 = gameState.player1.score;
    const score2 = gameState.player2.score;
    
    if (score1 > 21 && score2 > 21) return null;
    if (score1 > 21) return gameState.player2.username;
    if (score2 > 21) return gameState.player1.username;
    if (score1 > score2) return gameState.player1.username;
    if (score2 > score1) return gameState.player2.username;
    return null;
}

function showError(message) {
    document.getElementById('gameContent').innerHTML = `
        <div class="status-message error">
            ❌ ${message}
        </div>
        <div class="controls">
            <button class="btn" onclick="location.reload()">
                🔄 Перезавантажити
            </button>
        </div>
    `;
}

function showMessage(message, type = 'success') {
    const existingMessage = document.querySelector('.temporary-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `status-message ${type} temporary-message`;
    messageDiv.innerHTML = message;
    
    const gameContent = document.getElementById('gameContent');
    gameContent.insertBefore(messageDiv, gameContent.firstChild);
    
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

// Handle page visibility changes to pause/resume updates
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        if (gameUpdateInterval) {
            clearInterval(gameUpdateInterval);
        }
    } else {
        if (chatId && gameState && gameState.status === 'playing') {
            fetchGame();
            gameUpdateInterval = setInterval(fetchGame, 3000);
        }
    }
});

// Handle page unload
window.addEventListener('beforeunload', function() {
    if (gameUpdateInterval) {
        clearInterval(gameUpdateInterval);
    }
});

// Demo mode for browser testing
function showDemoMode() {
    document.getElementById('gameInfo').innerHTML = 'Демо режим - тестування без Telegram';
    
    document.getElementById('gameContent').innerHTML = `
        <div class="status-message warning">
            <h3>🔧 Демо режим</h3>
            <p>Цей додаток призначений для роботи в Telegram WebApp.</p>
            <p>Для тестування у браузері оберіть одну з опцій:</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="createDemoGame()">
                🎮 Створити тестову гру
            </button>
            <button class="btn btn-secondary" onclick="showGameInfo()">
                ℹ️ Інформація про гру
            </button>
        </div>
    `;
}

// Create demo game for testing
function createDemoGame() {
    // Set demo values
    chatId = 12345; // Demo chat ID
    userId = 67890; // Demo user ID
    username = 'Тестовий гравець';
    
    // Create demo game via API
    fetch('/api/create-demo-game', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            chat_id: chatId,
            user_id: userId,
            username: username
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Start fetching game state
            fetchGame();
            gameUpdateInterval = setInterval(fetchGame, 3000);
        } else {
            showError(data.error || 'Помилка створення демо гри');
        }
    })
    .catch(error => {
        console.error('Demo game creation error:', error);
        showError('Помилка створення демо гри');
    });
}

// Show game information
function showGameInfo() {
    document.getElementById('gameContent').innerHTML = `
        <div class="status-message">
            <h3>🃏 BlackJack Telegram WebApp</h3>
            <p><strong>Особливості:</strong></p>
            <ul style="text-align: left; margin: 20px 0;">
                <li>Багатокористувацька гра на двох гравців</li>
                <li>Інтеграція з Telegram ботом</li>
                <li>Віртуальна валюта для ставок</li>
                <li>Реальний час оновлення стану гри</li>
                <li>Адаптивний дизайн для мобільних пристроїв</li>
            </ul>
            <p><strong>Правила BlackJack:</strong></p>
            <ul style="text-align: left; margin: 20px 0;">
                <li>Мета: набрати 21 очко або ближче до 21</li>
                <li>Карти 2-10: номінальна вартість</li>
                <li>J, Q, K: 10 очок</li>
                <li>A: 11 або 1 очко (автоматично)</li>
                <li>Більше 21 = програш</li>
            </ul>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="createDemoGame()">
                🎮 Спробувати демо
            </button>
            <button class="btn btn-secondary" onclick="showDemoMode()">
                🔙 Назад
            </button>
        </div>
    `;
}

// Split hand function
async function splitHand() {
    if (!isMyTurn || !chatId || !userId) {
        showMessage('Не можна розділити руку зараз', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/game/${chatId}/split`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showMessage(data.error, 'error');
            return;
        }
        
        if (data.success) {
            showMessage('Рука розділена! Грайте першою рукою.', 'success');
            // Update game state
            gameState = data.game;
            displayGame();
        }
        
    } catch (error) {
        console.error('Split error:', error);
        showMessage('Помилка розділення руки', 'error');
    }
}

// Switch split hand function (automatically called when needed)
async function switchSplitHand() {
    if (!chatId || !userId) return;
    
    try {
        const response = await fetch(`/api/game/${chatId}/switch-hand`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            gameState = data.game;
            displayGame();
            
            if (data.result === 'switched_hand') {
                showMessage('Переключення на другу руку', 'success');
            }
        }
        
    } catch (error) {
        console.error('Switch hand error:', error);
    }
}
