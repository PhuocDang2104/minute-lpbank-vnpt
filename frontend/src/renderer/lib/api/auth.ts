import api, { ApiError } from '../apiClient';
import type { User } from '../../shared/dto/user';

const ACCESS_TOKEN_KEY = 'minute_access_token';
const REFRESH_TOKEN_KEY = 'minute_refresh_token';
const USER_STORAGE_KEY = 'minute_user';
const SETTINGS_STORAGE_KEY = 'minute_settings';

export type CurrentUser = User;

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserRegister {
  email: string;
  password: string;
  display_name: string;
  department_id?: string;
  organization_id?: string;
}

export interface AuthTokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

export interface VerifyResponse {
  valid: boolean;
  user_id: string;
  email?: string | null;
  role?: string | null;
}

export interface AuthMessage {
  message: string;
}

export interface RegisterResponse {
  id: string;
  email: string;
  display_name: string;
  role?: string;
  is_active?: boolean;
}

export interface GoogleLoginPayload {
  id_token: string;
}

export function getAccessToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getStoredUser(): CurrentUser | null {
  if (typeof localStorage === 'undefined') return null;
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as CurrentUser;
  } catch {
    return null;
  }
}

function storeTokens(tokens: AuthTokenResponse): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  if (tokens.refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }
}

export function storeUser(user: CurrentUser): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

// Backward-compatible alias
export const setStoredUser = storeUser;

export function clearAuth(): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

export async function register(payload: UserRegister): Promise<void> {
  await api.post('/auth/register', payload, { skipAuth: true });
}

export async function login(payload: UserLogin): Promise<AuthTokenResponse> {
  const token = await api.post<AuthTokenResponse>('/auth/login', payload, { skipAuth: true });
  storeTokens(token);
  return token;
}

export async function loginWithGoogle(payload: GoogleLoginPayload): Promise<AuthTokenResponse> {
  const token = await api.post<AuthTokenResponse>('/auth/google', payload, { skipAuth: true });
  storeTokens(token);
  return token;
}

export async function refreshAccessToken(refreshToken?: string): Promise<AuthTokenResponse> {
  const tokenToUse = refreshToken || getRefreshToken();
  if (!tokenToUse) {
    throw new ApiError(401, 'Unauthorized');
  }
  const token = await api.post<AuthTokenResponse>(
    '/auth/refresh',
    { refresh_token: tokenToUse },
    { skipAuth: true },
  );
  storeTokens(token);
  return token;
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const user = await api.get<CurrentUser>('/auth/me');
  storeUser(user);
  return user;
}

export async function verifyToken(): Promise<VerifyResponse> {
  return api.get<VerifyResponse>('/auth/verify');
}

export async function logout(): Promise<void> {
  try {
    if (getAccessToken()) {
      await api.post<AuthMessage>('/auth/logout');
    }
  } finally {
    clearAuth();
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(SETTINGS_STORAGE_KEY);
    }
  }
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<AuthMessage> {
  return api.post<AuthMessage>('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

export default {
  getStoredUser,
  setStoredUser,
  getAccessToken,
  getRefreshToken,
  clearAuth,
  storeUser,
  register,
  login,
  loginWithGoogle,
  refreshAccessToken,
  getCurrentUser,
  verifyToken,
  logout,
  changePassword,
};
