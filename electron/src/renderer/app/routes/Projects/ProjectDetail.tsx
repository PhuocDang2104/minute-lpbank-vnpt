import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getStoredUser } from '../../../lib/api/auth'
import { Project } from '../../../shared/dto/project'
import { Document } from '../../../shared/dto/document'
import { Meeting } from '../../../shared/dto/meeting'
import { ProjectMember } from '../../../shared/dto/projectMember'
import { useLanguage } from '../../../contexts/LanguageContext'
import { useChatContext } from '../../../contexts/ChatContext'
import projectsApi from '../../../lib/api/projects'
import meetingsApi from '../../../lib/api/meetings'
import { knowledgeApi, type KnowledgeDocument } from '../../../lib/api/knowledge'
import { FolderOpen, Users, FileText, Calendar, Loader2, CheckCircle, X, Trash2, ExternalLink } from 'lucide-react'
import { adminListUsers } from '../../../lib/api/admin'
import { UploadDocumentModal, type UploadToastState } from '../../../components/UploadDocumentModal'
import { API_URL } from '../../../config/env'

const ProjectDetail = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { t } = useLanguage()
  const { setOverride, clearOverride } = useChatContext()
  const user = getStoredUser()
  const isAdmin = (user?.role || '').toLowerCase() === 'admin'

  const [project, setProject] = useState<Project | null>(null)
  const [members, setMembers] = useState<ProjectMember[]>([])
  const [docs, setDocs] = useState<Document[]>([])
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [availableDocs, setAvailableDocs] = useState<KnowledgeDocument[]>([])
  const [isLoadingDocs, setIsLoadingDocs] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showMemberModal, setShowMemberModal] = useState(false)
  const [memberForm, setMemberForm] = useState({ user_id: '', role: 'member' })
  const [availableUsers, setAvailableUsers] = useState<any[]>([])
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [showMeetingModal, setShowMeetingModal] = useState(false)
  const [meetingForm, setMeetingForm] = useState<{ title: string; start_time: string; location?: string; meeting_type?: string }>({
    title: '',
    start_time: '',
    location: '',
    meeting_type: 'weekly_status',
  })
  const [meetingSaving, setMeetingSaving] = useState(false)
  const [memberSaving, setMemberSaving] = useState(false)
  const [showDocModal, setShowDocModal] = useState(false)
  const [uploadToast, setUploadToast] = useState<UploadToastState | null>(null)
  const [showAttachModal, setShowAttachModal] = useState(false)
  const [searchDoc, setSearchDoc] = useState('')
  const [attaching, setAttaching] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editSaving, setEditSaving] = useState(false)
  const [editForm, setEditForm] = useState<{ name: string; code?: string; description?: string; objective?: string }>({ name: '', code: '', description: '', objective: '' })

  useEffect(() => {
    const load = async () => {
      if (!projectId) return
      setLoading(true)
      try {
        // project detail
        const proj = await projectsApi.get(projectId)
        setProject(proj)
        setEditForm({
          name: proj.name || '',
          code: proj.code || '',
          description: proj.description || '',
          objective: proj.objective || '',
        })
        // members
        const m = await projectsApi.listMembers(projectId)
        setMembers(m.members || [])
        // documents
        const d = await projectsApi.listDocuments(projectId)
        setDocs(d.documents || [])
        // meetings
        const mt = await projectsApi.listMeetings(projectId)
        setMeetings(mt.meetings || [])
        // preload docs list for attach
        setIsLoadingDocs(true)
        try {
          const allDocs = await knowledgeApi.list({ limit: 100 })
          setAvailableDocs(allDocs.documents)
        } catch (err) {
          console.error('Failed to load docs', err)
        } finally {
          setIsLoadingDocs(false)
        }
        // load users for member selection
        setLoadingUsers(true)
        try {
          const resUsers = await adminListUsers({ limit: 200 })
          const list = (resUsers as any).users || (resUsers as any).data || []
          setAvailableUsers(list)
        } catch (err) {
          console.error('Failed to load users', err)
        } finally {
          setLoadingUsers(false)
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [projectId])

  useEffect(() => {
    if (!projectId) return
    setOverride({
      scope: 'project',
      projectId,
      title: project?.name || undefined,
    })
  }, [projectId, project?.name, setOverride])

  useEffect(() => {
    return () => clearOverride()
  }, [clearOverride])

  if (!isAdmin) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-header__title">Dự án</h1>
          <p>Bạn cần quyền admin để xem chi tiết dự án.</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="page">
        <div className="form-loading" style={{ padding: 'var(--space-2xl)' }}>
          <div className="spinner" style={{ width: 32, height: 32 }}></div>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="page">
        <div className="empty-state">
          <FolderOpen className="empty-state__icon" />
          <h3 className="empty-state__title">Không tìm thấy dự án</h3>
          <p className="empty-state__description">Kiểm tra lại liên kết hoặc danh sách dự án.</p>
        </div>
      </div>
    )
  }

  const fallbackMembers: ProjectMember[] = [
    {
      project_id: projectId || '',
      user_id: 'dang-nhu-phuoc',
      display_name: 'Đặng Như Phước',
      email: 'phuoc.dang2104@gmail.com',
      role: 'member',
    },
    {
      project_id: projectId || '',
      user_id: 'dat-truongminh',
      display_name: 'Đạt',
      email: 'truongminhdathd@gmail.com',
      role: 'member',
    },
    {
      project_id: projectId || '',
      user_id: 'thai-hoai-an',
      display_name: 'Thái Hoài An',
      email: 'hoaianthai345@gmail.com',
      role: 'member',
    },
  ]
  const displayMembers = members.length > 0 ? members : fallbackMembers

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-header__eyebrow">Project</p>
          <h1 className="page-header__title">{project.name}</h1>
          {project.objective && (
            <div style={{ marginTop: 'var(--space-sm)', padding: 'var(--space-sm)', background: 'rgba(246, 193, 59, 0.1)', borderRadius: 'var(--radius-md)', borderLeft: '3px solid var(--primary)' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--primary)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Mục tiêu dự án
              </div>
              <div style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                {project.objective}
              </div>
            </div>
          )}
          <p className="page-header__subtitle" style={{ marginTop: project.objective ? 'var(--space-sm)' : 0 }}>
            {project.description || 'Chưa có mô tả'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn--ghost btn--sm" onClick={() => setShowEditModal(true)}>Chỉnh sửa</button>
          <button
            className="btn btn--primary btn--sm"
            style={{ background: 'var(--error)', borderColor: 'var(--error)' }}
            onClick={async () => {
              if (!projectId) return
              const ok = window.confirm('Bạn có chắc muốn xóa dự án này? Tất cả cuộc họp, tài liệu, embedding liên quan sẽ bị xóa.')
              if (!ok) return
              try {
                await projectsApi.remove(projectId)
                navigate('/app/projects')
              } catch (err) {
                console.error('Delete project failed', err)
                alert('Xóa dự án thất bại. Kiểm tra quyền admin.')
              }
            }}
          >
            Xóa
          </button>
        </div>
      </div>

      {/* Modal: Add Member */}
      {showMemberModal && (
        <div className="modal-overlay" onClick={() => setShowMemberModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 480 }}>
            <div className="modal__header">
              <h3 className="modal__title">Thêm thành viên</h3>
            </div>
            <div className="modal__body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="form-group">
                <label className="form-label">Chọn người dùng</label>
                {loadingUsers ? (
                  <div className="form-loading">Đang tải danh sách...</div>
                ) : (
                  <select
                    className="form-select"
                    value={memberForm.user_id}
                    onChange={e => setMemberForm({ ...memberForm, user_id: e.target.value })}
                  >
                    <option value="">-- Chọn thành viên --</option>
                    {availableUsers.map(u => (
                      <option key={u.id} value={u.id}>{u.display_name || u.email || u.id}</option>
                    ))}
                  </select>
                )}
              </div>
              <div className="form-group">
                <label className="form-label">Hoặc nhập email/User ID</label>
                <input
                  className="form-input"
                  placeholder="user@example.com"
                  value={memberForm.user_id}
                  onChange={e => setMemberForm({ ...memberForm, user_id: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Role</label>
                <select
                  className="form-select"
                  value={memberForm.role}
                  onChange={e => setMemberForm({ ...memberForm, role: e.target.value })}
                >
                  <option value="member">Member</option>
                  <option value="owner">Owner</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
            </div>
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setShowMemberModal(false)}>Hủy</button>
              <button
                className="btn btn--primary"
                disabled={memberSaving || !memberForm.user_id.trim()}
                onClick={async () => {
                  setMemberSaving(true)
                  try {
                    await projectsApi.addMember(projectId!, memberForm.user_id.trim(), memberForm.role)
                    const m = await projectsApi.listMembers(projectId!)
                    setMembers(m.members || [])
                    setShowMemberModal(false)
                    setMemberForm({ user_id: '', role: 'member' })
                  } catch (err) {
                    console.error('Add member failed', err)
                    alert('Thêm thành viên thất bại. Kiểm tra quyền admin hoặc user id.')
                  } finally {
                    setMemberSaving(false)
                  }
                }}
              >
                {memberSaving ? 'Đang thêm...' : 'Thêm'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Modal: Add Meeting */}
      {showMeetingModal && (
        <div className="modal-overlay" onClick={() => setShowMeetingModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 640 }}>
            <div className="modal__header">
              <h3 className="modal__title">Tạo cuộc họp</h3>
            </div>
            <div className="modal__body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="form-group">
                <label className="form-label">Tiêu đề cuộc họp *</label>
                <input
                  className="form-input"
                  placeholder="VD: Weekly Status - Mobile Banking Sprint 24"
                  value={meetingForm.title}
                  onChange={e => setMeetingForm({ ...meetingForm, title: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Loại cuộc họp</label>
                  <select
                    className="form-select"
                    value={meetingForm.meeting_type}
                    onChange={e => setMeetingForm({ ...meetingForm, meeting_type: e.target.value })}
                  >
                    <option value="weekly_status">Weekly Status</option>
                    <option value="steering">Steering</option>
                    <option value="risk_review">Risk Review</option>
                    <option value="workshop">Workshop</option>
                    <option value="daily">Daily</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Thời gian bắt đầu</label>
                  <input
                    className="form-input"
                    type="datetime-local"
                    value={meetingForm.start_time}
                    onChange={e => setMeetingForm({ ...meetingForm, start_time: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Địa điểm / Teams link</label>
                <input
                  className="form-input"
                  placeholder="VD: Microsoft Teams / Phòng họp VIP"
                  value={meetingForm.location}
                  onChange={e => setMeetingForm({ ...meetingForm, location: e.target.value })}
                />
              </div>
            </div>
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setShowMeetingModal(false)}>Hủy</button>
              <button
                className="btn btn--primary"
                disabled={meetingSaving || !meetingForm.title.trim()}
                onClick={async () => {
                  setMeetingSaving(true)
                  try {
                    await meetingsApi.create({
                      title: meetingForm.title.trim(),
                      start_time: meetingForm.start_time || undefined,
                      meeting_type: meetingForm.meeting_type as any,
                      location: meetingForm.location || undefined,
                      project_id: projectId,
                    } as any)
                    const mt = await projectsApi.listMeetings(projectId!)
                    setMeetings(mt.meetings || [])
                    setShowMeetingModal(false)
                    setMeetingForm({ title: '', start_time: '', location: '', meeting_type: 'weekly_status' })
                  } catch (err) {
                    console.error('Create meeting failed', err)
                    alert('Tạo cuộc họp thất bại. Kiểm tra quyền admin.')
                  } finally {
                    setMeetingSaving(false)
                  }
                }}
              >
                {meetingSaving ? 'Đang tạo...' : 'Tạo'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Upload Doc - Using shared component */}
      <UploadDocumentModal
        isOpen={showDocModal}
        onClose={() => setShowDocModal(false)}
        onSuccess={async () => {
          setShowDocModal(false)
          // Refresh docs list
          const d = await projectsApi.listDocuments(projectId!)
          setDocs(d.documents || [])
        }}
        onUploadProgress={(state) => setUploadToast(state)}
        projectId={projectId}
      />

      {/* Modal: Attach existing doc */}
      {showAttachModal && (
        <div className="modal-overlay" onClick={() => setShowAttachModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 640, maxHeight: '80vh', overflow: 'auto' }}>
            <div className="modal__header">
              <h3 className="modal__title">Chọn tài liệu có sẵn</h3>
            </div>
            <div className="modal__body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <input
                className="form-input"
                placeholder="Tìm kiếm theo tên..."
                value={searchDoc}
                onChange={e => setSearchDoc(e.target.value)}
              />
              {isLoadingDocs ? (
                <div className="form-loading">Đang tải...</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {availableDocs
                    .filter(d => d.title.toLowerCase().includes(searchDoc.toLowerCase()))
                    .map(d => (
                      <div key={d.id} className="tool-card tool-card--compact" style={{ justifyContent: 'space-between' }}>
                        <div>
                          <div className="tool-card__title">{d.title}</div>
                          <div className="tool-card__detail" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            {d.source} • {d.file_type}
                          </div>
                        </div>
                        <button
                          className="btn btn--primary btn--sm"
                          disabled={attaching}
                          onClick={async () => {
                            setAttaching(true)
                            try {
                              await knowledgeApi.update(d.id, { project_id: projectId } as any)
                              const updatedDocs = await projectsApi.listDocuments(projectId!)
                              setDocs(updatedDocs.documents || [])
                              setShowAttachModal(false)
                            } catch (err) {
                              console.error('Attach doc failed', err)
                              alert('Gán tài liệu thất bại.')
                            } finally {
                              setAttaching(false)
                            }
                          }}
                        >
                          {attaching ? 'Đang gán...' : 'Thêm'}
                        </button>
                      </div>
                    ))}
                </div>
              )}
            </div>
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setShowAttachModal(false)}>Đóng</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Edit Project */}
      {showEditModal && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 520 }}>
            <div className="modal__header">
              <h3 className="modal__title">Chỉnh sửa dự án</h3>
            </div>
            <div className="modal__body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="form-group">
                <label className="form-label">Tên dự án *</label>
                <input
                  className="form-input"
                  value={editForm.name}
                  onChange={e => setEditForm({ ...editForm, name: e.target.value })}
                  placeholder="Nhập tên dự án"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Mã dự án</label>
                <input
                  className="form-input"
                  value={editForm.code || ''}
                  onChange={e => setEditForm({ ...editForm, code: e.target.value })}
                  placeholder="VD: PRJ-001"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Mục tiêu dự án</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  value={editForm.objective || ''}
                  onChange={e => setEditForm({ ...editForm, objective: e.target.value })}
                  placeholder="VD: Số hóa quy trình onboarding, giảm thời gian xử lý..."
                />
              </div>
              <div className="form-group">
                <label className="form-label">Mô tả chi tiết</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  value={editForm.description || ''}
                  onChange={e => setEditForm({ ...editForm, description: e.target.value })}
                  placeholder="Scope, milestones, stakeholders..."
                />
              </div>
            </div>
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setShowEditModal(false)}>Hủy</button>
              <button
                className="btn btn--primary"
                disabled={editSaving || !editForm.name.trim()}
                onClick={async () => {
                  if (!projectId) return
                  setEditSaving(true)
                  try {
                    const updated = await projectsApi.update(projectId, {
                      name: editForm.name.trim(),
                      code: editForm.code?.trim(),
                      objective: editForm.objective?.trim(),
                      description: editForm.description?.trim(),
                    } as any)
                    setProject(updated)
                    setShowEditModal(false)
                  } catch (err) {
                    console.error('Update project failed', err)
                    alert('Cập nhật dự án thất bại.')
                  } finally {
                    setEditSaving(false)
                  }
                }}
              >
                {editSaving ? 'Đang lưu...' : 'Lưu'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 'var(--space-xl)' }}>
        <div className="card" style={{ minHeight: 320 }}>
          <div className="card__header">
            <h3 className="card__title">Tài liệu</h3>
            <p className="card__subtitle">{docs.length} tài liệu</p>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn--primary btn--sm" onClick={() => setShowDocModal(true)}>Tải lên</button>
              <button className="btn btn--ghost btn--sm" onClick={() => setShowAttachModal(true)}>Chọn tài liệu có sẵn</button>
            </div>
          </div>
          {docs.length === 0 ? (
            <div className="empty-state">
              <FileText className="empty-state__icon" />
              <h3 className="empty-state__title">Chưa có tài liệu</h3>
            </div>
          ) : (
            <div className="admin-table">
              <div className="admin-table__head" style={{ gridTemplateColumns: '1.5fr 0.8fr 1fr 0.8fr' }}>
                <span>Tiêu đề</span><span>Loại</span><span>File</span><span>Ngày</span>
              </div>
              {docs.map(d => (
                <div key={String(d.id)} className="admin-table__row" style={{ gridTemplateColumns: '1.5fr 0.8fr 1fr 0.8fr' }}>
                  <span>{d.title}</span>
                  <span>{d.file_type || '--'}</span>
                  <span>{d.file_url ? <a href={d.file_url} target="_blank" rel="noreferrer">Xem</a> : '--'}</span>
                  <span>{d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : '--'}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 'var(--space-xl)', marginTop: 'var(--space-lg)' }}>
        <div className="card" style={{ minHeight: 320 }}>
          <div className="card__header">
            <h3 className="card__title">Thành viên</h3>
            <p className="card__subtitle">{displayMembers.length} người</p>
            <button className="btn btn--primary btn--sm" onClick={() => setShowMemberModal(true)}>Thêm thành viên</button>
          </div>
          {displayMembers.length === 0 ? (
            <div className="empty-state">
              <Users className="empty-state__icon" />
              <h3 className="empty-state__title">Chưa có thành viên</h3>
              <p className="empty-state__description">Thêm thành viên từ trang admin nếu cần.</p>
            </div>
          ) : (
            <div className="admin-table">
              <div className="admin-table__head" style={{ gridTemplateColumns: '1.4fr 1fr 0.8fr' }}>
                <span>Tên</span><span>Email</span><span>Role</span>
              </div>
              {displayMembers.map(m => (
                <div key={m.user_id} className="admin-table__row" style={{ gridTemplateColumns: '1.4fr 1fr 0.8fr' }}>
                  <span>{m.display_name || m.user_id}</span>
                  <span>{m.email || '--'}</span>
                  <span>{m.role || '--'}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card" style={{ minHeight: 320 }}>
          <div className="card__header">
            <h3 className="card__title">Cuộc họp</h3>
            <p className="card__subtitle">{meetings.length} cuộc họp</p>
            <button className="btn btn--primary btn--sm" onClick={() => setShowMeetingModal(true)}>Thêm cuộc họp</button>
          </div>
          {meetings.length === 0 ? (
            <div className="empty-state">
              <Calendar className="empty-state__icon" />
              <h3 className="empty-state__title">Chưa có cuộc họp</h3>
            </div>
          ) : (
            <div className="meeting-list">
              {meetings.map(m => (
                <div key={m.id} className="meeting-item">
                  <div className="meeting-item__time">
                    <div className="meeting-item__time-value">
                      {m.start_time ? new Date(m.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--'}
                    </div>
                    <div className="meeting-item__time-period">
                      {m.start_time ? new Date(m.start_time).toLocaleDateString() : 'TBD'}
                    </div>
                  </div>
                  <div className="meeting-item__divider"></div>
                  <div className="meeting-item__content">
                    <div className="meeting-item__title">{m.title}</div>
                    <div className="meeting-item__meta">
                      <span className="meeting-item__meta-item">
                        {m.meeting_type || '--'}
                      </span>
                      {m.location && (
                        <span className="meeting-item__meta-item">
                          {m.location}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className={`meeting-item__phase meeting-item__phase--${m.phase || 'pre'}`}>
                    {m.phase}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Upload Toast Notification */}
      {uploadToast && (
        <div
          style={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            padding: '12px 14px',
            background: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            borderRadius: '12px',
            boxShadow: '0 12px 35px rgba(0,0,0,0.28)',
            border: '1px solid var(--border-strong)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            minWidth: 260,
            zIndex: 9999,
          }}
        >
          {uploadToast.status === 'pending' && <Loader2 size={18} className="animate-spin" />}
          {uploadToast.status === 'success' && <CheckCircle size={18} color="var(--success)" />}
          {uploadToast.status === 'error' && <X size={18} color="var(--danger)" />}
          <div style={{ fontSize: 13, lineHeight: 1.5 }}>{uploadToast.message}</div>
          {uploadToast.status !== 'pending' && (
            <button
              style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}
              onClick={() => setUploadToast(null)}
            >
              <X size={14} />
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default ProjectDetail
