import { useState } from 'react'

type CreateProjectModalProps = {
  open: boolean
  loading?: boolean
  onClose: () => void
  onSubmit: (data: { name: string; code?: string; scope?: string; description?: string; objective?: string }) => void
}

/**
 * Create Project modal reusing the same visual language/layout as the Create Meeting modal.
 */
const CreateProjectModal = ({ open, loading, onClose, onSubmit }: CreateProjectModalProps) => {
  const [form, setForm] = useState({ name: '', code: '', scope: '', description: '', objective: '' })

  if (!open) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 560, maxHeight: '80vh', overflowY: 'auto' }}>
        <div className="modal__header">
          <h3 className="modal__title">Tạo dự án</h3>
          <button className="modal__close" onClick={onClose}>×</button>
        </div>

        <div className="modal__body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="form-group">
            <label className="form-label">Tên dự án *</label>
            <input
              className="form-input"
              placeholder="VD: LPB – Digital Onboarding"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Mã dự án</label>
            <input
              className="form-input"
              placeholder="PROJ-001"
              value={form.code}
              onChange={e => setForm({ ...form, code: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Phạm vi / Stakeholders</label>
            <input
              className="form-input"
              placeholder="PMO, Tech, Biz; related Org/Dept"
              value={form.scope}
              onChange={e => setForm({ ...form, scope: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Mục tiêu dự án (Objectives)</label>
            <textarea
              className="form-textarea"
              rows={3}
              placeholder="VD: Số hóa quy trình onboarding, giảm thời gian xử lý từ 3 ngày xuống 1 ngày..."
              value={form.objective}
              onChange={e => setForm({ ...form, objective: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Mô tả chi tiết</label>
            <textarea
              className="form-textarea"
              rows={3}
              placeholder="Scope, milestones, key stakeholders, deliverables..."
              value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
            />
          </div>
        </div>

        <div className="modal__footer">
          <button className="btn btn--ghost" onClick={onClose}>Hủy</button>
          <button
            className="btn btn--primary"
            disabled={loading || !form.name.trim()}
            onClick={() => onSubmit({
              name: form.name.trim(),
              code: form.code.trim() || undefined,
              scope: form.scope.trim() || undefined,
              objective: form.objective.trim() || undefined,
              description: form.description.trim() || undefined,
            })}
          >
            {loading ? 'Đang tạo...' : 'Tạo dự án'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default CreateProjectModal
