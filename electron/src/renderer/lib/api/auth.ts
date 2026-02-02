/**
 * Authentication API Client
 */
import api from '../apiClient';

export interface UserRegister {
  email: string;
  password: string;
  display_name: string;
  department_id?: string;
  organization_id?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface Token {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

export interface CurrentUser {
  id: string;
  email: string;
  display_name: string;
  role: string;
  department_id?: string;
  department_name?: string;
  organization_id?: string;
  avatar_url?: string;
  created_at?: string;
}

export interface RegisterResponse {
  id: string;
  email: string;
  display_name: string;
  role: string;
  message: string;
}

// Token storage keys
const ACCESS_TOKEN_KEY = 'meetmate_access_token';
const REFRESH_TOKEN_KEY = 'meetmate_refresh_token';
const USER_KEY = 'meetmate_user';

/**
 * Store tokens in localStorage
 */
export function storeTokens(tokens: Token): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  if (tokens.refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }
}

/**
 * Get access token from localStorage
 */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Get refresh token from localStorage
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Store current user in localStorage
 */
export function storeUser(user: CurrentUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Get current user from localStorage
 */
export function getStoredUser(): CurrentUser | null {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

/**
 * Clear all auth data from localStorage
 */
export function clearAuth(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

/**
 * Register a new user (legacy backend auth)
 */
export async function register(data: UserRegister): Promise<RegisterResponse> {
  return api.post<RegisterResponse>('/auth/register', data, { skipAuth: true });
}

/**
 * Login user (legacy backend auth)
 */
export async function login(data: UserLogin): Promise<Token> {
  const response = await api.post<Token>('/auth/login', data, { skipAuth: true });
  storeTokens(response);
  return response;
}

/**
 * Get current user info
 */
export async function getCurrentUser(): Promise<CurrentUser> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }
  
  const response = await api.get<CurrentUser>('/auth/me');
  storeUser(response);
  return response;
}

/**
 * Refresh access token
 */
export async function refreshTokens(): Promise<Token> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token');
  }
  
  const response = await api.post<Token>('/auth/refresh', {
    refresh_token: refreshToken
  });
  
  storeTokens(response);
  return response;
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  try {
    await api.post('/auth/logout', {});
  } catch {
    // Ignore errors on logout
  } finally {
    clearAuth();
  }
}

/**
 * Change password
 */
export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await api.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword
  });
}

/**
 * Verify token
 */
export async function verifyToken(): Promise<boolean> {
  try {
    const token = getAccessToken();
    if (!token) return false;
    
    await api.get('/auth/verify');
    return true;
  } catch {
    return false;
  }
}
