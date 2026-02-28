import { useState } from 'react';
import { Calendar, Loader2, Users } from 'lucide-react';
import type { MeetingCreate, MeetingType } from '../../../shared/dto/meeting';
import { getMeetingTypeLabel } from '../../../shared/dto/meeting';
import { meetingsApi } from '../../../lib/api/meetings';
import { useLocaleText } from '../../../i18n/useLocaleText';

interface CreateMeetingFormProps {
  onSuccess: (meetingId: string) => void;
  onCancel: () => void;
  projectId?: string;
}

interface FormData {
  title: string;
  description: string;
  meeting_type: MeetingType;
  project_id: string;
  session_date: string;
  start_time: string;
  end_time: string;
  is_instant: boolean;
}

interface FormErrors {
  title?: string;
  session_date?: string;
  start_time?: string;
  end_time?: string;
}

const PROJECT_OPTIONS = [
  { value: '', label: 'None' },
  { value: 'p0000001-0000-0000-0000-000000000001', label: 'Core Banking Modernization' },
  { value: 'p0000002-0000-0000-0000-000000000002', label: 'Mobile Banking 3.0' },
  { value: 'p0000003-0000-0000-0000-000000000003', label: 'Loan Origination System' },
  { value: 'p0000004-0000-0000-0000-000000000004', label: 'KYC Enhancement' },
];

type Step = 'selection' | 'details' | 'creating';

const formatDateInput = (value: Date) => value.toISOString().slice(0, 10);
const formatTimeInput = (value: Date) => value.toTimeString().slice(0, 5);

const buildDefaultFormData = (
  type: MeetingType,
  language: 'vi' | 'en',
  projectId?: string,
): FormData => {
  const now = new Date();
  const end = new Date(now.getTime() + 60 * 60 * 1000);
  const locale = language === 'en' ? 'en-US' : 'vi-VN';
  const label = getMeetingTypeLabel(type, language);

  return {
    title: `${label} - ${now.toLocaleDateString(locale)} ${now.toLocaleTimeString(locale, {
      hour: '2-digit',
      minute: '2-digit',
    })}`,
    description: '',
    meeting_type: type,
    project_id: projectId || '',
    session_date: formatDateInput(now),
    start_time: formatTimeInput(now),
    end_time: formatTimeInput(end),
    is_instant: false,
  };
};

