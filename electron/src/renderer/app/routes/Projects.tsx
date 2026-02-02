import { useEffect, useState } from 'react'
import { PlusCircle, RefreshCw, FolderOpen } from 'lucide-react'
import { Link } from 'react-router-dom'
import { adminListProjects, adminCreateProject } from '../../lib/api/admin'
import { Project } from '../../shared/dto/project'
import { getStoredUser } from '../../lib/api/auth'
import { useLanguage } from '../../contexts/LanguageContext'
import CreateProjectModal from './Projects/CreateProjectModal'

const Projects = () => {
  const { t } = useLanguage()
  const user = getStoredUser()
  const isAdmin = (user?.role || '').toLowerCase() === 'admin'

  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState<{ name: string; code?: string; scope?: string; description?: string; objective?: string }>({
    name: '',
    code: '',
    scope: '',
    description: '',
    objective: '',
  })
  const [showModal, setShowModal] = useState(false)

  const loadProjects = async () => {
    setLoading(true)
    try {
      const res = await adminListProjects({ limit: 200 })
      setProjects(res.projects)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (payload?: { name: string; code?: string; scope?: string; description?: string; objective?: string }) => {
    const data = payload || form
    if (!data.name.trim()) return
    setCreating(true)
    try {
      await adminCreateProject({
        name: data.name.trim(),
        code: data.code?.trim() || undefined,
        description: data.description?.trim() || undefined,
        objective: data.objective?.trim() || undefined,
        scope: data.scope?.trim() || undefined,
      } as any)
      setForm({ name: '', code: '', scope: '', description: '', objective: '' })
      await loadProjects()
      setShowModal(false)
    } finally {
      setCreating(false)
    }
  }

  useEffect(() => {
    if (isAdmin) {
      loadProjects()
    }
  }, [isAdmin])

  if (!isAdmin) {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <p className="page-header__eyebrow">Projects</p>
            <h1 className="page-header__title">Quản lý dự án</h1>
            <p className="page-header__subtitle">Chỉ admin mới xem được danh sách dự án.</p>
          </div>
        </div>
        <div className="card">
          <p>Bạn cần quyền admin để truy cập trang này.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="page-header__eyebrow">Projects</p>
          <h1 className="page-header__title">Quản lý dự án</h1>
          <p className="page-header__subtitle">
            Tạo mới, xem danh sách dự án và mô tả ngắn gọn.
          </p>
        </div>
        <div className="page-header__actions">
          <button className="btn btn-outline" onClick={loadProjects} disabled={loading}>
            <RefreshCw size={16} style={{ marginRight: 6 }} /> {loading ? t('common.loading') : 'Tải lại'}
          </button>
          <button className="btn btn--primary" onClick={() => setShowModal(true)}>
            <PlusCircle size={16} style={{ marginRight: 6 }} /> Tạo dự án
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card__header">
          <h3 className="card__title">Danh sách dự án</h3>
          <p className="card__subtitle">{projects.length} dự án</p>
        </div>
        {projects.length === 0 ? (
          <div className="empty-state">
            <FolderOpen className="empty-state__icon" />
            <h3 className="empty-state__title">Chưa có dự án nào</h3>
            <p className="empty-state__description">Bấm "Tạo dự án" để thêm dự án mới.</p>
          </div>
        ) : (
          <div className="meeting-list">
            {projects.map(p => (
              <Link key={p.id} to={`/app/projects/${p.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                <div className="meeting-item">
                  <div className="meeting-item__content" style={{ width: '100%' }}>
                    <div className="meeting-item__title">{p.name}</div>
                    <div className="meeting-item__meta">
                      <span className="meeting-item__meta-item">
                        Mã: {p.code || '--'}
                      </span>
                      <span className="meeting-item__meta-item">
                        {p.created_at ? new Date(p.created_at).toLocaleDateString() : '--'}
                      </span>
                    </div>
                    {p.description && (
                      <div className="meeting-item__meta" style={{ marginTop: 6 }}>
                        <span className="meeting-item__meta-item">{p.description}</span>
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      <CreateProjectModal
        open={showModal}
        loading={creating}
        onClose={() => setShowModal(false)}
        onSubmit={(data) => {
          setForm(data)
          handleCreate(data)
        }}
      />
    </div>
  )
}

export default Projects
