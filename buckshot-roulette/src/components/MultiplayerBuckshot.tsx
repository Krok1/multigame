import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import pokerTableBg from '@/assets/poker-table-bg.jpg';
import shotgunImg from '@/assets/shotgun.jpg';
import bloodSplatter from '@/assets/blood-splatter.png';

// Game types
interface Player {
  id: string;
  name: string;
  health: number;
  bonuses: Bonus[];
  isHandcuffed: boolean;
}

interface Bonus {
  type: 'magnifying' | 'beer' | 'handcuffs' | 'cigarettes' | 'knife';
  used: boolean;
}

interface GameState {
  players: [Player, Player];
  currentPlayer: 0 | 1;
  shells: ('live' | 'blank')[];
  currentShell: number;
  gamePhase: 'waiting' | 'playing' | 'round-end' | 'finished';
  winner: Player | null;
  knifeBonusActive: boolean;
  lastAction: string;
  round: number;
  maxRounds: number;
  mode: string;
}

interface Session {
  id: number;
  chat_id: number;
  creator_id: number;
  creator_username: string;
  player2_id: number | null;
  player2_username: string | null;
  game_mode: string;
  stake: number;
  status: string;
  game_data: string | null;
  created_at: string;
  finished_at: string | null;
  winner_id: number | null;
}

// Bonus icons and names
const bonusInfo = {
  magnifying: { icon: '🔍', name: 'Magnifying Glass' },
  beer: { icon: '🍺', name: 'Beer' },
  handcuffs: { icon: '⛓️', name: 'Handcuffs' },
  cigarettes: { icon: '🚬', name: 'Cigarettes' },
  knife: { icon: '🔪', name: 'Knife' }
};

const API_BASE_URL = 'http://localhost:5001';

