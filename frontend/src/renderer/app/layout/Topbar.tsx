import { useMemo, useState, useRef, useEffect, useCallback } from 'react'
import { useLocation, Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  HelpCircle,
  Home,
  ChevronRight,
  Search,
  LogOut,
  FolderOpen,
  Users,
  BookOpen,
  X,
} from 'lucide-react'
import { useLocaleText } from '../../i18n/useLocaleText'
import { useLanguage } from '../../contexts/LanguageContext'
import { logout } from '../../lib/api/auth'
import { meetingsApi } from '../../lib/api/meetings'
import { projectsApi } from '../../lib/api/projects'
import { USE_API } from '../../config/env'
import { meetings as mockMeetings } from '../../store/mockData'
import type { Meeting, MeetingPhase } from '../../shared/dto/meeting'
import type { Project } from '../../shared/dto/project'

type SearchEntityType = 'project' | 'meeting' | 'course'

interface SearchSuggestion {
  id: string
  entityType: SearchEntityType
  title: string
  subtitle?: string
  route: string
}

const RECENT_SEARCH_STORAGE_KEY = 'minute_topbar_recent_searches'
const MAX_RECENT_SEARCHES = 6
const MAX_PROJECT_SUGGESTIONS = 5
const MAX_SESSION_SUGGESTIONS = 6
const PROJECT_SEARCH_LIMIT = 200
const MEETING_SEARCH_LIMIT = 400

const normalizeSearchText = (value: string | null | undefined): string => (
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[đĐ]/g, 'd')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
)

const isSearchSuggestion = (value: unknown): value is SearchSuggestion => {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Record<string, unknown>
  const entityType = candidate.entityType
  return (
    typeof candidate.id === 'string'
    && typeof candidate.title === 'string'
    && typeof candidate.route === 'string'
    && (entityType === 'project' || entityType === 'meeting' || entityType === 'course')
  )
}

