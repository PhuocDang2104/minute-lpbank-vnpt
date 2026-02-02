import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  FileText,
  Clock,
  User,
  Check,
  Plus,
  AlertTriangle,
  HelpCircle,
  ExternalLink,
} from 'lucide-react'
import { useChatContext } from '../../../contexts/ChatContext'
import {
  meetings,
  prereadDocuments,
  users,
} from '../../../store/mockData'

const MeetingPre = () => {
  const { meetingId } = useParams()
  const meeting = meetings.find(m => m.id === meetingId)
  const prereads = prereadDocuments.filter(d => d.meetingId === meetingId)
  const { setOverride, clearOverride } = useChatContext()

  useEffect(() => {
    if (!meeting) return
    setOverride({
      scope: 'meeting',
      meetingId: meeting.id,
      phase: 'pre',
      title: meeting.title,
    })
  }, [meeting?.id, meeting?.title, setOverride])

  useEffect(() => {
    return () => clearOverride()
  }, [clearOverride])

  if (!meeting) {
    return <div>Meeting not found</div>
  }

  const agenda = [
    { item: 'Opening & Roll Call', duration: 5, presenter: 'Bùi Văn I' },
    { item: 'Review Integration Architecture', duration: 15, presenter: 'Hoàng Thị E' },
    { item: 'Risk Assessment Results', duration: 20, presenter: 'Đặng Thị K' },
    { item: 'Compliance Requirements Checklist', duration: 15, presenter: 'Đặng Thị K' },
    { item: 'Mitigation Plan Discussion', duration: 20, presenter: 'All' },
    { item: 'Action Items & Next Steps', duration: 5, presenter: 'Nguyễn Văn A' },
  ]

  const questions = [
    { id: 1, user: users['u005'], question: 'API Gateway hiện tại có đáp ứng được throughput dự kiến 500 TPS không?', type: 'question' as const },
    { id: 2, user: users['u010'], question: 'Cần xác nhận lại data retention policy cho transaction logs - 7 năm hay 10 năm theo NHNN?', type: 'risk' as const },
  ]

  const totalDuration = agenda.reduce((sum, item) => sum + item.duration, 0)

  return (
    <div className="panel-split panel-split--single">
      {/* Main Content */}
      <div className="panel-split__main">
        {/* Agenda Section */}
        <div className="card mb-4">
          <div className="card__header">
            <h3 className="card__title">
              <FileText size={18} className="card__title-icon" />
              Agenda (AI Generated)
            </h3>
            <span className="badge badge--success">
              <Check size={12} />
              Đã phê duyệt
            </span>
          </div>
          <div className="card__body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
              {agenda.map((item, index) => (
                <div key={index} className="agenda-item">
                  <div className="agenda-item__number">{index + 1}</div>
                  <div className="agenda-item__content">
                    <div className="agenda-item__title">{item.item}</div>
                    <div className="agenda-item__presenter">
                      <User size={12} />
                      {item.presenter}
                    </div>
                  </div>
                  <div className="agenda-item__duration">
                    <Clock size={12} style={{ marginRight: '4px' }} />
                    {item.duration} phút
                  </div>
                </div>
              ))}
            </div>
            <div style={{ 
              marginTop: 'var(--space-base)', 
              padding: 'var(--space-md)', 
              background: 'var(--accent-subtle)', 
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-base)'
            }}>
              <Clock size={16} className="text-accent" />
              <span>
                Tổng thời gian: <strong style={{ color: 'var(--text-primary)' }}>{totalDuration} phút</strong>
                <span style={{ margin: '0 8px' }}>•</span>
                Thời gian họp: <strong style={{ color: 'var(--text-primary)' }}>60 phút</strong>
              </span>
            </div>
          </div>
        </div>

        {/* Pre-read Documents */}
        <div className="card mb-4">
          <div className="card__header">
            <h3 className="card__title">
              <FileText size={18} className="card__title-icon" />
              Tài liệu cần đọc trước
            </h3>
            <span className="badge badge--neutral">RAG Suggested</span>
          </div>
          <div className="card__body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
              {prereads.length > 0 ? prereads.map(doc => (
                <div 
                  key={doc.id}
                  className={`doc-card ${doc.status === 'accepted' ? 'doc-card--accepted' : 'doc-card--suggested'}`}
                >
                  <div className="doc-card__header">
                    <div className="doc-card__title">{doc.title}</div>
                    {doc.status === 'accepted' ? (
                      <span className="badge badge--success">
                        <Check size={10} />
                        Đã chọn
                      </span>
                    ) : (
                      <button className="btn btn--secondary btn--sm">
                        <Plus size={14} />
                        Thêm
                      </button>
                    )}
                  </div>
                  <div className="doc-card__snippet">{doc.snippet}</div>
                  <div className="doc-card__meta">
                    <span className="badge badge--info">{doc.source}</span>
                    <span>Độ liên quan: {Math.round(doc.relevanceScore * 100)}%</span>
                    <a href={doc.url} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent)' }}>
                      <ExternalLink size={12} />
                      Mở
                    </a>
                  </div>
                </div>
              )) : (
                <div className="empty-state">
                  <FileText size={48} className="empty-state__icon" />
                  <div className="empty-state__title">Chưa có tài liệu gợi ý</div>
                  <div className="empty-state__description">
                    AI sẽ gợi ý tài liệu liên quan khi có đủ context về cuộc họp
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Pre-meeting Questions */}
        <div className="card">
          <div className="card__header">
            <h3 className="card__title">
              <HelpCircle size={18} className="card__title-icon" />
              Câu hỏi trước cuộc họp
            </h3>
            <button className="btn btn--primary btn--sm">
              <Plus size={14} />
              Thêm câu hỏi
            </button>
          </div>
          <div className="card__body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
              {questions.map(q => (
                <div 
                  key={q.id}
                  className={`question-card ${q.type === 'risk' ? 'question-card--risk' : 'question-card--question'}`}
                >
                  <div className="question-card__header">
                    <div className="question-card__avatar">
                      {q.user.displayName.split(' ').slice(-1)[0][0]}
                    </div>
                    <div className="question-card__user">
                      {q.user.displayName} • {q.user.department}
                    </div>
                  </div>
                  <div className="question-card__text">{q.question}</div>
                  <div style={{ marginTop: 'var(--space-sm)' }}>
                    <span className={`badge ${q.type === 'risk' ? 'badge--warning' : 'badge--info'}`}>
                      {q.type === 'risk' ? <AlertTriangle size={10} /> : <HelpCircle size={10} />}
                      {q.type === 'risk' ? 'Rủi ro' : 'Câu hỏi'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

    </div>
  )
}

export default MeetingPre
