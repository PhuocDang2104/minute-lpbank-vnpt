import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertCircle,
  Calendar,
  ChevronDown,
  FileText,
  FolderOpen,
  MoreVertical,
  RefreshCw,
  Search,
} from 'lucide-react'
import { meetings as mockMeetings, formatDate, formatTime, getInitials } from '../../../store/mockData'
import { meetingsApi } from '../../../lib/api/meetings'
import { projectsApi } from '../../../lib/api/projects'
import { USE_API } from '../../../config/env'
import type { Meeting, MeetingPhase } from '../../../shared/dto/meeting'
import { MEETING_TYPE_LABELS } from '../../../shared/dto/meeting'
import type { Project } from '../../../shared/dto/project'

const Meetings = () => {
  const [projects, setProjects] = useState<Project[]>([])
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')

  const loadData = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      if (!USE_API) {
        const mappedMeetings: Meeting[] = mockMeetings.map(m => ({
          id: m.id,
          title: m.title,
          description: m.description,
          meeting_type: m.meetingType as any,
          phase: m.phase as MeetingPhase,
          start_time: m.startTime.toISOString(),
          end_time: m.endTime.toISOString(),
          created_at: m.startTime.toISOString(),
          location: m.location,
          project_id: m.project ? `mock-${m.project.toLowerCase().replace(/\\s+/g, '-')}` : undefined,
        }))

        const mockProjects: Project[] = Array.from(
          new Map(
            mockMeetings
              .filter(m => m.project)
              .map((m, idx) => {
                const id = `mock-${m.project.toLowerCase().replace(/\\s+/g, '-')}`
                return [
                  id,
                  {
                    id,
                    name: m.project,
                    code: `PR-${idx + 1}`,
                    description: `Workspace dự án ${m.project}`,
                    meeting_count: mockMeetings.filter(mm => mm.project === m.project).length,
                    document_count: Math.max(1, idx % 4),
                    member_count: 4 + (idx % 6),
                  },
                ]
              }),
          ).values(),
        )

        setMeetings(mappedMeetings)
        setProjects(mockProjects)
        setIsLoading(false)
        return
      }

      const [projectRes, meetingRes] = await Promise.allSettled([
        projectsApi.list({ limit: 200 }),
        meetingsApi.list({ limit: 400 }),
      ])

      let meetingFailed = false
      let projectFailed = false

      if (meetingRes.status === 'fulfilled') {
        setMeetings(meetingRes.value.meetings || [])
      } else {
        meetingFailed = true
        setMeetings([])
      }

      if (projectRes.status === 'fulfilled') {
        setProjects(projectRes.value.projects || [])
      } else {
        projectFailed = true
        setProjects([])
      }

      if (meetingFailed) {
        setError('Không thể tải dữ liệu cuộc họp. Vui lòng thử lại.')
      } else if (projectFailed) {
        setError('Không thể tải danh sách dự án. Các phiên lẻ vẫn hiển thị.')
      }
    } catch (err) {
      console.error('Failed to load meetings workspace:', err)
      setError('Không thể tải dữ liệu cuộc họp. Vui lòng thử lại.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const normalizedSearch = search.trim().toLowerCase()

  const filteredProjects = useMemo(() => {
    if (!normalizedSearch) return projects
    return projects.filter(project => (
      project.name?.toLowerCase().includes(normalizedSearch)
      || project.code?.toLowerCase().includes(normalizedSearch)
      || project.description?.toLowerCase().includes(normalizedSearch)
      || project.objective?.toLowerCase().includes(normalizedSearch)
    ))
  }, [projects, normalizedSearch])

  const filteredMeetings = useMemo(() => {
    if (!normalizedSearch) return meetings
    return meetings.filter(meeting => (
      meeting.title?.toLowerCase().includes(normalizedSearch)
      || meeting.description?.toLowerCase().includes(normalizedSearch)
      || meeting.location?.toLowerCase().includes(normalizedSearch)
      || MEETING_TYPE_LABELS[meeting.meeting_type]?.toLowerCase().includes(normalizedSearch)
    ))
  }, [meetings, normalizedSearch])

  const standaloneMeetings = useMemo(() => (
    filteredMeetings
      .filter(meeting => !meeting.project_id)
      .sort((a, b) => {
        const timeA = new Date(a.created_at || a.start_time || '').getTime()
        const timeB = new Date(b.created_at || b.start_time || '').getTime()
        return timeB - timeA
      })
  ), [filteredMeetings])

  return (
    <div className="drive-page">
      <div className="drive-toolbar">
        <div className="drive-search">
          <Search size={16} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search in Drive"
          />
        </div>
        <button className="btn btn--ghost drive-refresh" onClick={loadData} disabled={isLoading} title="Làm mới">
          <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
        </button>
      </div>

      <header className="drive-welcome">
        <h1>Workspace</h1>
        <p>
          Các cuộc họp được tổ chức theo thư mục dự án, còn phiên lẻ hiển thị như Suggested files.
        </p>
      </header>

      {error && (
        <div className="drive-banner drive-banner--error">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {isLoading && (
        <div className="drive-loading">
          <div className="spinner" style={{ width: 28, height: 28 }}></div>
          <p>Đang tải dữ liệu...</p>
        </div>
      )}

      {!isLoading && (
        <>
          <section className="drive-section">
            <div className="drive-section__title">
              <ChevronDown size={16} />
              Suggested folders
            </div>

            {filteredProjects.length === 0 ? (
              <div className="drive-empty">
                <FolderOpen size={28} />
                <div>
                  <h3>Chưa có dự án</h3>
                  <p>Tạo dự án mới để gom các phiên liên quan.</p>
                </div>
              </div>
            ) : (
              <div className="drive-folders">
                {filteredProjects.map(project => (
                  <Link key={project.id} to={`/app/projects/${project.id}`} className="drive-folder">
                    <div className="drive-folder__icon">
                      <FolderOpen size={18} />
                    </div>
                    <div className="drive-folder__info">
                      <div className="drive-folder__name">{project.name}</div>
                      <div className="drive-folder__meta">In Workspace</div>
                    </div>
                    <MoreVertical size={16} className="drive-folder__more" />
                  </Link>
                ))}
              </div>
            )}
          </section>

          <section className="drive-section">
            <div className="drive-section__title">
              <ChevronDown size={16} />
              Suggested files
            </div>

            {standaloneMeetings.length === 0 ? (
              <div className="drive-empty">
                <FileText size={26} />
                <div>
                  <h3>Chưa có phiên lẻ</h3>
                  <p>Tạo mới hoặc gỡ liên kết dự án để hiển thị tại đây.</p>
                </div>
              </div>
            ) : (
              <div className="drive-table">
                <div className="drive-table__header">
                  <div>Name</div>
                  <div>Reason suggested</div>
                  <div>Owner</div>
                  <div>Location</div>
                </div>
                {standaloneMeetings.map(meeting => (
                  <DriveSuggestedRow key={meeting.id} meeting={meeting} />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}

const DriveSuggestedRow = ({ meeting }: { meeting: Meeting }) => {
  const createdDate = meeting.created_at
    ? new Date(meeting.created_at)
    : (meeting.start_time ? new Date(meeting.start_time) : new Date())
  const start = meeting.start_time ? new Date(meeting.start_time) : null
  const end = meeting.end_time ? new Date(meeting.end_time) : null
  const timeLabel = start && end ? `${formatTime(start)} - ${formatTime(end)}` : ''

  const ownerName = meeting.organizer?.display_name || meeting.organizer?.full_name || 'me'
  const initials = getInitials(ownerName)
  const reason = meeting.phase === 'in' ? 'Đang diễn ra' : `Gần đây • ${formatDate(createdDate)}`

  return (
    <Link to={`/app/meetings/${meeting.id}/detail`} className="drive-table__row">
      <div className="drive-table__cell drive-table__name">
        <div className="drive-file-icon">
          <FileText size={16} />
        </div>
        <div>
          <div className="drive-file-title">{meeting.title}</div>
          <div className="drive-file-meta">
            {MEETING_TYPE_LABELS[meeting.meeting_type] || meeting.meeting_type}
            {timeLabel ? ` • ${timeLabel}` : ''}
          </div>
        </div>
      </div>
      <div className="drive-table__cell">{reason}</div>
      <div className="drive-table__cell">
        <div className="drive-owner">
          <span className="drive-owner__avatar">{initials}</span>
          {ownerName}
        </div>
      </div>
      <div className="drive-table__cell">
        <span className="drive-location">Phiên lẻ</span>
      </div>
    </Link>
  )
}

export default Meetings
