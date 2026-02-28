import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowUp,
  BookOpenCheck,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock,
  Eye,
  EyeOff,
  KeyRound,
  RefreshCw,
  SlidersHorizontal,
  Sparkles,
  Video,
  X,
} from 'lucide-react'
import aiApi from '../../lib/api/ai'
import { useCalendarMeetings, type NormalizedMeeting } from '../../services/meeting'
import { useLocaleText } from '../../i18n/useLocaleText'
import { currentUser } from '../../store/mockData'
import { getStoredUser } from '../../lib/api/auth'
import { usersApi } from '../../lib/api/users'
import type { LlmProvider } from '../../shared/dto/user'

type UserRole = 'admin' | 'PMO' | 'chair' | 'user'

interface VideoSuggestion {
  title: string
  description: string
  url: string
  roles: UserRole[]
}

type LlmModelOption = { value: string; label: string }

const VIDEO_SUGGESTIONS: VideoSuggestion[] = [
  {
    title: 'Project Management in 8 Minutes',
    description: 'How to run planning, execution, and reporting with high clarity.',
    url: 'https://www.youtube.com/watch?v=9LSX2WJH7A8',
    roles: ['PMO', 'admin', 'chair'],
  },
  {
    title: 'How to Run Effective Meetings',
    description: 'Practical frameworks to reduce wasted meeting time.',
    url: 'https://www.youtube.com/watch?v=8S0FDjFBj8o',
    roles: ['PMO', 'chair', 'user'],
  },
  {
    title: 'Decision-Making for Leaders',
    description: 'Better decision quality in complex, cross-functional teams.',
    url: 'https://www.youtube.com/watch?v=R9xFQ2q6aTY',
    roles: ['chair', 'admin', 'PMO'],
  },
  {
    title: 'Risk Management Explained',
    description: 'A fast guide to identifying and controlling delivery risk.',
    url: 'https://www.youtube.com/watch?v=8An2SxNFvmU',
    roles: ['admin', 'PMO', 'chair', 'user'],
  },
  {
    title: 'Business Communication Tips',
    description: 'Communicate updates and blockers with confidence.',
    url: 'https://www.youtube.com/watch?v=HAnw168huqA',
    roles: ['user', 'PMO', 'chair'],
  },
  {
    title: 'Strategic Leadership Skills',
    description: 'Leading teams with strategy, alignment, and accountability.',
    url: 'https://www.youtube.com/watch?v=wL4N7iW47Mc',
    roles: ['admin', 'chair'],
  },
  {
    title: 'Time Management Fundamentals',
    description: 'Prioritization methods to finish high-value tasks first.',
    url: 'https://www.youtube.com/watch?v=oTugjssqOT0',
    roles: ['user', 'PMO', 'admin'],
  },
]

