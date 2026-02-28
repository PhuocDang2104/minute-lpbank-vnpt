import type { LlmProvider } from './dto/user'

export type LlmModelOption = { value: string; label: string }

export const CHAT_MODEL_OPTIONS: Record<LlmProvider, LlmModelOption[]> = {
  gemini: [
    { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite' },
    { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
    { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
    { value: 'gemini-1.5-flash-8b', label: 'Gemini 1.5 Flash 8B' },
  ],
  groq: [
    { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B Versatile' },
    { value: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B Instant' },
    { value: 'meta-llama/llama-4-scout-17b-16e-instruct', label: 'Llama 4 Scout 17B (Groq)' },
    { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B 32K' },
  ],
}

export const VISION_MODEL_OPTIONS: Record<LlmProvider, LlmModelOption[]> = {
  gemini: [
    { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite (Vision)' },
    { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash (Vision)' },
    { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro (Vision)' },
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash (Vision)' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro (Vision)' },
  ],
  groq: [
    { value: 'meta-llama/llama-4-scout-17b-16e-instruct', label: 'Llama 4 Scout 17B (Vision)' },
    { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B Versatile (Vision)' },
  ],
}

export const getDefaultChatModel = (provider: LlmProvider): string =>
  CHAT_MODEL_OPTIONS[provider]?.[0]?.value || ''

export const getDefaultVisionModel = (provider: LlmProvider): string =>
  VISION_MODEL_OPTIONS[provider]?.[0]?.value || ''
