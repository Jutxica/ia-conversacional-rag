import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { StorageService } from '../services/StorageService';

interface AppContextType {
  apiUrl: string;
  apiKey: string;
  isLogged: boolean;
  setApiConfig: (url: string, key: string) => Promise<void>;
  setLoginStatus: (status: boolean) => Promise<void>;
  isLoading: boolean;
}

const DEFAULT_API_URL = "https://dehon-ai-dehon-ai.xgaqg9.easypanel.host";
const DEFAULT_API_KEY = "e94c9ba1ba74aee889b5c5fe3e0a6521";

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [apiUrl, setApiUrl] = useState(DEFAULT_API_URL);
  const [apiKey, setApiKey] = useState(DEFAULT_API_KEY);
  const [isLogged, setIsLogged] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initApp = async () => {
      try {
        const config = await StorageService.getApiConfig();
        if (config.url) setApiUrl(config.url);
        if (config.key) setApiKey(config.key);

        const logged = await StorageService.getLoginStatus();
        setIsLogged(logged);
      } catch (e) {
        console.error("Erro ao inicializar Context", e);
      } finally {
        setIsLoading(false);
      }
    };
    initApp();
  }, []);

  const handleSetApiConfig = async (url: string, key: string) => {
    setApiUrl(url);
    setApiKey(key);
    await StorageService.saveApiConfig(url, key);
  };

  const handleSetLoginStatus = async (status: boolean) => {
    setIsLogged(status);
    await StorageService.setLoginStatus(status);
  };

  return (
    <AppContext.Provider value={{
      apiUrl,
      apiKey,
      isLogged,
      setApiConfig: handleSetApiConfig,
      setLoginStatus: handleSetLoginStatus,
      isLoading
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext deve ser usado dentro de um AppProvider');
  }
  return context;
};