const MODEL_OPTIONS: Record<LlmProvider, LlmModelOption[]> = {
  gemini: [
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
    { value: 'gemini-1.5-flash-8b', label: 'Gemini 1.5 Flash 8B' },
  ],
  groq: [
    { value: 'meta-llama/llama-4-scout-17b-16e-instruct', label: 'Llama 4 Scout 17B (Groq)' },
    { value: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B Instant' },
    { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B Versatile' },
    { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B 32K' },
  ],
}


const getDayKey = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const toStartOfDay = (date: Date) => new Date(date.getFullYear(), date.getMonth(), date.getDate())

const getMonthGrid = (date: Date) => {
  const year = date.getFullYear()
  const month = date.getMonth()
  const firstOfMonth = new Date(year, month, 1)
  const firstWeekday = (firstOfMonth.getDay() + 6) % 7
  const gridStart = new Date(year, month, 1 - firstWeekday)

  return Array.from({ length: 42 }).map((_, idx) => {
    const nextDate = new Date(gridStart)
    nextDate.setDate(gridStart.getDate() + idx)
    return {
      date: nextDate,
      isCurrentMonth: nextDate.getMonth() === month,
    }
  })
}

const getYoutubeVideoId = (url: string) => {
  try {
    const parsed = new URL(url)
    if (parsed.hostname.includes('youtu.be')) {
      return parsed.pathname.replace('/', '')
    }
    if (parsed.pathname.startsWith('/shorts/')) {
      return parsed.pathname.split('/')[2] || null
    }
    return parsed.searchParams.get('v')
  } catch {
    return null
  }
}

const getYoutubeThumbnail = (url: string) => {
  const id = getYoutubeVideoId(url)
  return id ? `https://img.youtube.com/vi/${id}/hqdefault.jpg` : null
}

const getDisplayName = (fullName: string) => {
  const trimmed = fullName.trim()
  if (!trimmed) return 'there'
  const parts = trimmed.split(/\s+/)
  return parts.length > 1 ? parts.slice(-2).join(' ') : parts[0]
}

const Dashboard = () => {
  const { lt, dateLocale, language } = useLocaleText()
  const storedUser = getStoredUser()
  const displayUser = storedUser || currentUser
  const activeUserId = String(displayUser.id || '').trim()
  const userRoleRaw = String(displayUser.role || 'user') as UserRole
  const userRole: UserRole = ['admin', 'PMO', 'chair', 'user'].includes(userRoleRaw) ? userRoleRaw : 'user'
  const userDisplayName =
    ('display_name' in displayUser ? displayUser.display_name : undefined) ||
    ('displayName' in displayUser ? displayUser.displayName : undefined) ||
    'Minute User'

  const [askValue, setAskValue] = useState('')
  const [askResponse, setAskResponse] = useState<string | null>(null)
  const [askError, setAskError] = useState<string | null>(null)
  const [askLoading, setAskLoading] = useState(false)
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [advancedProvider, setAdvancedProvider] = useState<LlmProvider>('gemini')
  const [advancedModel, setAdvancedModel] = useState<string>(MODEL_OPTIONS.gemini[0]?.value || '')
  const [advancedApiKeyInput, setAdvancedApiKeyInput] = useState('')
  const [advancedApiKeySet, setAdvancedApiKeySet] = useState(false)
  const [advancedApiKeyLast4, setAdvancedApiKeyLast4] = useState<string | null>(null)
  const [advancedShowApiKey, setAdvancedShowApiKey] = useState(false)
  const [advancedClearApiKey, setAdvancedClearApiKey] = useState(false)
  const [advancedLoading, setAdvancedLoading] = useState(false)
  const [advancedSaving, setAdvancedSaving] = useState(false)
  const [advancedError, setAdvancedError] = useState<string | null>(null)
  const [advancedNotice, setAdvancedNotice] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState(() => new Date())

  const [viewMonth, setViewMonth] = useState(() => new Date())
  const [selectedDate, setSelectedDate] = useState(() => toStartOfDay(new Date()))
  const calendarMonthStart = useMemo(
    () => new Date(viewMonth.getFullYear(), viewMonth.getMonth(), 1),
    [viewMonth],
  )
  const calendarMonthEnd = useMemo(
    () => new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 0, 23, 59, 59),
    [viewMonth],
  )
  const { data: monthMeetings, isLoading: meetingsLoading, error: meetingsError, refetch } =
    useCalendarMeetings(calendarMonthStart, calendarMonthEnd)

  const meetingsByDay = useMemo(() => {
    const source = monthMeetings || []
    return source.reduce<Map<string, NormalizedMeeting[]>>((acc, item) => {
      const key = item.date && /^\d{4}-\d{2}-\d{2}$/.test(item.date)
        ? item.date
        : getDayKey(item.startTime)
      if (!acc.has(key)) {
        acc.set(key, [])
      }
      acc.get(key)?.push(item)
      return acc
    }, new Map())
  }, [monthMeetings])

  const selectedDayMeetings = useMemo(() => {
    const key = getDayKey(selectedDate)
    return (meetingsByDay.get(key) || []).sort((a, b) => a.startTime.getTime() - b.startTime.getTime())
  }, [meetingsByDay, selectedDate])

  const monthGrid = useMemo(() => getMonthGrid(viewMonth), [viewMonth])
  const monthTitle = calendarMonthStart.toLocaleDateString(dateLocale, { month: 'long', year: 'numeric' })
  const todayKey = getDayKey(new Date())
  const selectedKey = getDayKey(selectedDate)

  const videosForRole = useMemo(() => {
    const scoped = VIDEO_SUGGESTIONS.filter(item => item.roles.includes(userRole))
    return scoped.length > 0 ? scoped : VIDEO_SUGGESTIONS.slice(0, 5)
  }, [userRole])

  const carouselRef = useRef<HTMLDivElement | null>(null)
  const askInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    const timer = window.setInterval(() => setCurrentTime(new Date()), 60_000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    if (!advancedOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setAdvancedOpen(false)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [advancedOpen])

  useEffect(() => {
    if (!advancedOpen) return
    let isActive = true

    const loadAdvancedSettings = async () => {
      if (!activeUserId) {
        setAdvancedError(lt('Không tìm thấy người dùng hiện tại để tải cấu hình.', 'Cannot resolve current user to load settings.'))
        return
      }

      setAdvancedLoading(true)
      setAdvancedError(null)
      setAdvancedNotice(null)

      try {
        const response = await usersApi.getLlmSettings(activeUserId)
        if (!isActive) return
        const provider: LlmProvider = response.provider === 'groq' ? 'groq' : 'gemini'
        const options = MODEL_OPTIONS[provider]
        const fallbackModel = options[0]?.value || ''
        const nextModel = options.some(item => item.value === response.model) ? response.model : fallbackModel
        setAdvancedProvider(provider)
        setAdvancedModel(nextModel)
        setAdvancedApiKeyInput('')
        setAdvancedApiKeySet(Boolean(response.api_key_set))
        setAdvancedApiKeyLast4(response.api_key_last4 || null)
        setAdvancedShowApiKey(false)
        setAdvancedClearApiKey(false)
      } catch {
        if (!isActive) return
        setAdvancedError(lt('Không thể tải cấu hình model. Vui lòng thử lại.', 'Unable to load model settings. Please try again.'))
      } finally {
        if (isActive) {
          setAdvancedLoading(false)
        }
      }
    }

    loadAdvancedSettings()
    return () => {
      isActive = false
    }
  }, [activeUserId, advancedOpen, lt])

  const greetingMessage = useMemo(() => {
    const hour = currentTime.getHours()
    const name = getDisplayName(userDisplayName)
    if (hour >= 5 && hour < 12) {
      return lt(
        'Chúc bạn buổi sáng làm việc hiệu quả, ' + name + '.',
        'Hope your morning\'s going well, ' + name + '.',
      )
    }
    if (hour >= 12 && hour < 17) {
      return lt(
        'Chúc bạn buổi chiều làm việc suôn sẻ, ' + name + '.',
        'Hope your afternoon\'s going well, ' + name + '.',
      )
    }
    if (hour >= 17 && hour < 22) {
      return lt(
        'Chúc bạn buổi tối làm việc nhẹ nhàng, ' + name + '.',
        'Hope your evening\'s going well, ' + name + '.',
      )
    }
    return lt(
      'Chúc bạn làm việc tập trung vào đêm nay, ' + name + '.',
      'Hope your night is productive, ' + name + '.',
    )
  }, [currentTime, lt, userDisplayName])

  const shiftCarousel = (direction: 'left' | 'right') => {
    const node = carouselRef.current
    if (!node) return
    const step = node.clientWidth * 0.85
    node.scrollBy({
      left: direction === 'left' ? -step : step,
      behavior: 'smooth',
    })
  }

  const jumpToToday = () => {
    const today = new Date()
    setViewMonth(today)
    setSelectedDate(toStartOfDay(today))
  }

  const moveMonth = (offset: number) => {
    const next = new Date(viewMonth)
    next.setMonth(viewMonth.getMonth() + offset)
    setViewMonth(next)
  }

  const handleAsk = async () => {
    const question = askValue.trim()
    if (!question || askLoading) return

    setAskLoading(true)
    setAskError(null)
    setAskResponse(null)
    try {
      const result = await aiApi.homeAsk(question)
      setAskResponse(result.message)
      setAskValue('')
    } catch {
      setAskError(lt('Không thể kết nối AI lúc này. Vui lòng thử lại.', 'Unable to connect to AI right now. Please try again.'))
    } finally {
      setAskLoading(false)
    }
  }

  const handleAskAdvanced = () => {
    setAdvancedOpen(true)
  }

  const handleProviderChange = (nextProvider: LlmProvider) => {
    setAdvancedProvider(nextProvider)
    const options = MODEL_OPTIONS[nextProvider]
    setAdvancedModel(options[0]?.value || '')
  }

  const advancedApiKeyBadge = useMemo(() => {
    if (advancedLoading) {
      return {
        label: lt('Đang tải...', 'Loading...'),
        color: '#5f4a2b',
        bg: 'rgba(248, 229, 194, 0.35)',
        border: 'rgba(145, 101, 31, 0.24)',
      }
    }
    if (advancedApiKeyInput.trim().length > 0) {
      return {
        label: lt('Sẽ cập nhật khi lưu', 'Will update on save'),
        color: '#1f2937',
        bg: '#f3f4f6',
        border: '#d1d5db',
      }
    }
    if (advancedClearApiKey) {
      return {
        label: lt('Sẽ xoá khi lưu', 'Will remove on save'),
        color: '#b42318',
        bg: 'rgba(254, 226, 226, 0.7)',
        border: 'rgba(239, 68, 68, 0.28)',
      }
    }
    if (advancedApiKeySet) {
      const suffix = advancedApiKeyLast4 ? `•••• ${advancedApiKeyLast4}` : lt('Đã lưu', 'Saved')
      return {
        label: suffix,
        color: '#065f46',
        bg: 'rgba(209, 250, 229, 0.6)',
        border: 'rgba(16, 185, 129, 0.3)',
      }
    }
    return {
      label: lt('Chưa thiết lập', 'Not set'),
      color: '#6b7280',
      bg: '#f9fafb',
      border: '#e5e7eb',
    }
  }, [advancedApiKeyInput, advancedApiKeyLast4, advancedApiKeySet, advancedClearApiKey, advancedLoading, lt])

  const handleSaveAdvanced = async () => {
    if (!activeUserId || advancedSaving) return

    setAdvancedSaving(true)
    setAdvancedError(null)
    setAdvancedNotice(null)

    try {
      const payload: {
        provider: LlmProvider
        model: string
        api_key?: string
        clear_api_key?: boolean
      } = {
        provider: advancedProvider,
        model: advancedModel,
      }
      const trimmedApiKey = advancedApiKeyInput.trim()
      if (advancedClearApiKey) {
        payload.clear_api_key = true
      } else if (trimmedApiKey) {
        payload.api_key = trimmedApiKey
      }
      const result = await usersApi.updateLlmSettings(activeUserId, payload)
      const provider: LlmProvider = result.provider === 'groq' ? 'groq' : 'gemini'
      const options = MODEL_OPTIONS[provider]
      const fallbackModel = options[0]?.value || ''
      const nextModel = options.some(item => item.value === result.model) ? result.model : fallbackModel
      setAdvancedProvider(provider)
      setAdvancedModel(nextModel)
      setAdvancedApiKeyInput('')
      setAdvancedApiKeySet(Boolean(result.api_key_set))
      setAdvancedApiKeyLast4(result.api_key_last4 || null)
      setAdvancedShowApiKey(false)
      setAdvancedClearApiKey(false)
      setAdvancedNotice(lt('Đã lưu cấu hình model và API key cho Ask AI.', 'Ask AI model and API key settings saved.'))
    } catch {
      setAdvancedError(lt('Không thể lưu cấu hình model. Vui lòng thử lại.', 'Unable to save model settings. Please try again.'))
    } finally {
      setAdvancedSaving(false)
    }
  }

  return (
    <div className="home-hub">
      <header className="home-hub__header">
        <h1>Home</h1>
      </header>


      <section className="home-hub-ai">
        <h2 className="home-hub-ai__greeting">{greetingMessage}</h2>

        <div className={`home-hub-ai__shell ${askLoading ? 'is-loading' : ''}`}>
          <input
            ref={askInputRef}
            className="home-hub-ai__input"
            value={askValue}
            onChange={event => setAskValue(event.target.value)}
            placeholder={lt(
              'Hỏi MINUTE bất kỳ điều gì về meeting, training course và project của bạn...',
              'Ask MINUTE anything about your meetings, training courses, and projects...',
            )}
            onKeyDown={event => {
              if (event.key === 'Enter') {
                event.preventDefault()
                handleAsk()
              }
            }}
            disabled={askLoading}
          />

          <div className="home-hub-ai__footer">
            <div className="home-hub-ai__spark">
              <Sparkles size={18} />
            </div>

            <div className="home-hub-ai__actions">
              <button
                type="button"
                className="home-hub-ai__advanced"
                onClick={handleAskAdvanced}
              >
                <SlidersHorizontal size={16} />
                {lt('Nâng cao', 'Advanced')}
              </button>

              <button
                type="button"
                className="home-hub-ai__send"
                onClick={handleAsk}
                disabled={askLoading || !askValue.trim()}
                title={askLoading ? lt('Đang gửi', 'Sending') : lt('Gửi yêu cầu', 'Send request')}
              >
                <ArrowUp size={18} />
              </button>
            </div>
          </div>
        </div>

        {(askResponse || askError) && (
          <div className={`home-hub-ai__response ${askError ? 'home-hub-ai__response--error' : ''}`}>
            <span className="home-hub-ai__response-label">Minute AI</span>
            <p>{askError || askResponse}</p>
          </div>
        )}
      </section>

      {advancedOpen && (
        <div className="modal-overlay" onClick={() => setAdvancedOpen(false)}>
          <div className="modal home-hub-ai-modal" onClick={event => event.stopPropagation()}>
            <div className="modal__header">
              <h3 className="modal__title">{lt('Cài đặt Ask AI', 'Ask AI settings')}</h3>
              <button type="button" className="modal__close" onClick={() => setAdvancedOpen(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="modal__body home-hub-ai-modal__body">
              <p className="home-hub-ai-modal__hint">
                {lt(
                  'Chọn provider/model mặc định cho Ask AI. Cấu hình này dùng chung với trang Settings.',
                  'Choose default provider/model for Ask AI. This uses the same setting as the Settings page.',
                )}
              </p>

              {advancedLoading ? (
                <div className="home-hub-ai-modal__status">
                  <div className="spinner" style={{ width: 20, height: 20 }} />
                  <span>{lt('Đang tải cấu hình model...', 'Loading model settings...')}</span>
                </div>
              ) : (
                <>
                  <div className="form-group">
                    <label className="form-label">{lt('Nhà cung cấp', 'Provider')}</label>
                    <select
                      className="form-select"
                      value={advancedProvider}
                      onChange={event => handleProviderChange(event.target.value as LlmProvider)}
                      disabled={advancedSaving}
                    >
                      <option value="gemini">Gemini</option>
                      <option value="groq">Groq</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">{lt('Model', 'Model')}</label>
                    <select
                      className="form-select"
                      value={advancedModel}
                      onChange={event => setAdvancedModel(event.target.value)}
                      disabled={advancedSaving}
                    >
                      {(MODEL_OPTIONS[advancedProvider] || []).map(item => (
                        <option key={item.value} value={item.value}>
                          {item.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">{lt('LLM API key của riêng bạn', 'Your LLM API key')}</label>
                    <div className="home-hub-ai-modal__key-row">
                      <input
                        className="form-input"
                        type={advancedShowApiKey ? 'text' : 'password'}
                        value={advancedApiKeyInput}
                        onChange={event => {
                          setAdvancedApiKeyInput(event.target.value)
                          setAdvancedClearApiKey(false)
                        }}
                        placeholder={lt('Nhập API key', 'Enter API key')}
                        disabled={advancedSaving}
                      />
                      <div className="home-hub-ai-modal__key-actions">
                        <button
                          type="button"
                          className="home-hub-ai-modal__key-btn"
                          onClick={() => setAdvancedShowApiKey(prev => !prev)}
                          disabled={advancedSaving}
                          title={advancedShowApiKey ? lt('Ẩn key', 'Hide key') : lt('Hiện key', 'Show key')}
                        >
                          {advancedShowApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>
                        <button
                          type="button"
                          className="home-hub-ai-modal__key-btn"
                          onClick={() => {
                            setAdvancedClearApiKey(true)
                            setAdvancedApiKeyInput('')
                          }}
                          disabled={advancedSaving || !advancedApiKeySet}
                        >
                          {lt('Xoá key', 'Remove key')}
                        </button>
                      </div>
                    </div>
                    <span
                      className="home-hub-ai-modal__key-badge"
                      style={{
                        color: advancedApiKeyBadge.color,
                        background: advancedApiKeyBadge.bg,
                        borderColor: advancedApiKeyBadge.border,
                      }}
                    >
                      {advancedApiKeyBadge.label}
                    </span>
                    <p className="home-hub-ai-modal__key-note">
                      <KeyRound size={14} />
                      {lt(
                        'API key được mã hoá và chỉ lưu trên server.',
                        'API key is encrypted and stored only on the server.',
                      )}
                    </p>
                  </div>
                </>
              )}

              {advancedError && <div className="home-hub-ai-modal__error">{advancedError}</div>}
              {advancedNotice && <div className="home-hub-ai-modal__success">{advancedNotice}</div>}

              <Link to="/app/settings" className="home-hub-ai-modal__link" onClick={() => setAdvancedOpen(false)}>
                {lt('Mở trang Settings đầy đủ', 'Open full Settings page')}
              </Link>
            </div>

            <div className="modal__footer home-hub-ai-modal__footer">
              <button
                type="button"
                className="home-hub-ai-modal__btn home-hub-ai-modal__btn--ghost"
                onClick={() => setAdvancedOpen(false)}
              >
                {lt('Đóng', 'Close')}
              </button>
              <button
                type="button"
                className="home-hub-ai-modal__btn home-hub-ai-modal__btn--primary"
                onClick={handleSaveAdvanced}
                disabled={advancedLoading || advancedSaving}
              >
                {advancedSaving ? lt('Đang lưu...', 'Saving...') : lt('Lưu và áp dụng', 'Save & apply')}
              </button>
            </div>
          </div>
        </div>
      )}

      <section className="home-hub-calendar">
        <div className="home-hub-calendar__header">
          <div className="home-hub-calendar__title">
            <CalendarDays size={18} />
            <h2>{lt('Session Calendar', 'Session Calendar')}</h2>
          </div>
          <div className="home-hub-calendar__actions">
            <button type="button" className="home-hub-calendar__icon-btn" onClick={() => moveMonth(-1)}>
              <ChevronLeft size={16} />
            </button>
            <div className="home-hub-calendar__month-label">{monthTitle}</div>
            <button type="button" className="home-hub-calendar__icon-btn" onClick={() => moveMonth(1)}>
              <ChevronRight size={16} />
            </button>
            <button type="button" className="home-hub-calendar__text-btn" onClick={jumpToToday}>
              {lt('Hôm nay', 'Today')}
            </button>
            <button type="button" className="home-hub-calendar__icon-btn" onClick={refetch} title={lt('Làm mới', 'Refresh')}>
              <RefreshCw size={16} className={meetingsLoading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        <div className="home-hub-calendar__body">
          <div className="home-hub-calendar__month-grid">
            <div className="home-hub-calendar__weekdays">
              {(language === 'vi'
                ? ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
                : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']).map(day => (
                <span key={day}>{day}</span>
              ))}
            </div>
            <div className="home-hub-calendar__days">
              {monthGrid.map(({ date, isCurrentMonth }) => {
                const dayKey = getDayKey(date)
                const count = meetingsByDay.get(dayKey)?.length || 0
                const dayMeetings = meetingsByDay.get(dayKey) || []
                return (
                  <button
                    key={dayKey}
                    type="button"
                    className={`home-hub-calendar__day ${isCurrentMonth ? '' : 'is-outside'} ${dayKey === todayKey ? 'is-today' : ''} ${dayKey === selectedKey ? 'is-selected' : ''}`}
                    onClick={() => setSelectedDate(toStartOfDay(date))}
                  >
                    <div className="home-hub-calendar__day-number">{date.getDate()}</div>
                    <div className="home-hub-calendar__day-events">
                      {dayMeetings.slice(0, 2).map(meeting => (
                        <span key={meeting.id}>
                          {meeting.start || lt('Cả ngày', 'All day')} · {meeting.title}
                        </span>
                      ))}
                      {count > 2 && <span>+{count - 2}</span>}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          <aside className="home-hub-calendar__agenda">
            <h3>
              {selectedDate.toLocaleDateString(dateLocale, {
                weekday: 'long',
                day: '2-digit',
                month: 'long',
                year: 'numeric',
              })}
            </h3>

            {meetingsError && (
              <div className="home-hub-calendar__error">
                {lt('Không thể tải session từ hệ thống. Đang hiển thị dữ liệu fallback.', 'Unable to load sessions from API. Showing fallback data.')}
              </div>
            )}

            {meetingsLoading ? (
              <div className="home-hub-calendar__loading">
                <div className="spinner" style={{ width: 24, height: 24 }} />
                <span>{lt('Đang tải session...', 'Loading sessions...')}</span>
              </div>
            ) : selectedDayMeetings.length === 0 ? (
              <div className="home-hub-calendar__empty">
                {lt('Không có session nào trong ngày này.', 'No sessions on this day.')}
              </div>
            ) : (
              <ul className="home-hub-calendar__agenda-list">
                {selectedDayMeetings.map(meeting => (
                  <li key={meeting.id}>
                    <Link to={`/app/meetings/${meeting.id}/detail`}>
                      <div className="home-hub-calendar__agenda-time">
                        <Clock size={13} />
                        <span>{meeting.start && meeting.end ? `${meeting.start} - ${meeting.end}` : lt('Chưa lên lịch', 'Unscheduled')}</span>
                      </div>
                      <strong>{meeting.title}</strong>
                      <small>{meeting.location || lt('Online', 'Online')}</small>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </aside>
        </div>
      </section>

      <section className="home-hub-videos">
        <header className="home-hub-videos__header">
          <div>
            <h2>
              <BookOpenCheck size={18} />
              {lt('Role-aligned training picks', 'Role-aligned training picks')}
            </h2>
            <p>
              {lt(
                'Commercial-grade learning playlists tailored to your role for stronger daily execution.',
                'Commercial-grade learning playlists tailored to your role for stronger daily execution.',
              )}
            </p>
          </div>
          <div className="home-hub-videos__controls">
            <button type="button" className="home-hub-videos__ctrl" onClick={() => shiftCarousel('left')}>
              <ChevronLeft size={16} />
            </button>
            <button type="button" className="home-hub-videos__ctrl" onClick={() => shiftCarousel('right')}>
              <ChevronRight size={16} />
            </button>
          </div>
        </header>

        <div className="home-hub-videos__track" ref={carouselRef}>
          {videosForRole.map(video => {
            const thumbnail = getYoutubeThumbnail(video.url)
            return (
              <a
                key={video.url}
                href={video.url}
                target="_blank"
                rel="noreferrer"
                className="home-hub-video-card"
              >
                <div className="home-hub-video-card__thumb">
                  {thumbnail ? (
                    <img src={thumbnail} alt={video.title} loading="lazy" />
                  ) : (
                    <div className="home-hub-video-card__thumb-fallback">
                      <Video size={20} />
                    </div>
                  )}
                </div>
                <div className="home-hub-video-card__body">
                  <h3>{video.title}</h3>
                  <p>{video.description}</p>
                  <span>{lt('Mở trên YouTube', 'Open on YouTube')}</span>
                </div>
              </a>
            )
          })}
        </div>
      </section>
    </div>
  )
}

export default Dashboard
