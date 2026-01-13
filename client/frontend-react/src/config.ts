// API configuration shared across the React app

const runtimeOrigin = typeof window !== 'undefined' ? window.location.origin : undefined;

// Guess the backend host when running the UI on a dev port (e.g. Vite 3000) without VITE_API_BASE_URL.
const inferredBackendOrigin = (() => {
  if (!runtimeOrigin || runtimeOrigin === 'null') {
    return 'http://localhost:8000';
  }

  try {
    const url = new URL(runtimeOrigin);
    const hostname = url.hostname;
    const port = url.port;

    // If we already run on the backend port, use it as-is.
    if (port === '8000') {
      return runtimeOrigin;
    }

    const isLocalHost = ['localhost', '127.0.0.1', '0.0.0.0'].includes(hostname);
    const isTypicalVitePort = ['3000', '5173', '4173'].includes(port);

    if (isLocalHost && (!port || isTypicalVitePort)) {
      return `${url.protocol}//${hostname}:8000`;
    }

    if (isTypicalVitePort) {
      return `${url.protocol}//${hostname}:8000`;
    }

    return runtimeOrigin;
  } catch (err) {
    console.warn('Failed to infer backend origin from runtimeOrigin', err);
    return 'http://localhost:8000';
  }
})();

const fallbackOrigin = inferredBackendOrigin || 'http://localhost:8000';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || fallbackOrigin).replace(/\/$/, '');

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
export const API_TIMEOUT = 500000;

// Default headers (empty - let each request specify its Content-Type)
export const DEFAULT_HEADERS: Record<string, string> = {
};
