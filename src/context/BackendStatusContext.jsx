// Backend status context to track connectivity to Python FastAPI backend
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { checkBackendHealth, API_BASE_URL } from '../services/api';

const BackendStatusContext = createContext();

export function BackendStatusProvider({ children }) {
  const [isOnline, setIsOnline] = useState(false);
  const [latencyMs, setLatencyMs] = useState(null);
  const [checking, setChecking] = useState(true);
  const [lastChecked, setLastChecked] = useState(null);

  const checkStatus = useCallback(async () => {
    setChecking(true);
    const result = await checkBackendHealth();
    setIsOnline(result.isOnline);
    setLatencyMs(result.latencyMs);
    setChecking(false);
    setLastChecked(new Date());
  }, []);

  useEffect(() => {
    checkStatus();
    // Re-check periodically every 25 seconds
    const interval = setInterval(checkStatus, 25000);
    return () => clearInterval(interval);
  }, [checkStatus]);

  return (
    <BackendStatusContext.Provider
      value={{
        isOnline,
        latencyMs,
        checking,
        lastChecked,
        apiBaseUrl: API_BASE_URL,
        refreshStatus: checkStatus
      }}
    >
      {children}
    </BackendStatusContext.Provider>
  );
}

export function useBackendStatus() {
  const context = useContext(BackendStatusContext);
  if (!context) {
    throw new Error('useBackendStatus must be used within BackendStatusProvider');
  }
  return context;
}
