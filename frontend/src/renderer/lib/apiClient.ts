// ============================================
// API CLIENT
// HTTP client for backend communication
// ============================================

import { API_URL } from '../config/env';

const API_BASE_URL = API_URL;
const API_PREFIX = '/api/v1';
const ACCESS_TOKEN_KEY = 'minute_access_token';
const REFRESH_TOKEN_KEY = 'minute_refresh_token';
const USER_STORAGE_KEY = 'minute_user';

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  skipAuth?: boolean; // Skip adding Authorization header
}

/**
 * Get access token from localStorage
 */
function getAccessToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function storeTokens(accessToken: string, refreshToken?: string): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

function clearStoredAuth(): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

interface RefreshResponse {
  access_token: string;
  refresh_token?: string;
}

async function tryRefreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  try {
    const refreshResponse = await fetch(`${API_BASE_URL}${API_PREFIX}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!refreshResponse.ok) {
      clearStoredAuth();
      return null;
    }

    const tokens = (await refreshResponse.json()) as RefreshResponse;
    if (!tokens.access_token) {
      clearStoredAuth();
      return null;
    }

    storeTokens(tokens.access_token, tokens.refresh_token);
    return tokens.access_token;
  } catch {
    clearStoredAuth();
    return null;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { params, skipAuth, ...init } = options;

  // Build URL with query params
  let url = `${API_BASE_URL}${API_PREFIX}${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  // Build headers with auth token
  const isFormData = init.body instanceof FormData;
  const headers: HeadersInit = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...init.headers,
  };

  // Add Authorization header if token exists and not skipped
  if (!skipAuth) {
    const token = getAccessToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, {
    ...init,
    headers,
  });

  const canAttemptRefresh =
    response.status === 401 &&
    !skipAuth &&
    !endpoint.includes('/auth/login') &&
    !endpoint.includes('/auth/refresh') &&
    !endpoint.includes('/auth/google');

  if (canAttemptRefresh) {
    const newAccessToken = await tryRefreshAccessToken();
    if (newAccessToken) {
      const retryHeaders = new Headers(headers);
      retryHeaders.set('Authorization', `Bearer ${newAccessToken}`);
      const retryResponse = await fetch(url, {
        ...init,
        headers: retryHeaders,
      });

      if (!retryResponse.ok) {
        let retryData;
        try {
          retryData = await retryResponse.json();
        } catch {
          retryData = null;
        }
        throw new ApiError(retryResponse.status, retryResponse.statusText, retryData);
      }

      if (retryResponse.status === 204) {
        return null as T;
      }
      return retryResponse.json();
    }
  }

  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    throw new ApiError(response.status, response.statusText, data);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

// HTTP methods
export const api = {
  get: <T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>) =>
    request<T>(endpoint, { method: 'GET', params }),

  post: <T>(endpoint: string, data?: unknown, options?: { skipAuth?: boolean }) =>
    request<T>(endpoint, {
      method: 'POST',
      body: data instanceof FormData ? data : data ? JSON.stringify(data) : undefined,
      skipAuth: options?.skipAuth,
    }),

  put: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: 'PUT',
      body: data instanceof FormData ? data : data ? JSON.stringify(data) : undefined,
    }),

  patch: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: 'PATCH',
      body: data instanceof FormData ? data : data ? JSON.stringify(data) : undefined,
    }),

  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: 'DELETE' }),
};

// Alias for backward compatibility
export const apiClient = api;

export default api;