const MultiplayerBuckshot: React.FC = () => {
  const { toast } = useToast();
  
  // Game state
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [currentUserId, setCurrentUserId] = useState<string>('');
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  
  // Blood effect state
  const [showBloodEffect, setShowBloodEffect] = useState(false);

  // Get URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const chatId = urlParams.get('chat_id');
  const mode = urlParams.get('mode') || 'test';

  // Trigger blood effect
  const triggerBloodEffect = useCallback(() => {
    setShowBloodEffect(true);
    setTimeout(() => setShowBloodEffect(false), 1000);
  }, []);

  // Initialize game
  useEffect(() => {
    const initGame = async () => {
      if (!chatId) {
        setError('No chat ID provided');
        setLoading(false);
        return;
      }

      try {
        // Get session and game state
        const response = await fetch(`${API_BASE_URL}/api/sessions/${chatId}`, {
          headers: {
            'bypass-tunnel-reminder': 'true'
          }
        });
        
        if (!response.ok) {
          throw new Error('Failed to load game');
        }
        
        const data = await response.json();
        
        if (data.success) {
          setSession(data.session);
          setGameState(data.game);
          
          // Determine current user ID (simplified - in real app would come from Telegram)
          const telegram = (window as any).Telegram?.WebApp;
          if (telegram?.initDataUnsafe?.user) {
            setCurrentUserId(telegram.initDataUnsafe.user.id.toString());
          } else {
            // Fallback for testing
            setCurrentUserId(data.session.creator_id.toString());
          }
        } else {
          setError(data.error || 'Failed to load game');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load game');
      } finally {
        setLoading(false);
      }
    };

    initGame();
  }, [chatId]);

  // Check if it's current user's turn
  useEffect(() => {
    if (gameState && currentUserId) {
      const currentPlayer = gameState.players[gameState.currentPlayer];
      setIsMyTurn(currentPlayer.id === currentUserId && gameState.gamePhase === 'playing');
    }
  }, [gameState, currentUserId]);

  // Poll for game updates
  useEffect(() => {
    if (!chatId || !gameState) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/sessions/${chatId}`, {
          headers: {
            'bypass-tunnel-reminder': 'true'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.game) {
            setGameState(data.game);
          }
        }
      } catch (err) {
        console.error('Failed to poll game state:', err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [chatId, gameState]);

  // Update game state on server
  const updateGameState = useCallback(async (newGameState: GameState) => {
    if (!chatId || !currentUserId) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/game/${chatId}/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'bypass-tunnel-reminder': 'true'
        },
        body: JSON.stringify({
          game: newGameState,
          user_id: currentUserId
        })
      });

      if (!response.ok) {
        console.error('Failed to update game state');
      }
    } catch (err) {
      console.error('Error updating game state:', err);
    }
  }, [chatId, currentUserId]);

  // Use bonus
  const useBonus = useCallback((bonusIndex: number) => {
    if (!gameState || !isMyTurn) return;

    const currentPlayer = gameState.players[gameState.currentPlayer];
    const bonus = currentPlayer.bonuses[bonusIndex];
    
    if (bonus.used) return;
    
    const newGameState = { ...gameState };
    const player = newGameState.players[newGameState.currentPlayer];
    
    switch (bonus.type) {
      case 'magnifying':
        const shellType = newGameState.shells[newGameState.currentShell];
        toast({
          title: "Shell Revealed",
          description: `Current shell is: ${shellType.toUpperCase()}`,
          variant: shellType === 'live' ? 'destructive' : 'default'
        });
        break;
        
      case 'beer':
        if (newGameState.currentShell < newGameState.shells.length) {
          const ejectedShell = newGameState.shells[newGameState.currentShell];
          newGameState.currentShell++;
          newGameState.lastAction = `Ejected ${ejectedShell} shell`;
          toast({
            title: "Shell Ejected",
            description: `Ejected a ${ejectedShell} shell`,
          });
        }
        break;
        
      case 'handcuffs':
        const opponent = newGameState.players[1 - newGameState.currentPlayer];
        opponent.isHandcuffed = true;
        newGameState.lastAction = `${opponent.name} handcuffed`;
        toast({
          title: "Handcuffs Applied",
          description: `${opponent.name} will skip their next turn`,
        });
        break;
        
      case 'cigarettes':
        if (player.health < 3) {
          player.health++;
          newGameState.lastAction = `${player.name} healed 1 HP`;
          toast({
            title: "Health Restored",
            description: `${player.name} gained 1 health`,
          });
        }
        break;
        
      case 'knife':
        newGameState.knifeBonusActive = true;
        newGameState.lastAction = `${player.name} sharpened the knife`;
        toast({
          title: "Knife Ready",
          description: "Next shot will deal double damage",
          variant: 'destructive'
        });
        break;
    }
    
    player.bonuses[bonusIndex].used = true;
    setGameState(newGameState);
    updateGameState(newGameState);
  }, [gameState, isMyTurn, toast, updateGameState]);

  // Generate new shells for next round
  const generateNewShells = useCallback(() => {
    if (!gameState) return [];
    
    const baseShellCount = 3 + gameState.round;
    const shellCount = Math.floor(Math.random() * 4) + baseShellCount;
    const liveCount = Math.floor(Math.random() * (shellCount - 1)) + 1;
    const blankCount = shellCount - liveCount;
    
    const shells: ('live' | 'blank')[] = [
      ...Array(liveCount).fill('live'),
      ...Array(blankCount).fill('blank')
    ];
    
    // Shuffle shells
    for (let i = shells.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shells[i], shells[j]] = [shells[j], shells[i]];
    }
    
    return shells;
  }, [gameState]);

  // Generate new bonuses for players
  const generateNewBonuses = useCallback(() => {
    if (!gameState) return [];
    
    const bonusTypes = ['magnifying', 'beer', 'handcuffs', 'cigarettes', 'knife'] as const;
    const bonusCount = Math.min(Math.floor(Math.random() * 2) + 2 + Math.floor(gameState.round / 2), 5);
    const bonuses: Bonus[] = [];
    
    for (let i = 0; i < bonusCount; i++) {
      const randomType = bonusTypes[Math.floor(Math.random() * bonusTypes.length)];
      bonuses.push({ type: randomType, used: false });
    }
    
    return bonuses;
  }, [gameState]);

  // Start new round
  const startNewRound = useCallback(() => {
    if (!gameState) return;

    const newGameState = { ...gameState };
    newGameState.round++;
    newGameState.shells = generateNewShells();
    newGameState.currentShell = 0;
    newGameState.gamePhase = 'playing';
    newGameState.knifeBonusActive = false;
    newGameState.lastAction = `Round ${newGameState.round} начался!`;
    
    // Reset handcuffs and give new bonuses
    newGameState.players.forEach(player => {
      player.isHandcuffed = false;
      player.bonuses = generateNewBonuses();
    });
    
    setGameState(newGameState);
    updateGameState(newGameState);
  }, [gameState, generateNewShells, generateNewBonuses, updateGameState]);

  // Shoot action
  const shoot = useCallback((target: 'self' | 'opponent') => {
    if (!gameState || !isMyTurn) return;

    if (gameState.currentShell >= gameState.shells.length) {
      // No more shells - start new round if game isn't finished
      if (gameState.round < gameState.maxRounds) {
        const newGameState = { ...gameState, gamePhase: 'round-end' };
        setGameState(newGameState);
        updateGameState(newGameState);
        
        toast({
          title: "Round Complete!",
          description: `Round ${gameState.round} finished. Starting Round ${gameState.round + 1}...`,
        });
        
        setTimeout(() => {
          startNewRound();
        }, 2000);
      } else {
        // Game ends - determine winner by health
        const winner = gameState.players.reduce((prev, current) => 
          prev.health > current.health ? prev : current
        );
        const newGameState = { 
          ...gameState, 
          gamePhase: 'finished',
          winner 
        };
        setGameState(newGameState);
        updateGameState(newGameState);
      }
      return;
    }
    
    const shellType = gameState.shells[gameState.currentShell];
    const damage = shellType === 'live' ? (gameState.knifeBonusActive ? 2 : 1) : 0;
    
    const newGameState = { ...gameState };
    const currentPlayer = newGameState.players[newGameState.currentPlayer];
    const targetPlayer = target === 'self' ? currentPlayer : newGameState.players[1 - newGameState.currentPlayer];
    
    // Apply damage and trigger blood effect
    if (damage > 0) {
      targetPlayer.health = Math.max(0, targetPlayer.health - damage);
      newGameState.lastAction = `${targetPlayer.name} took ${damage} damage (${shellType})`;
      triggerBloodEffect();
    } else {
      newGameState.lastAction = `${shellType} shell - no damage`;
    }
    
    // Move to next shell
    newGameState.currentShell++;
    newGameState.knifeBonusActive = false;
    
    // Check for winner
    if (targetPlayer.health <= 0) {
      newGameState.gamePhase = 'finished';
      newGameState.winner = newGameState.players.find(p => p.health > 0) || null;
      setGameState(newGameState);
      updateGameState(newGameState);
      return;
    }
    
    // Check if shells are empty after this shot
    if (newGameState.currentShell >= newGameState.shells.length) {
      if (newGameState.round < newGameState.maxRounds) {
        newGameState.gamePhase = 'round-end';
        setGameState(newGameState);
        updateGameState(newGameState);
        return;
      } else {
        // Final round complete - determine winner by health
        const winner = newGameState.players.reduce((prev, current) => 
          prev.health > current.health ? prev : current
        );
        newGameState.gamePhase = 'finished';
        newGameState.winner = winner;
        setGameState(newGameState);
        updateGameState(newGameState);
        return;
      }
    }
    
    // Switch turns (unless shot self with blank, or target is handcuffed)
    if (target === 'opponent' || shellType === 'live') {
      const nextPlayer = 1 - newGameState.currentPlayer;
      const nextPlayerObj = newGameState.players[nextPlayer];
      
      if (nextPlayerObj.isHandcuffed) {
        nextPlayerObj.isHandcuffed = false;
        // Stay with current player
      } else {
        newGameState.currentPlayer = nextPlayer as 0 | 1;
      }
    }
    
    setGameState(newGameState);
    updateGameState(newGameState);
  }, [gameState, isMyTurn, toast, startNewRound, triggerBloodEffect, updateGameState]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center p-4">
        <Card className="p-8 text-center bg-card border-border">
          <h1 className="text-2xl font-creepster text-danger mb-4">
            Loading Buckshot Roulette...
          </h1>
          <p className="text-muted-foreground">Connecting to game server...</p>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center p-4">
        <Card className="p-8 text-center bg-card border-danger">
          <h1 className="text-2xl font-creepster text-danger mb-4">
            Error
          </h1>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>
            Retry
          </Button>
        </Card>
      </div>
    );
  }

  // Waiting for player state
  if (!gameState || gameState.gamePhase === 'waiting') {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center p-4">
        <Card className="p-8 text-center bg-card border-warning">
          <h1 className="text-2xl font-creepster text-warning mb-4">
            Waiting for Player
          </h1>
          <p className="text-muted-foreground mb-4">
            Share the game link with another player to start
          </p>
          <div className="flex justify-center gap-4 mb-4">
            {gameState?.players.map((player, index) => (
              <div key={player.id} className="text-center">
                <p className="font-bold">{player.name}</p>
                <div className="flex gap-1 justify-center">
                  {Array.from({ length: 3 }, (_, i) => (
                    <span key={i} className="text-2xl">
                      {i < player.health ? '❤️' : '🖤'}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <p className="text-sm text-muted-foreground">
            Game ID: {chatId}
          </p>
        </Card>
      </div>
    );
  }

  // Game finished state
  if (gameState.gamePhase === 'finished') {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center p-4">
        <Card className="p-8 text-center bg-card border-danger animate-fade-in">
          <h1 className="text-4xl font-creepster text-danger mb-4">
            GAME OVER
          </h1>
          <p className="text-2xl mb-6">
            {gameState.winner?.name} WINS!
          </p>
          <Button 
            onClick={() => window.location.reload()}
            variant="destructive"
            size="lg"
          >
            Play Again
          </Button>
        </Card>
      </div>
    );
  }

  // Round end screen
  if (gameState.gamePhase === 'round-end') {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center p-4">
        <Card className="p-8 text-center bg-card border-warning animate-fade-in">
          <h1 className="text-3xl font-creepster text-warning mb-4">
            ROUND {gameState.round} COMPLETE
          </h1>
          <p className="text-xl mb-4">Preparing next round...</p>
          <div className="flex justify-center gap-8 mb-6">
            {gameState.players.map(player => (
              <div key={player.id} className="text-center">
                <p className="font-bold">{player.name}</p>
                <div className="flex gap-1 justify-center">
                  {Array.from({ length: 3 }, (_, i) => (
                    <span key={i} className="text-2xl">
                      {i < player.health ? '❤️' : '🖤'}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <p className="text-sm text-muted-foreground">More shells and bonuses incoming...</p>
        </Card>
      </div>
    );
  }

  const currentPlayer = gameState.players[gameState.currentPlayer];
  const opponent = gameState.players[1 - gameState.currentPlayer];
  const remainingShells = gameState.shells.slice(gameState.currentShell);
  const liveCount = remainingShells.filter(s => s === 'live').length;
  const blankCount = remainingShells.filter(s => s === 'blank').length;

  return (
    <div 
      className="min-h-screen text-foreground p-2 md:p-4 relative overflow-hidden"
      style={{
        backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), url(${pokerTableBg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundAttachment: 'fixed'
      }}
    >
      {/* Blood effect overlay */}
      {showBloodEffect && (
        <div 
          className="fixed inset-0 pointer-events-none z-50 animate-fade-in"
          style={{
            backgroundImage: `url(${bloodSplatter})`,
            backgroundSize: '200px 200px',
            backgroundRepeat: 'repeat',
            opacity: 0.7,
            animation: 'blood-drip 1s ease-out'
          }}
        />
      )}
      
      {/* Header */}
      <div className="text-center mb-4 md:mb-6">
        <h1 className="text-2xl md:text-4xl font-creepster text-danger mb-2 animate-pulse-glow">
          BUCKSHOT ROULETTE
        </h1>
        <div className="flex justify-center items-center gap-2 md:gap-4 mb-2 text-sm md:text-base">
          <span className="text-warning font-bold">Round {gameState.round}/{gameState.maxRounds}</span>
          <span className="text-muted-foreground">•</span>
          <span className="text-muted-foreground">{currentPlayer.name}'s Turn</span>
          {!isMyTurn && (
            <>
              <span className="text-muted-foreground">•</span>
              <span className="text-muted-foreground">Waiting for opponent...</span>
            </>
          )}
        </div>
      </div>

      {/* Shotgun centerpiece */}
      <div className="flex justify-center mb-4 md:mb-6">
        <div className="relative">
          <img 
            src={shotgunImg} 
            alt="Shotgun" 
            className="w-32 md:w-48 h-auto opacity-90 drop-shadow-2xl"
            style={{
              filter: 'brightness(0.8) contrast(1.2)'
            }}
          />
          {gameState.knifeBonusActive && (
            <div className="absolute -top-2 -right-2 text-danger text-2xl animate-pulse-glow">
              🔪
            </div>
          )}
        </div>
      </div>

      {/* Shell Info */}
      <Card className="mb-4 md:mb-6 p-3 md:p-4 bg-card/90 backdrop-blur-sm border-border">
        <div className="text-center">
          <h3 className="text-base md:text-lg font-bold mb-2">Shells Remaining</h3>
          <div className="flex justify-center gap-4 text-sm md:text-base">
            <span className="text-danger font-bold">🔴 {liveCount} Live</span>
            <span className="text-muted-foreground">⚪ {blankCount} Blank</span>
          </div>
        </div>
      </Card>

      {/* Players Health */}
      <div className="grid grid-cols-2 gap-2 md:gap-4 mb-4 md:mb-6">
        {gameState.players.map((player, index) => (
          <Card 
            key={player.id} 
            className={`p-3 md:p-4 bg-card/90 backdrop-blur-sm ${index === gameState.currentPlayer ? 'border-danger animate-pulse-glow' : 'border-border'}`}
          >
            <h3 className="text-sm md:text-lg font-bold text-center mb-2">
              {player.name}
              {player.isHandcuffed && ' 🔒'}
              {player.id === currentUserId && ' (You)'}
            </h3>
            <div className="flex justify-center gap-1">
              {Array.from({ length: 3 }, (_, i) => (
                <span key={i} className="text-xl md:text-2xl">
                  {i < player.health ? '❤️' : '🖤'}
                </span>
              ))}
            </div>
          </Card>
        ))}
      </div>

      {/* Current Player Bonuses */}
      {isMyTurn && (
        <Card className="mb-4 md:mb-6 p-3 md:p-4 bg-card/90 backdrop-blur-sm border-border">
          <h3 className="text-base md:text-lg font-bold mb-3">Your Items</h3>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
            {currentPlayer.bonuses.map((bonus, index) => (
              <Button
                key={index}
                onClick={() => useBonus(index)}
                disabled={bonus.used}
                variant={bonus.used ? "secondary" : "default"}
                className={`p-2 md:p-3 min-h-[60px] md:min-h-[70px] flex flex-col items-center gap-1 ${!bonus.used ? 'hover:shadow-glow border-warning' : ''}`}
                size="sm"
              >
                <span className="text-lg md:text-xl">{bonusInfo[bonus.type].icon}</span>
                <span className="text-xs leading-tight text-center">{bonusInfo[bonus.type].name}</span>
              </Button>
            ))}
          </div>
        </Card>
      )}

      {/* Action Buttons */}
      {isMyTurn && (
        <div className="grid grid-cols-2 gap-2 md:gap-4 mb-4">
          <Button
            onClick={() => shoot('self')}
            variant="warning"
            className="py-6 md:py-8 text-base md:text-lg font-bold min-h-[80px] md:min-h-[90px]"
            disabled={gameState.currentShell >= gameState.shells.length}
          >
            🔫 SHOOT SELF
          </Button>
          <Button
            onClick={() => shoot('opponent')}
            variant="destructive"
            className="py-6 md:py-8 text-base md:text-lg font-bold min-h-[80px] md:min-h-[90px]"
            disabled={gameState.currentShell >= gameState.shells.length}
          >
            🔫 SHOOT {opponent.name.toUpperCase()}
          </Button>
        </div>
      )}

      {/* Last Action */}
      {gameState.lastAction && (
        <Card className="p-3 bg-muted/90 backdrop-blur-sm border-border text-center">
          <p className="text-xs md:text-sm text-muted-foreground">{gameState.lastAction}</p>
        </Card>
      )}
    </div>
  );
};

export default MultiplayerBuckshot; 