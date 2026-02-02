// ============================================
// ENVIRONMENT CONFIG
// ============================================
// Thay đổi giá trị này để kết nối với API server

// API Server URL
// - Local development: 'http://localhost:8000'
// - Production (Render): 'https://vnpt-ai-hackathon-meetmate.onrender.com'

// Toggle between local and production
const IS_PRODUCTION = true;

export const API_URL = IS_PRODUCTION 
  ? 'https://vnpt-ai-hackathon-meetmate.onrender.com'
  : 'http://localhost:8000';

// Bật/tắt kết nối API (false = dùng mock data)
// Set false để demo với mock data khi backend chưa sẵn sàng
export const USE_API = true;

// Debug mode
export const DEBUG = !IS_PRODUCTION;

// Supabase Auth (điền giá trị thật qua env Vite khi build)
export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';
