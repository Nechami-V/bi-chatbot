// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

export const API_ENDPOINTS = {
  // Auth endpoints
  LOGIN: '/auth/login',
  ME: '/auth/me',
  LOGOUT: '/auth/logout',
  
  // Chat endpoints
  ASK: '/ask',
  
  // System endpoints
  HEALTH: '/health',
  SCHEMA: '/schema',
  SYNC_TRANSLATIONS: '/sync-translations',
} as const;

// Request timeout in milliseconds
export const API_TIMEOUT = 30000;

// Default headers (empty - let each request specify its Content-Type)
export const DEFAULT_HEADERS: Record<string, string> = {
};
