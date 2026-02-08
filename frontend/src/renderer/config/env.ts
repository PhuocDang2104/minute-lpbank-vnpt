const isDevelopment =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

const normalizeApiBase = (value: string): string => {
  const trimmed = value.trim();
  if (!trimmed) return '';
  return trimmed
    .replace(/\/+$/, '')
    .replace(/\/api\/v1$/i, '');
};

const envApiUrl = normalizeApiBase(import.meta.env.VITE_API_URL || '');
const fallbackApiUrl = isDevelopment
  ? 'http://localhost:8000'
  : 'https://minute-backend.onrender.com';

export const API_URL = envApiUrl || fallbackApiUrl;

export const WS_BASE_URL = API_URL.startsWith('https://')
  ? API_URL.replace(/^https:/i, 'wss:')
  : API_URL.startsWith('http://')
    ? API_URL.replace(/^http:/i, 'ws:')
    : API_URL;

export const USE_API = true;
export const DEBUG = isDevelopment;

export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';
