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
  gamePhase: 'setup' | 'playing' | 'round-end' | 'finished';
  winner: Player | null;
  knifeBonusActive: boolean;
  lastAction: string;
  round: number;
  maxRounds: number;
}

// Bonus icons and names
const bonusInfo = {
  magnifying: { icon: '🔍', name: 'Magnifying Glass' },
  beer: { icon: '🍺', name: 'Beer' },
  handcuffs: { icon: '⛓️', name: 'Handcuffs' },
  cigarettes: { icon: '🚬', name: 'Cigarettes' },
  knife: { icon: '🔪', name: 'Knife' }
};

const BuckshotRoulette: React.FC = () => {
  const { toast } = useToast();
  
  // Blood effect state
  const [showBloodEffect, setShowBloodEffect] = useState(false);

  // Trigger blood effect
  const triggerBloodEffect = useCallback(() => {
    setShowBloodEffect(true);
    setTimeout(() => setShowBloodEffect(false), 1000);
  }, []);
  
  // Initialize game state
  const [gameState, setGameState] = useState<GameState>(() => {
    const shellCount = Math.floor(Math.random() * 6) + 3; // 3-8 shells
    const liveCount = Math.floor(Math.random() * (shellCount - 1)) + 1; // At least 1 live
    const blankCount = shellCount - liveCount;
    
    // Create shell array
    const shells: ('live' | 'blank')[] = [
      ...Array(liveCount).fill('live'),
      ...Array(blankCount).fill('blank')
    ];
    
    // Shuffle shells
    for (let i = shells.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shells[i], shells[j]] = [shells[j], shells[i]];
    }
    
    // Generate random bonuses for each player
    const generateBonuses = (): Bonus[] => {
      const bonusTypes = ['magnifying', 'beer', 'handcuffs', 'cigarettes', 'knife'] as const;
      const bonusCount = Math.floor(Math.random() * 2) + 2; // 2-3 bonuses
      const bonuses: Bonus[] = [];
      
      for (let i = 0; i < bonusCount; i++) {
        const randomType = bonusTypes[Math.floor(Math.random() * bonusTypes.length)];
        bonuses.push({ type: randomType, used: false });
      }
      
      return bonuses;
    };
    
    return {
      players: [
        {
          id: '1',
          name: 'Player 1',
          health: 3,
          bonuses: generateBonuses(),
          isHandcuffed: false
        },
        {
          id: '2', 
          name: 'Player 2',
          health: 3,
          bonuses: generateBonuses(),
          isHandcuffed: false
        }
      ],
      currentPlayer: 0,
      shells,
      currentShell: 0,
      gamePhase: 'playing',
      winner: null,
      knifeBonusActive: false,
      lastAction: '',
      round: 1,
      maxRounds: 5
    };
  });

  // Use bonus
  const useBonus = useCallback((bonusIndex: number) => {
    const currentPlayer = gameState.players[gameState.currentPlayer];
    const bonus = currentPlayer.bonuses[bonusIndex];
    
    if (bonus.used) return;
    
    setGameState(prev => {
      const newState = { ...prev };
      const player = newState.players[newState.currentPlayer];
      
      switch (bonus.type) {
        case 'magnifying':
          const shellType = newState.shells[newState.currentShell];
          toast({
            title: "Shell Revealed",
            description: `Current shell is: ${shellType.toUpperCase()}`,
            variant: shellType === 'live' ? 'destructive' : 'default'
          });
          break;
          
        case 'beer':
          if (newState.currentShell < newState.shells.length) {
            const ejectedShell = newState.shells[newState.currentShell];
            newState.currentShell++;
            newState.lastAction = `Ejected ${ejectedShell} shell`;
            toast({
              title: "Shell Ejected",
              description: `Ejected a ${ejectedShell} shell`,
            });
          }
          break;
          
        case 'handcuffs':
          const opponent = newState.players[1 - newState.currentPlayer];
          opponent.isHandcuffed = true;
          newState.lastAction = `${opponent.name} handcuffed`;
          toast({
            title: "Handcuffs Applied",
            description: `${opponent.name} will skip their next turn`,
          });
          break;
          
        case 'cigarettes':
          if (player.health < 3) {
            player.health++;
            newState.lastAction = `${player.name} healed 1 HP`;
            toast({
              title: "Health Restored",
              description: `${player.name} gained 1 health`,
            });
          }
          break;
          
        case 'knife':
          newState.knifeBonusActive = true;
          newState.lastAction = `${player.name} sharpened the knife`;
          toast({
            title: "Knife Ready",
            description: "Next shot will deal double damage",
            variant: 'destructive'
          });
          break;
      }
      
      player.bonuses[bonusIndex].used = true;
      return newState;
    });
  }, [gameState, toast]);

  // Generate new shells for next round
  const generateNewShells = useCallback(() => {
    const baseShellCount = 3 + gameState.round; // More shells each round
    const shellCount = Math.floor(Math.random() * 4) + baseShellCount; // 3-6 first round, 4-7 second, etc.
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
  }, [gameState.round]);

  // Generate new bonuses for players
  const generateNewBonuses = useCallback(() => {
    const bonusTypes = ['magnifying', 'beer', 'handcuffs', 'cigarettes', 'knife'] as const;
    const bonusCount = Math.min(Math.floor(Math.random() * 2) + 2 + Math.floor(gameState.round / 2), 5); // More bonuses in later rounds
    const bonuses: Bonus[] = [];
    
    for (let i = 0; i < bonusCount; i++) {
      const randomType = bonusTypes[Math.floor(Math.random() * bonusTypes.length)];
      bonuses.push({ type: randomType, used: false });
    }
    
    return bonuses;
  }, [gameState.round]);

  // Start new round
  const startNewRound = useCallback(() => {
    setGameState(prev => {
      const newState = { ...prev };
      newState.round++;
      newState.shells = generateNewShells();
      newState.currentShell = 0;
      newState.gamePhase = 'playing';
      newState.knifeBonusActive = false;
      newState.lastAction = `Round ${newState.round} начался!`;
      
      // Reset handcuffs and give new bonuses
      newState.players.forEach(player => {
        player.isHandcuffed = false;
        player.bonuses = generateNewBonuses();
      });
      
      return newState;
    });
  }, [generateNewShells, generateNewBonuses]);

  // Shoot action
  const shoot = useCallback((target: 'self' | 'opponent') => {
    if (gameState.currentShell >= gameState.shells.length) {
      // No more shells - start new round if game isn't finished
      if (gameState.round < gameState.maxRounds) {
        setGameState(prev => ({ ...prev, gamePhase: 'round-end' }));
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
        setGameState(prev => ({ 
          ...prev, 
          gamePhase: 'finished',
          winner 
        }));
      }
      return;
    }
    
    const shellType = gameState.shells[gameState.currentShell];
    const damage = shellType === 'live' ? (gameState.knifeBonusActive ? 2 : 1) : 0;
    
    setGameState(prev => {
      const newState = { ...prev };
      const currentPlayer = newState.players[newState.currentPlayer];
      const targetPlayer = target === 'self' ? currentPlayer : newState.players[1 - newState.currentPlayer];
      
      // Apply damage and trigger blood effect
      if (damage > 0) {
        targetPlayer.health = Math.max(0, targetPlayer.health - damage);
        newState.lastAction = `${targetPlayer.name} took ${damage} damage (${shellType})`;
        triggerBloodEffect(); // Show blood effect
      } else {
        newState.lastAction = `${shellType} shell - no damage`;
      }
      
      // Move to next shell
      newState.currentShell++;
      newState.knifeBonusActive = false;
      
      // Check for winner
      if (targetPlayer.health <= 0) {
        newState.gamePhase = 'finished';
        newState.winner = newState.players.find(p => p.health > 0) || null;
        return newState;
      }
      
      // Check if shells are empty after this shot
      if (newState.currentShell >= newState.shells.length) {
        if (newState.round < newState.maxRounds) {
          newState.gamePhase = 'round-end';
          return newState;
        } else {
          // Final round complete - determine winner by health
          const winner = newState.players.reduce((prev, current) => 
            prev.health > current.health ? prev : current
          );
          newState.gamePhase = 'finished';
          newState.winner = winner;
          return newState;
        }
      }
      
      // Switch turns (unless shot self with blank, or target is handcuffed)
      if (target === 'opponent' || shellType === 'live') {
        const nextPlayer = 1 - newState.currentPlayer;
        const nextPlayerObj = newState.players[nextPlayer];
        
        if (nextPlayerObj.isHandcuffed) {
          nextPlayerObj.isHandcuffed = false;
          // Stay with current player
        } else {
          newState.currentPlayer = nextPlayer as 0 | 1;
        }
      }
      
      return newState;
    });
  }, [gameState, toast, startNewRound]);

  // Restart game
  const restartGame = useCallback(() => {
    window.location.reload();
  }, []);

  const currentPlayer = gameState.players[gameState.currentPlayer];
  const opponent = gameState.players[1 - gameState.currentPlayer];
  const remainingShells = gameState.shells.slice(gameState.currentShell);
  const liveCount = remainingShells.filter(s => s === 'live').length;
  const blankCount = remainingShells.filter(s => s === 'blank').length;

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
            onClick={restartGame}
            variant="danger"
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

      {/* Action Buttons */}
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
          variant="danger"
          className="py-6 md:py-8 text-base md:text-lg font-bold min-h-[80px] md:min-h-[90px]"
          disabled={gameState.currentShell >= gameState.shells.length}
        >
          🔫 SHOOT {opponent.name.toUpperCase()}
        </Button>
      </div>

      {/* Last Action */}
      {gameState.lastAction && (
        <Card className="p-3 bg-muted/90 backdrop-blur-sm border-border text-center">
          <p className="text-xs md:text-sm text-muted-foreground">{gameState.lastAction}</p>
        </Card>
      )}
    </div>
  );
};

export default BuckshotRoulette;