const Topbar = () => {
  const location = useLocation()
  const currentPath = location.pathname
  const navigate = useNavigate()
  const isDockView = /^\/app\/meetings\/[^/]+\/dock/.test(currentPath)
  const { lt, dateLocale } = useLocaleText()
  const { language, setLanguage } = useLanguage()

  const [searchTerm, setSearchTerm] = useState('')
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [isSearchLoading, setIsSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [hasSearchIndexLoaded, setHasSearchIndexLoaded] = useState(false)
  const [projectsIndex, setProjectsIndex] = useState<Project[]>([])
  const [meetingsIndex, setMeetingsIndex] = useState<Meeting[]>([])
  const [recentSearches, setRecentSearches] = useState<SearchSuggestion[]>([])

  const searchContainerRef = useRef<HTMLDivElement | null>(null)

  const toggleLanguage = () => setLanguage(language === 'vi' ? 'en' : 'vi')
  const languageSwitchLabel = language === 'vi' ? 'VI' : 'EN'

  const routeTitles: Record<string, string> = useMemo(() => ({
    '/': 'Home',
    '/app': 'Home',
    '/app/home': 'Home',
    '/app/dashboard': 'Home',
    '/app/calendar': lt('Lịch họp', 'Calendar'),
    '/app/meetings': 'Workspace',
    '/app/projects': lt('Dự án', 'Projects'),
    '/app/knowledge': lt('Kho kiến thức', 'Knowledge Hub'),
    '/app/tasks': lt('Nhiệm vụ', 'Tasks'),
    '/app/settings': lt('Cài đặt', 'Settings'),
    '/app/admin': lt('Bảng quản trị', 'Admin Console'),
  }), [lt])

  const routeBreadcrumbs: Array<{ match: RegExp; trail: string[] }> = useMemo(
    () => [
      { match: /^\/app\/meetings\/[^/]+\/detail/, trail: ['Workspace', lt('Chi tiết phiên', 'Session detail')] },
      { match: /^\/app\/projects\/[^/]+$/, trail: [lt('Dự án', 'Projects'), lt('Chi tiết dự án', 'Project detail')] },
    ],
    [lt],
  )

  const findPageTitle = (path: string) => {
    if (routeTitles[path]) return routeTitles[path]
    if (path.startsWith('/app/meetings')) return 'Workspace'
    if (path.startsWith('/app/projects')) return lt('Dự án', 'Projects')
    if (path.startsWith('/app/knowledge')) return lt('Kho kiến thức', 'Knowledge Hub')
    if (path.startsWith('/app/tasks')) return lt('Nhiệm vụ', 'Tasks')
    if (path.startsWith('/app/settings')) return lt('Cài đặt', 'Settings')
    return 'Minute'
  }

  const handleLogout = () => {
    void logout()
      .catch(() => null)
      .finally(() => navigate('/'))
  }

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      const raw = window.localStorage.getItem(RECENT_SEARCH_STORAGE_KEY)
      if (!raw) return
      const parsed = JSON.parse(raw)
      if (!Array.isArray(parsed)) return
      setRecentSearches(parsed.filter(isSearchSuggestion).slice(0, MAX_RECENT_SEARCHES))
    } catch {
      setRecentSearches([])
    }
  }, [])

  useEffect(() => {
    if (!isSearchOpen) return

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node | null
      if (searchContainerRef.current?.contains(target)) return
      setIsSearchOpen(false)
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isSearchOpen])

  const persistRecentSearches = useCallback((items: SearchSuggestion[]) => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(RECENT_SEARCH_STORAGE_KEY, JSON.stringify(items))
  }, [])

  const pushRecentSearch = useCallback((item: SearchSuggestion) => {
    setRecentSearches((prev) => {
      const deduplicated = prev.filter(
        (existing) => !(existing.entityType === item.entityType && existing.id === item.id),
      )
      const next = [item, ...deduplicated].slice(0, MAX_RECENT_SEARCHES)
      persistRecentSearches(next)
      return next
    })
  }, [persistRecentSearches])

  const loadSearchIndex = useCallback(async (force = false) => {
    if (isSearchLoading) return
    if (hasSearchIndexLoaded && !force) return

    setIsSearchLoading(true)
    setSearchError(null)

    try {
      if (!USE_API) {
        const fallbackMeetings: Meeting[] = mockMeetings.map((item) => {
          const projectId = item.project ? `mock-${item.project.toLowerCase().replace(/\s+/g, '-')}` : undefined
          return {
            id: item.id,
            title: item.title,
            description: item.description,
            meeting_type: item.meetingType as Meeting['meeting_type'],
            phase: item.phase as MeetingPhase,
            start_time: item.startTime.toISOString(),
            end_time: item.endTime.toISOString(),
            project_id: projectId,
            created_at: item.startTime.toISOString(),
            location: item.location,
          }
        })

        const fallbackProjects: Project[] = Array.from(
          new Map(
            mockMeetings
              .filter((item) => Boolean(item.project))
              .map((item) => {
                const id = `mock-${String(item.project).toLowerCase().replace(/\s+/g, '-')}`
                return [id, { id, name: String(item.project) }]
              }),
          ).values(),
        )

        setProjectsIndex(fallbackProjects)
        setMeetingsIndex(fallbackMeetings)
        setHasSearchIndexLoaded(true)
        return
      }

      const [projectResult, meetingResult] = await Promise.allSettled([
        projectsApi.list({ limit: PROJECT_SEARCH_LIMIT }),
        meetingsApi.list({ limit: MEETING_SEARCH_LIMIT }),
      ])

      const projectLoaded = projectResult.status === 'fulfilled'
      const meetingLoaded = meetingResult.status === 'fulfilled'

      setProjectsIndex(projectLoaded ? (projectResult.value.projects || []) : [])
      setMeetingsIndex(meetingLoaded ? (meetingResult.value.meetings || []) : [])

      const hasAnyLoaded = projectLoaded || meetingLoaded
      setHasSearchIndexLoaded(hasAnyLoaded)

      if (!hasAnyLoaded) {
        setSearchError(lt('Không thể tải dữ liệu tìm kiếm. Vui lòng thử lại.', 'Unable to load search data. Please try again.'))
      }
    } catch {
      setSearchError(lt('Không thể tải dữ liệu tìm kiếm. Vui lòng thử lại.', 'Unable to load search data. Please try again.'))
    } finally {
      setIsSearchLoading(false)
    }
  }, [hasSearchIndexLoaded, isSearchLoading, lt])

  const normalizedSearch = normalizeSearchText(searchTerm)
  const queryTokens = useMemo(
    () => normalizedSearch.split(/\s+/).filter(Boolean),
    [normalizedSearch],
  )

  const projectNameById = useMemo(
    () => new Map(projectsIndex.map((project) => [project.id, project.name])),
    [projectsIndex],
  )

  const projectSuggestions = useMemo<SearchSuggestion[]>(() => {
    if (queryTokens.length === 0) return []

    const matchesQuery = (parts: Array<string | null | undefined>) => {
      const text = normalizeSearchText(parts.filter(Boolean).join(' '))
      return queryTokens.every((token) => text.includes(token))
    }

    return projectsIndex
      .filter((project) => matchesQuery([project.name, project.code, project.description, project.objective]))
      .slice(0, MAX_PROJECT_SUGGESTIONS)
      .map((project) => ({
        id: project.id,
        entityType: 'project',
        title: project.name,
        subtitle: project.code || undefined,
        route: `/app/projects/${project.id}`,
      }))
  }, [projectsIndex, queryTokens])

  const sessionSuggestions = useMemo<SearchSuggestion[]>(() => {
    if (queryTokens.length === 0) return []

    const matchesQuery = (parts: Array<string | null | undefined>) => {
      const text = normalizeSearchText(parts.filter(Boolean).join(' '))
      return queryTokens.every((token) => text.includes(token))
    }

    const ordered = [...meetingsIndex].sort((a, b) => {
      const timeA = new Date(a.created_at || a.start_time || '').getTime()
      const timeB = new Date(b.created_at || b.start_time || '').getTime()
      return timeB - timeA
    })

    return ordered
      .filter((meeting) => {
        const isCourse = meeting.meeting_type === 'study_session'
        const projectName = meeting.project_id ? projectNameById.get(meeting.project_id) : undefined
        return matchesQuery([
          meeting.title,
          meeting.description,
          projectName,
          isCourse ? 'course training study đào tạo khóa học lớp học' : 'meeting họp phiên workspace',
        ])
      })
      .slice(0, MAX_SESSION_SUGGESTIONS)
      .map((meeting) => {
        const isCourse = meeting.meeting_type === 'study_session'
        const projectName = meeting.project_id ? projectNameById.get(meeting.project_id) : undefined
        const rawDate = meeting.start_time || meeting.created_at
        const formattedDate = rawDate
          ? (() => {
            const date = new Date(rawDate)
            if (Number.isNaN(date.getTime())) return ''
            return date.toLocaleDateString(dateLocale, { day: '2-digit', month: '2-digit', year: 'numeric' })
          })()
          : ''

        const subtitleParts = [
          projectName ? `${lt('Dự án', 'Project')}: ${projectName}` : undefined,
          formattedDate || undefined,
        ].filter(Boolean)

        return {
          id: meeting.id,
          entityType: isCourse ? 'course' : 'meeting',
          title: meeting.title,
          subtitle: subtitleParts.length ? subtitleParts.join(' • ') : undefined,
          route: `/app/meetings/${meeting.id}/detail`,
        }
      })
  }, [dateLocale, lt, meetingsIndex, projectNameById, queryTokens])

  const firstSuggestion = projectSuggestions[0] || sessionSuggestions[0] || null

  const getEntityTag = useCallback((entityType: SearchEntityType) => {
    if (entityType === 'project') return lt('Dự án', 'Project')
    if (entityType === 'course') return lt('Khóa học', 'Course')
    return lt('Phiên', 'Session')
  }, [lt])

  const renderSuggestionIcon = useCallback((entityType: SearchEntityType) => {
    if (entityType === 'project') return <FolderOpen size={15} />
    if (entityType === 'course') return <BookOpen size={15} />
    return <Users size={15} />
  }, [])

  const handleSuggestionSelect = useCallback((suggestion: SearchSuggestion) => {
    pushRecentSearch(suggestion)
    setSearchTerm(suggestion.title)
    setIsSearchOpen(false)
    navigate(suggestion.route)
  }, [navigate, pushRecentSearch])

  const handleSearchFocus = () => {
    setIsSearchOpen(true)
    void loadSearchIndex(true)
  }

  const handleSearchInputChange = (nextValue: string) => {
    setSearchTerm(nextValue)
    if (!isSearchOpen) {
      setIsSearchOpen(true)
    }
    if (!hasSearchIndexLoaded) {
      void loadSearchIndex()
    }
  }

  const clearSearchInput = () => {
    setSearchTerm('')
    setSearchError(null)
    setIsSearchOpen(true)
  }

  const showRecentSearches = queryTokens.length === 0
  const hasMatchedResults = projectSuggestions.length > 0 || sessionSuggestions.length > 0

  return (
    <header className={`topbar ${isDockView ? 'topbar--dock' : ''}`}>
      {isDockView ? (
        <>
          <div className="topbar__dock-left">
            <div className="topbar__dock-brand">
              <img src="/minute_icon.svg" alt="Minute" className="topbar__dock-logo" />
              <span className="topbar__dock-name">Minute</span>
            </div>
            <ChevronRight size={14} className="topbar__dock-sep" />
            <span className="topbar__dock-crumb">Workspace</span>
          </div>
          <div className="topbar__dock-right">
            <button
              className="topbar__icon-btn"
              onClick={toggleLanguage}
              title={language === 'vi' ? 'Switch to English' : lt('Chuyển sang tiếng Việt', 'Switch to Vietnamese')}
              type="button"
            >
              {languageSwitchLabel}
            </button>
            <button
              className="topbar__icon-btn topbar__dock-back"
              onClick={() => navigate(-1)}
              title={lt('Quay lại', 'Back')}
              type="button"
            >
              <ArrowLeft size={18} />
            </button>
          </div>
        </>
      ) : (
        <>
          <div className="topbar__left">
            {(() => {
              const matched = routeBreadcrumbs.find(item => item.match.test(currentPath))
              const baseCrumb = findPageTitle(currentPath)
              const trail = matched ? matched.trail : []
              const crumbs = trail.length && trail[0] === baseCrumb ? trail : [baseCrumb, ...trail]
              return (
                <div className="topbar__breadcrumb">
                  <Home size={14} />
                  <ChevronRight size={14} />
                  {crumbs.map((crumb, idx) => (
                    <span
                      key={`${crumb}-${idx}`}
                      className={idx === 0 ? 'topbar__breadcrumb-current' : 'topbar__breadcrumb-extra'}
                    >
                      {idx > 0 && <ChevronRight size={12} />}
                      {crumb}
                    </span>
                  ))}
                </div>
              )
            })()}
            <div className={`topbar__search ${isSearchOpen ? 'is-open' : ''}`} ref={searchContainerRef}>
              <Search className="topbar__search-icon" />
              <input
                type="search"
                className="topbar__search-input"
                placeholder={lt('Tìm cuộc họp, khóa đào tạo, dự án...', 'Search meetings, training courses, projects...')}
                value={searchTerm}
                onFocus={handleSearchFocus}
                onChange={(event) => handleSearchInputChange(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Escape') {
                    setIsSearchOpen(false)
                    return
                  }
                  if (event.key === 'Enter' && firstSuggestion) {
                    event.preventDefault()
                    handleSuggestionSelect(firstSuggestion)
                  }
                }}
              />
              {searchTerm && (
                <button
                  type="button"
                  className="topbar__search-clear"
                  title={lt('Xóa tìm kiếm', 'Clear search')}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={clearSearchInput}
                >
                  <X size={16} />
                </button>
              )}

              {isSearchOpen && (
                <div className="topbar-search__panel" role="listbox" aria-label={lt('Gợi ý tìm kiếm', 'Search suggestions')}>
                  {isSearchLoading && !hasSearchIndexLoaded && (
                    <div className="topbar-search__empty">{lt('Đang tải dữ liệu...', 'Loading data...')}</div>
                  )}

                  {showRecentSearches ? (
                    <div className="topbar-search__section">
                      <div className="topbar-search__section-title">{lt('Tìm kiếm gần đây', 'Recent searches')}</div>
                      {recentSearches.length > 0 ? (
                        recentSearches.map((suggestion) => (
                          <button
                            key={`${suggestion.entityType}-${suggestion.id}`}
                            type="button"
                            className="topbar-search__item"
                            onMouseDown={(event) => event.preventDefault()}
                            onClick={() => handleSuggestionSelect(suggestion)}
                          >
                            <span className={`topbar-search__item-icon topbar-search__item-icon--${suggestion.entityType}`}>
                              {renderSuggestionIcon(suggestion.entityType)}
                            </span>
                            <span className="topbar-search__item-main">
                              <span className="topbar-search__item-title">{suggestion.title}</span>
                              {suggestion.subtitle && (
                                <span className="topbar-search__item-subtitle">{suggestion.subtitle}</span>
                              )}
                            </span>
                            <span className="topbar-search__item-tag">{getEntityTag(suggestion.entityType)}</span>
                          </button>
                        ))
                      ) : (
                        <div className="topbar-search__empty">
                          {lt('Bắt đầu gõ để tìm phiên, khóa đào tạo hoặc dự án.', 'Start typing to search meetings, training courses, and projects.')}
                        </div>
                      )}
                    </div>
                  ) : (
                    <>
                      {projectSuggestions.length > 0 && (
                        <div className="topbar-search__section">
                          <div className="topbar-search__section-title">{lt('Dự án', 'Projects')}</div>
                          {projectSuggestions.map((suggestion) => (
                            <button
                              key={`${suggestion.entityType}-${suggestion.id}`}
                              type="button"
                              className="topbar-search__item"
                              onMouseDown={(event) => event.preventDefault()}
                              onClick={() => handleSuggestionSelect(suggestion)}
                            >
                              <span className={`topbar-search__item-icon topbar-search__item-icon--${suggestion.entityType}`}>
                                {renderSuggestionIcon(suggestion.entityType)}
                              </span>
                              <span className="topbar-search__item-main">
                                <span className="topbar-search__item-title">{suggestion.title}</span>
                                {suggestion.subtitle && (
                                  <span className="topbar-search__item-subtitle">{suggestion.subtitle}</span>
                                )}
                              </span>
                              <span className="topbar-search__item-tag">{getEntityTag(suggestion.entityType)}</span>
                            </button>
                          ))}
                        </div>
                      )}

                      {sessionSuggestions.length > 0 && (
                        <div className="topbar-search__section">
                          <div className="topbar-search__section-title">{lt('Phiên', 'Sessions')}</div>
                          {sessionSuggestions.map((suggestion) => (
                            <button
                              key={`${suggestion.entityType}-${suggestion.id}`}
                              type="button"
                              className="topbar-search__item"
                              onMouseDown={(event) => event.preventDefault()}
                              onClick={() => handleSuggestionSelect(suggestion)}
                            >
                              <span className={`topbar-search__item-icon topbar-search__item-icon--${suggestion.entityType}`}>
                                {renderSuggestionIcon(suggestion.entityType)}
                              </span>
                              <span className="topbar-search__item-main">
                                <span className="topbar-search__item-title">{suggestion.title}</span>
                                {suggestion.subtitle && (
                                  <span className="topbar-search__item-subtitle">{suggestion.subtitle}</span>
                                )}
                              </span>
                              <span className="topbar-search__item-tag">{getEntityTag(suggestion.entityType)}</span>
                            </button>
                          ))}
                        </div>
                      )}

                      {!hasMatchedResults && !isSearchLoading && (
                        <div className="topbar-search__empty">{lt('Không tìm thấy kết quả phù hợp.', 'No matching results found.')}</div>
                      )}
                    </>
                  )}

                  {searchError && (
                    <div className="topbar-search__error">{searchError}</div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="topbar__right">
            <button
              className="topbar__icon-btn"
              onClick={toggleLanguage}
              title={language === 'vi' ? 'Switch to English' : lt('Chuyển sang tiếng Việt', 'Switch to Vietnamese')}
              type="button"
            >
              {languageSwitchLabel}
            </button>
            <Link to="/about" className="topbar__icon-btn" title={lt('About MINUTE', 'About MINUTE')}>
              <HelpCircle size={18} />
            </Link>
            <button
              type="button"
              className="topbar__icon-btn topbar__icon-btn--logout"
              title={lt('Quay về landing page', 'Back to landing page')}
              onClick={handleLogout}
            >
              <LogOut size={18} />
            </button>
          </div>
        </>
      )}
    </header>
  )
}

export default Topbar