export const CreateMeetingForm = ({ onSuccess, onCancel, projectId }: CreateMeetingFormProps) => {
  const { lt, language } = useLocaleText();

  const [step, setStep] = useState<Step>('selection');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});
  const [formData, setFormData] = useState<FormData>(() => buildDefaultFormData('project_meeting', language, projectId));

  const handleSelectType = (type: MeetingType) => {
    setError(null);
    setErrors({});
    setFormData(buildDefaultFormData(type, language, projectId));
    setStep('details');
  };

  const handleChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const validateForm = (): FormErrors => {
    const nextErrors: FormErrors = {};

    if (!formData.title.trim()) {
      nextErrors.title = lt('Vui lòng nhập tiêu đề phiên.', 'Please enter a session title.');
    }

    if (!formData.is_instant) {
      if (!formData.session_date) {
        nextErrors.session_date = lt('Vui lòng chọn ngày diễn ra.', 'Please select the session date.');
      }
      if (!formData.start_time) {
        nextErrors.start_time = lt('Vui lòng chọn giờ bắt đầu.', 'Please select a start time.');
      }
      if (!formData.end_time) {
        nextErrors.end_time = lt('Vui lòng chọn giờ kết thúc.', 'Please select an end time.');
      }

      if (!nextErrors.session_date && !nextErrors.start_time && !nextErrors.end_time) {
        const start = new Date(`${formData.session_date}T${formData.start_time}`);
        const end = new Date(`${formData.session_date}T${formData.end_time}`);
        if (end.getTime() <= start.getTime()) {
          nextErrors.end_time = lt('Giờ kết thúc phải sau giờ bắt đầu.', 'End time must be after start time.');
        }
      }
    }

    return nextErrors;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const nextErrors = validateForm();
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setIsSubmitting(true);
    setStep('creating');

    try {
      const start = formData.is_instant || !formData.session_date || !formData.start_time
        ? undefined
        : new Date(`${formData.session_date}T${formData.start_time}`);
      const end = formData.is_instant || !formData.session_date || !formData.end_time
        ? undefined
        : new Date(`${formData.session_date}T${formData.end_time}`);
      const payload: MeetingCreate = {
        title: formData.title.trim(),
        description: formData.description.trim() || undefined,
        meeting_type: formData.meeting_type,
        session_date: formData.is_instant ? undefined : (formData.session_date || undefined),
        start_time: start?.toISOString(),
        end_time: end?.toISOString(),
      };

      const selectedProjectId = projectId || formData.project_id;
      if (selectedProjectId) {
        payload.project_id = selectedProjectId;
      }

      const response = await meetingsApi.create(payload);
      onSuccess(response.id);
    } catch (err) {
      console.error('Failed to create session:', err);
      setError(lt('Không thể tạo phiên. Vui lòng thử lại.', 'Unable to create session. Please try again.'));
      setStep('details');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (step === 'creating') {
    return (
      <div className="mode-selection-container" style={{ textAlign: 'center', padding: '60px 0' }}>
        <Loader2 size={48} className="spinner" style={{ animation: 'spin 1s linear infinite', color: '#6366f1', margin: '0 auto 24px' }} />
        <h3 style={{ fontSize: 18, color: 'var(--text-primary)' }}>{lt('Đang tạo phiên...', 'Creating session...')}</h3>
        <p style={{ color: 'var(--text-secondary)', marginTop: 8 }}>{lt('Vui lòng đợi trong giây lát', 'Please wait a moment')}</p>
      </div>
    );
  }

  if (step === 'selection') {
    return (
      <div className="mode-selection-container" style={{ textAlign: 'center', padding: '20px 0' }}>
        <h3 style={{ marginBottom: 8, fontSize: 18, color: 'var(--text-primary)' }}>
          {lt('Bước 1: Chọn loại phiên', 'Step 1: Choose session type')}
        </h3>
        <p style={{ marginBottom: 24, fontSize: 13, color: 'var(--text-secondary)' }}>
          {lt('Sau khi chọn, bạn sẽ điền thông tin trước khi tạo phiên.', 'After selecting, you will fill session details before creation.')}
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <button
            type="button"
            className="mode-card"
            onClick={() => handleSelectType('project_meeting')}
            disabled={isSubmitting}
            style={{
              padding: '30px 20px',
              border: '2px solid var(--border)',
              borderRadius: '12px',
              background: 'var(--bg-secondary)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{
              width: 60,
              height: 60,
              borderRadius: '50%',
              background: '#e0e7ff',
              color: '#4338ca',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Users size={32} />
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                {lt('Dự án / Công việc', 'Project / Work')}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                {lt('Phiên làm việc cho đội nhóm và dự án', 'Working session for teams and projects')}
              </div>
            </div>
          </button>

          <button
            type="button"
            className="mode-card"
            onClick={() => handleSelectType('study_session')}
            disabled={isSubmitting}
            style={{
              padding: '30px 20px',
              border: '2px solid var(--border)',
              borderRadius: '12px',
              background: 'var(--bg-secondary)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{
              width: 60,
              height: 60,
              borderRadius: '50%',
              background: '#f3e8ff',
              color: '#7e22ce',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Calendar size={32} />
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                {lt('Lớp học online', 'Online Class')}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                {lt('Phiên dựa trên kịch bản học tập', 'Session tailored for study workflow')}
              </div>
            </div>
          </button>
        </div>

        <div style={{ marginTop: 32, display: 'flex', justifyContent: 'center' }}>
          <button type="button" className="btn btn--ghost" onClick={onCancel} disabled={isSubmitting}>
            {lt('Hủy bỏ', 'Cancel')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 6, fontSize: 17, color: 'var(--text-primary)' }}>
          {lt('Bước 2: Điền thông tin phiên', 'Step 2: Fill session details')}
        </h3>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          {lt('Hoàn tất thông tin này trước khi tạo session.', 'Complete these fields before creating the session.')}
        </p>
      </div>

      {error && <div className="form-error" style={{ marginBottom: 12 }}>{error}</div>}

      <div className="form-group">
        <label className="form-label">{lt('Loại phiên', 'Session type')}</label>
        <select
          className="form-select"
          value={formData.meeting_type}
          onChange={(e) => handleChange('meeting_type', e.target.value as MeetingType)}
          disabled={isSubmitting}
        >
          <option value="project_meeting">{getMeetingTypeLabel('project_meeting', language)}</option>
          <option value="study_session">{getMeetingTypeLabel('study_session', language)}</option>
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">{lt('Tiêu đề phiên *', 'Session title *')}</label>
        <input
          type="text"
          className={`form-input ${errors.title ? 'form-input--error' : ''}`}
          value={formData.title}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder={lt('Nhập tiêu đề phiên', 'Enter session title')}
          disabled={isSubmitting}
        />
        {errors.title && <span className="form-field__error">{errors.title}</span>}
      </div>

      <div className="form-group">
        <label className="form-label">{lt('Mô tả', 'Description')}</label>
        <textarea
          className="form-textarea"
          rows={3}
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          placeholder={lt('Nhập mô tả ngắn', 'Enter a short description')}
          disabled={isSubmitting}
        />
      </div>

      {!projectId && (
        <div className="form-group">
          <label className="form-label">{lt('Dự án (tùy chọn)', 'Project (optional)')}</label>
          <select
            className="form-select"
            value={formData.project_id}
            onChange={(e) => handleChange('project_id', e.target.value)}
            disabled={isSubmitting}
          >
            {PROJECT_OPTIONS.map(item => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="form-group">
        <label className="form-label">{lt('Ngày diễn ra', 'Session date')}</label>
        <input
          type="date"
          className={`form-input ${errors.session_date ? 'form-input--error' : ''}`}
          value={formData.session_date}
          onChange={(e) => handleChange('session_date', e.target.value)}
          disabled={isSubmitting || formData.is_instant}
        />
        {errors.session_date && <span className="form-field__error">{errors.session_date}</span>}
        <label className="checkbox-label" style={{ marginTop: 10, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <input
            type="checkbox"
            checked={formData.is_instant}
            onChange={(e) => {
              const checked = e.target.checked;
              setFormData(prev => ({
                ...prev,
                is_instant: checked,
                session_date: checked ? '' : (prev.session_date || formatDateInput(new Date())),
              }));
            }}
            disabled={isSubmitting}
          />
          <span>{lt('Phiên tức thì (không có ngày diễn ra - N/A)', 'Instant session (no session date - N/A)')}</span>
        </label>
      </div>

      {!formData.is_instant && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-base)' }}>
          <div className="form-group">
            <label className="form-label">{lt('Giờ bắt đầu *', 'Start time *')}</label>
            <input
              type="time"
              className={`form-input ${errors.start_time ? 'form-input--error' : ''}`}
              value={formData.start_time}
              onChange={(e) => handleChange('start_time', e.target.value)}
              disabled={isSubmitting}
            />
            {errors.start_time && <span className="form-field__error">{errors.start_time}</span>}
          </div>
          <div className="form-group">
            <label className="form-label">{lt('Giờ kết thúc *', 'End time *')}</label>
            <input
              type="time"
              className={`form-input ${errors.end_time ? 'form-input--error' : ''}`}
              value={formData.end_time}
              onChange={(e) => handleChange('end_time', e.target.value)}
              disabled={isSubmitting}
            />
            {errors.end_time && <span className="form-field__error">{errors.end_time}</span>}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginTop: 20 }}>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => setStep('selection')}
          disabled={isSubmitting}
        >
          {lt('Quay lại', 'Back')}
        </button>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" className="btn btn--secondary" onClick={onCancel} disabled={isSubmitting}>
            {lt('Hủy', 'Cancel')}
          </button>
          <button type="submit" className="btn btn--primary" disabled={isSubmitting}>
            {lt('Tạo session', 'Create session')}
          </button>
        </div>
      </div>
    </form>
  );
};

export default CreateMeetingForm;

