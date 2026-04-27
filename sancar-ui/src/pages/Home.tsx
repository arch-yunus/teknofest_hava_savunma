import { useEffect } from 'react';
import { useLocation } from 'wouter';
import CommandCenter from './CommandCenter';

export default function Home() {
  const [, setLocation] = useLocation();

  // Komuta kontrol merkezine yönlendir
  useEffect(() => {
    setLocation('/command-center');
  }, [setLocation]);

  return <CommandCenter />;
}
