import { useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock,
  RefreshCw,
  Send,
  Sparkles,
  Video,
} from 'lucide-react'
import aiApi from '../../lib/api/ai'
import { useCalendarMeetings, type NormalizedMeeting } from '../../services/meeting'
import { useLocaleText } from '../../i18n/useLocaleText'
import { currentUser } from '../../store/mockData'
import { getStoredUser } from '../../lib/api/auth'

type UserRole = 'admin' | 'PMO' | 'chair' | 'user'

interface VideoSuggestion {
  title: string
  description: string
  url: string
  roles: UserRole[]
}

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

const ROLE_LABELS: Record<UserRole, string> = {
  admin: 'Admin',
  PMO: 'PMO',
  chair: 'Chair',
  user: 'Member',
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

const Dashboard = () => {
  const { lt, dateLocale, language } = useLocaleText()
  const storedUser = getStoredUser()
  const displayUser = storedUser || currentUser
  const userRoleRaw = String(displayUser.role || 'user') as UserRole
  const userRole: UserRole = ['admin', 'PMO', 'chair', 'user'].includes(userRoleRaw) ? userRoleRaw : 'user'
  const userDisplayName = displayUser.display_name || displayUser.displayName || 'Minute User'
  const userDepartment = displayUser.department_name || displayUser.department || ''

  const [askValue, setAskValue] = useState('')
  const [askResponse, setAskResponse] = useState<string | null>(null)
  const [askError, setAskError] = useState<string | null>(null)
  const [askLoading, setAskLoading] = useState(false)

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

  const quickPrompts = [
    lt('Tóm tắt các session cần ưu tiên hôm nay', 'Summarize sessions I should prioritize today'),
    lt('Chuẩn bị agenda cho phiên gần nhất', 'Prepare an agenda for my next session'),
    lt('Nhắc tôi các deadline có rủi ro trễ', 'Highlight deadlines that are at risk'),
  ]

  const videosForRole = useMemo(() => {
    const scoped = VIDEO_SUGGESTIONS.filter(item => item.roles.includes(userRole))
    return scoped.length > 0 ? scoped : VIDEO_SUGGESTIONS.slice(0, 5)
  }, [userRole])

  const carouselRef = useRef<HTMLDivElement | null>(null)

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

  return (
    <div className="home-hub">
      <header className="home-hub__header">
        <div>
          <h1>Home</h1>
          <p>
            {lt('Không gian điều phối công việc tập trung cho ', 'A focused command center for ')}
            <strong>{userDisplayName}</strong>
            {userDepartment ? ` • ${userDepartment}` : ''}
          </p>
        </div>
        <span className="home-hub__role-pill">
          {lt('Vai trò', 'Role')}: {ROLE_LABELS[userRole]}
        </span>
      </header>

      <section className="home-hub-ai">
        <div className="home-hub-ai__bar">
          <Sparkles size={18} />
          <input
            className="home-hub-ai__input"
            value={askValue}
            onChange={event => setAskValue(event.target.value)}
            placeholder={lt('Hỏi AI nhanh hoặc yêu cầu trợ giúp một tác vụ...', 'Quickly ask AI or request support for a task...')}
            onKeyDown={event => {
              if (event.key === 'Enter') {
                event.preventDefault()
                handleAsk()
              }
            }}
            disabled={askLoading}
          />
          <button
            type="button"
            className="home-hub-ai__send"
            onClick={handleAsk}
            disabled={askLoading || !askValue.trim()}
          >
            <Send size={16} />
            {askLoading ? lt('Đang gửi', 'Sending') : lt('Gửi', 'Send')}
          </button>
        </div>

        <div className="home-hub-ai__prompts">
          {quickPrompts.map(prompt => (
            <button
              key={prompt}
              type="button"
              className="home-hub-ai__prompt-chip"
              onClick={() => setAskValue(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>

        {(askResponse || askError) && (
          <div className={`home-hub-ai__response ${askError ? 'home-hub-ai__response--error' : ''}`}>
            <span className="home-hub-ai__response-label">Minute AI</span>
            <p>{askError || askResponse}</p>
          </div>
        )}
      </section>

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
            <h2>{lt('Video suggestion theo vai trò', 'Role-based video suggestions')}</h2>
            <p>
              {lt('Nội dung được gợi ý theo role hiện tại để cải thiện hiệu suất làm việc.', 'Curated by your current role to improve day-to-day performance.')}
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
