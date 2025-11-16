import { API_BASE_URL, API_ENDPOINTS, DEFAULT_HEADERS, API_TIMEOUT } from '../config';

// Types matching the backend API
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_info: {
    id: number;
    email: string;
    full_name?: string;
  };
  permissions: Record<string, any>;
}

export interface AskRequest {
  question: string;
}

export interface AskResponse {
  question: string;
  answer: string;
  sql?: string;
  data?: any[];
  error?: string;
  total_time_ms?: number;
  timings_ms?: Record<string, number>;
  visualization?: {
    chart_type: 'line' | 'bar' | 'pie' | 'metric' | 'scatter';
    title: string;
    label_field: string;
    value_field: string;
    labels: string[];
    values: number[];
  };
}

export interface UserInfo {
  id: number;
  username: string;
  email?: string;
}

// Token storage
const TOKEN_KEY = 'bi_chatbot_token';

export const setToken = (token: string) => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

export const clearToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

// API Error class
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Base fetch wrapper with timeout and auth
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout = API_TIMEOUT
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const token = getToken();
    
    console.log('fetchWithTimeout called:', { url, hasToken: !!token });
    
    // Merge headers properly - don't override, merge
    const headers: Record<string, string> = {
      ...DEFAULT_HEADERS,
      ...(options.headers as Record<string, string> || {}),
    };

    // Add auth token if available (but not for login endpoint)
    if (token && !url.includes('/auth/login')) {
      console.log('Adding Authorization header with token');
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response;
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error?.name === 'AbortError') {
      throw new APIError('Request timeout - server took too long to respond');
    }
    // Re-throw the original error
    throw error;
  }
}

// Handle API response
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    let errorData;

    try {
      errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // Response is not JSON
    }

    throw new APIError(errorMessage, response.status, errorData);
  }

  return response.json();
}

// API Methods

/**
 * Login to the system
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
  const url = `${API_BASE_URL}${API_ENDPOINTS.LOGIN}`;
  
  // Send JSON with email instead of username
  const requestBody = {
    email,
    password
  };

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

  const data = await handleResponse<LoginResponse>(response);
  
  console.log('Login response:', data);
  
  // Store token
  if (data.access_token) {
    console.log('Storing token:', data.access_token.substring(0, 20) + '...');
    setToken(data.access_token);
  } else {
    console.error('No access_token in response:', data);
  }

  return data;
}

/**
 * Get current user info
 */
export async function getCurrentUser(): Promise<UserInfo> {
  const url = `${API_BASE_URL}${API_ENDPOINTS.ME}`;
  const response = await fetchWithTimeout(url, { method: 'GET' });
  return handleResponse<UserInfo>(response);
}

/**
 * Logout (client-side token clearing)
 */
export async function logout(): Promise<void> {
  clearToken();
}

/**
 * Ask a question to the chatbot
 */
export async function askQuestion(question: string): Promise<AskResponse> {
  const url = `${API_BASE_URL}${API_ENDPOINTS.ASK}`;
  
  const requestBody: AskRequest = { question };

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

  return handleResponse<AskResponse>(response);
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; version: string }> {
  const url = `${API_BASE_URL}${API_ENDPOINTS.HEALTH}`;
  const response = await fetchWithTimeout(url, { method: 'GET' });
  return handleResponse(response);
}

/**
 * Get database schema info
 */
export async function getSchema(): Promise<any> {
  const url = `${API_BASE_URL}${API_ENDPOINTS.SCHEMA}`;
  const response = await fetchWithTimeout(url, { method: 'GET' });
  return handleResponse(response);
}

/**
 * Export data to Excel or CSV
 */
export async function exportData(
  question: string,
  format: 'excel' | 'csv' = 'excel'
): Promise<Blob> {
  const url = `${API_BASE_URL}${API_ENDPOINTS.EXPORT}?format=${format}`;
  
  const requestBody = { question };

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // Response is not JSON
    }
    throw new APIError(errorMessage, response.status);
  }

  // Return the blob directly for file download
  return response.blob();
}
