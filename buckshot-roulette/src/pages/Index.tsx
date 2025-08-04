import { useEffect, useState } from 'react';
import BuckshotRoulette from '@/components/BuckshotRoulette';
import MultiplayerBuckshot from '@/components/MultiplayerBuckshot';

const Index = () => {
  const [isMultiplayer, setIsMultiplayer] = useState(false);
  
  useEffect(() => {
    // Check if we have chat_id parameter (multiplayer mode)
    const urlParams = new URLSearchParams(window.location.search);
    const chatId = urlParams.get('chat_id');
    setIsMultiplayer(!!chatId);
  }, []);

  if (isMultiplayer) {
    return <MultiplayerBuckshot />;
  }

  return <BuckshotRoulette />;
};

export default Index;
