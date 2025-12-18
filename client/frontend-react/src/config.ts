// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Development mode: disable authentication (matches server DISABLE_AUTH flag)
export const DISABLE_AUTH = import.meta.env.VITE_DISABLE_AUTH === 'true';

export const API_ENDPOINTS = {
  // Auth endpoints
  LOGIN: '/auth/login',
  ME: '/auth/me',
  LOGOUT: '/auth/logout',
  
  // Chat endpoints
  ASK: '/ask',
  EXPORT: '/export',
  
  // System endpoints
  HEALTH: '/health',
  SCHEMA: '/schema',
  SYNC_TRANSLATIONS: '/sync-translations',
} as const;

// Request timeout in milliseconds (3 minutes for complex queries)
export const API_TIMEOUT = 180000;

// Default headers (empty - let each request specify its Content-Type)
export const DEFAULT_HEADERS: Record<string, string> = {
};
