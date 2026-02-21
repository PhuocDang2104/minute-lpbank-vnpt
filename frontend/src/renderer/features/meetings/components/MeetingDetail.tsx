import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Clock,
  AlertCircle,
  RefreshCw,
  Video,
  Edit2,
  Trash2,
  X,
  Save,
} from 'lucide-react';
import { meetingsApi } from '../../../lib/api/meetings';
import { sessionsApi } from '../../../lib/api/sessions';
import type { MeetingWithParticipants, MeetingUpdate } from '../../../shared/dto/meeting';
import { getMeetingTypeLabel } from '../../../shared/dto/meeting';
import { USE_API } from '../../../config/env';
import { useChatContext } from '../../../contexts/ChatContext';
import { useLocaleText } from '../../../i18n/useLocaleText';

// Tab Components
import PostMeetTabV2 from './tabs/PostMeetTab';

export const MeetingDetail = () => {
  const { lt, language, dateLocale, timeLocale } = useLocaleText();
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();

  const [meeting, setMeeting] = useState<MeetingWithParticipants | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [streamSessionId, setStreamSessionId] = useState<string | null>(null);
  const [audioIngestToken, setAudioIngestToken] = useState('');
  const [sessionInitError, setSessionInitError] = useState<string | null>(null);
  const [isInitSessionLoading, setIsInitSessionLoading] = useState(false);
  const { setOverride, clearOverride } = useChatContext();

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    session_date: '',
    start_time: '',
    end_time: '',
    is_instant: false,
  });
  const [isSaving, setIsSaving] = useState(false);

  // Delete confirmation
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchMeeting = useCallback(async () => {
    if (!meetingId) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await meetingsApi.get(meetingId);
      setMeeting(data);
      setStreamSessionId(data.id);
    } catch (err) {
      console.error('Failed to fetch meeting:', err);
      setError(lt('Không thể tải thông tin cuộc họp', 'Unable to load meeting details'));
    } finally {
      setIsLoading(false);
    }
  }, [meetingId]);

  useEffect(() => {
    fetchMeeting();
  }, [fetchMeeting]);

  useEffect(() => {
    if (!meeting) return;
    setOverride({
      scope: 'meeting',
      meetingId: meeting.id,
      phase: 'post',
      title: meeting.title,
    });
  }, [meeting?.id, meeting?.title, setOverride]);

  useEffect(() => {
    return () => clearOverride();
  }, [clearOverride]);

  const openMeetingDock = (override?: { sessionId?: string; token?: string }) => {
    if (!meeting) return;
    const params = new URLSearchParams();
    const session = override?.sessionId || streamSessionId || meeting.id;
    if (session) params.set('session', session);
    params.set('platform', 'gmeet');
    const token = override?.token || audioIngestToken;
    if (token) params.set('token', token);
    const qs = params.toString();
    navigate(`/app/meetings/${meeting.id}/dock${qs ? `?${qs}` : ''}`);
  };

  const handleInitRealtimeSession = async () => {
    if (!USE_API) {
      setShowJoinModal(false);
      return;
    }
    const desiredSessionId = streamSessionId || meeting?.id;
    if (!desiredSessionId) return;

    setIsInitSessionLoading(true);
    setSessionInitError(null);
    try {
      const res = await sessionsApi.create({
        session_id: desiredSessionId,
        language_code: 'vi-VN',
        target_sample_rate_hz: 16000,
        audio_encoding: 'PCM_S16LE',
        channels: 1,
        realtime: true,
        interim_results: true,
        enable_word_time_offsets: true,
      });
      const sessionId = res.session_id;
      setStreamSessionId(sessionId);

      let token = audioIngestToken.trim();
      if (!token) {
        const tokenRes = await sessionsApi.registerSource(sessionId);
        token = tokenRes.audio_ingest_token;
      }
      setAudioIngestToken(token);
      setShowJoinModal(false);
      openMeetingDock({ sessionId, token });
    } catch (err) {
      console.error('Failed to init realtime session:', err);
      setSessionInitError(lt('Không thể khởi tạo realtime session. Kiểm tra backend /api/v1/sessions.', 'Unable to initialize realtime session. Check backend /api/v1/sessions.'));
    } finally {
      setIsInitSessionLoading(false);
    }
  };

  // Open edit modal with current meeting data
  const handleOpenEdit = () => {
    if (!meeting) return;

    const formatDateInput = (dateStr: string | null | undefined) => {
      if (!dateStr) return '';
      return String(dateStr).slice(0, 10);
    };
    const formatDateFromIso = (dateStr: string | null | undefined) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      if (Number.isNaN(date.getTime())) return '';
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };
    const formatTimeInput = (dateStr: string | null | undefined) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      if (Number.isNaN(date.getTime())) return '';
      return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    };
    const nextSessionDate = formatDateInput(meeting.session_date) || formatDateFromIso(meeting.start_time);

    setEditForm({
      title: meeting.title || '',
      description: meeting.description || '',
      session_date: nextSessionDate,
      start_time: formatTimeInput(meeting.start_time),
      end_time: formatTimeInput(meeting.end_time),
      is_instant: !nextSessionDate,
    });
    setShowEditModal(true);
  };

  // Save edited meeting
  const handleSaveEdit = async () => {
    if (!meetingId) return;

    const title = editForm.title.trim();
    if (!title) {
      alert(lt('Vui long nhap tieu de phien.', 'Please enter the session title.'));
      return;
    }

    let startIso: string | null = null;
    let endIso: string | null = null;
    if (!editForm.is_instant) {
      if (!editForm.session_date || !editForm.start_time || !editForm.end_time) {
        alert(lt('Vui long dien du ngay va gio.', 'Please provide session date and time.'));
        return;
      }
      const startDate = new Date(`${editForm.session_date}T${editForm.start_time}`);
      const endDate = new Date(`${editForm.session_date}T${editForm.end_time}`);
      if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
        alert(lt('Ngay gio khong hop le.', 'Invalid date/time.'));
        return;
      }
      if (endDate.getTime() <= startDate.getTime()) {
        alert(lt('Gio ket thuc phai sau gio bat dau.', 'End time must be after start time.'));
        return;
      }
      startIso = startDate.toISOString();
      endIso = endDate.toISOString();
    }

    setIsSaving(true);
    try {
      const updateData: MeetingUpdate = {
        title,
        description: editForm.description || undefined,
        session_date: editForm.is_instant
          ? null
          : (editForm.session_date || null),
        start_time: editForm.is_instant ? null : startIso,
        end_time: editForm.is_instant ? null : endIso,
      };

      await meetingsApi.update(meetingId, updateData);
      setShowEditModal(false);
      fetchMeeting();
    } catch (err) {
      console.error('Failed to update meeting:', err);
      alert(lt('Không thể cập nhật cuộc họp', 'Unable to update meeting'));
    } finally {
      setIsSaving(false);
    }
  };

  // Delete meeting
  const handleDelete = async () => {
    if (!meetingId) return;

    setIsDeleting(true);
    try {
      await meetingsApi.delete(meetingId);
      navigate('/app/meetings');
    } catch (err) {
      console.error('Failed to delete meeting:', err);
      alert(lt('Không thể xóa cuộc họp', 'Unable to delete meeting'));
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  if (isLoading) {
    return (
      <div className="meeting-detail-loading">
        <div className="spinner" style={{ width: 40, height: 40 }}></div>
        <p>{lt('Đang tải thông tin cuộc họp...', 'Loading meeting details...')}</p>
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="empty-state">
        <AlertCircle className="empty-state__icon" />
        <h3 className="empty-state__title">{error || lt('Không tìm thấy cuộc họp', 'Meeting not found')}</h3>
        <button className="btn btn--secondary" onClick={() => navigate('/app/meetings')}>
          {lt('Quay lại', 'Back')}
        </button>
      </div>
    );
  }

  const startTime = meeting.start_time ? new Date(meeting.start_time) : null;
  const sessionDateRaw = meeting.session_date || (meeting.start_time ? meeting.start_time.slice(0, 10) : null);
  const sessionDate = sessionDateRaw ? new Date(`${sessionDateRaw}T00:00:00`) : null;
  const sessionIdValue = streamSessionId || meeting.id;

  return (
    <div className="meeting-detail-v2">
      {/* Compact Header */}
      <header className="meeting-detail-v2__header">
        <div className="meeting-detail-v2__header-left">
          <button
            className="btn btn--ghost btn--icon btn--sm"
            style={{ padding: '6px', width: '32px', height: '32px' }}
            onClick={() => navigate('/app/meetings')}
          >
            <ArrowLeft size={16} />
          </button>
          <div className="meeting-detail-v2__header-info">
            <div className="meeting-detail-v2__header-badges">
              <span className="badge badge--neutral">{getMeetingTypeLabel(meeting.meeting_type, language)}</span>
            </div>
            <h1 className="meeting-detail-v2__title">{meeting.title}</h1>
          </div>
        </div>

        <div className="meeting-detail-v2__header-right">
          <div className="meeting-detail-v2__meta-compact">
            {(sessionDate || startTime) && (
              <>
                <span className="meta-item">
                  <Calendar size={14} />
                  {(sessionDate || startTime)?.toLocaleDateString(dateLocale, { day: '2-digit', month: '2-digit' })}
                </span>
                {startTime && (
                  <span className="meta-item">
                    <Clock size={14} />
                    {startTime.toLocaleTimeString(timeLocale, { hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </>
            )}
          </div>

          <div className="meeting-detail-v2__actions" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {/* Utility */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                className="btn btn--ghost btn--icon btn--sm"
                style={{ padding: '6px', width: '32px', height: '32px' }}
                onClick={fetchMeeting}
                title={lt('Làm mới', 'Refresh')}
              >
                <RefreshCw size={16} />
              </button>
              {meeting.phase === 'pre' && (
                <button
                  className="btn btn--ghost btn--icon btn--sm"
                  style={{ padding: '6px', width: '32px', height: '32px' }}
                  onClick={handleOpenEdit}
                  title={lt('Chỉnh sửa', 'Edit')}
                >
                  <Edit2 size={16} />
                </button>
              )}
              {meeting.phase === 'pre' && (
                <button
                  className="btn btn--ghost btn--icon btn--sm"
                  style={{ padding: '6px', width: '32px', height: '32px', color: 'var(--error)' }}
                  onClick={() => setShowDeleteConfirm(true)}
                  title={lt('Xóa cuộc họp', 'Delete meeting')}
                >
                  <Trash2 size={16} />
                </button>
              )}
            </div>

            {/* Navigation / join */}
            {!meeting.recording_url && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  className="btn btn--secondary"
                  onClick={() => setShowJoinModal(true)}
                  title={lt('Mở dock để ghi realtime', 'Open dock for realtime capture')}
                >
                  <Video size={16} />
                  {lt('Live Record', 'Live Record')}
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Summary only */}
      <main className="meeting-detail-v2__content">
        <PostMeetTabV2
          meeting={meeting}
          onRefresh={fetchMeeting}
        />
      </main>

      {/* Edit Modal */}
      {showEditModal && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <div className="modal__header">
              <h2 className="modal__title">
                <Edit2 size={20} />
                {lt('Chỉnh sửa phiên', 'Edit session')}
              </h2>
              <button className="btn btn--ghost btn--icon" onClick={() => setShowEditModal(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="modal__body">
              <div className="form-group">
                <label className="form-label">{lt('Tiêu đề phiên', 'Session title')}</label>
                <input
                  type="text"
                  className="form-input"
                  value={editForm.title}
                  onChange={e => setEditForm({ ...editForm, title: e.target.value })}
                  placeholder={lt('Nhập tiêu đề...', 'Enter title...')}
                />
              </div>

              <div className="form-group">
                <label className="form-label">{lt('Mô tả', 'Description')}</label>
                <textarea
                  className="form-input"
                  value={editForm.description}
                  onChange={e => setEditForm({ ...editForm, description: e.target.value })}
                  placeholder={lt('Nhập mô tả...', 'Enter description...')}
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label className="form-label">{lt('Ngay dien ra', 'Session date')}</label>
                <input
                  type="date"
                  className="form-input"
                  value={editForm.session_date}
                  onChange={e => setEditForm({ ...editForm, session_date: e.target.value })}
                  disabled={editForm.is_instant}
                />
                <label className="checkbox-label" style={{ marginTop: 10, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                  <input
                    type="checkbox"
                    checked={editForm.is_instant}
                    onChange={(e) => {
                      const checked = e.target.checked;
                      const now = new Date();
                      const plusHour = new Date(now.getTime() + (60 * 60 * 1000));
                      const fallbackDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
                      const fallbackStart = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
                      const fallbackEnd = `${String(plusHour.getHours()).padStart(2, '0')}:${String(plusHour.getMinutes()).padStart(2, '0')}`;
                      setEditForm(prev => ({
                        ...prev,
                        is_instant: checked,
                        session_date: checked ? '' : (prev.session_date || fallbackDate),
                        start_time: checked ? '' : (prev.start_time || fallbackStart),
                        end_time: checked ? '' : (prev.end_time || fallbackEnd),
                      }));
                    }}
                  />
                  <span>{lt('Phien tuc thi (N/A)', 'Instant session (N/A)')}</span>
                </label>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-base)' }}>
                <div className="form-group">
                  <label className="form-label">
                    <Clock size={14} style={{ marginRight: '6px' }} />
                    {lt('Thời gian bắt đầu', 'Start time')}
                  </label>
                  <input
                    type="time"
                    className="form-input"
                    value={editForm.start_time}
                    onChange={e => setEditForm({ ...editForm, start_time: e.target.value })}
                    disabled={editForm.is_instant}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    <Clock size={14} style={{ marginRight: '6px' }} />
                    {lt('Thời gian kết thúc', 'End time')}
                  </label>
                  <input
                    type="time"
                    className="form-input"
                    value={editForm.end_time}
                    onChange={e => setEditForm({ ...editForm, end_time: e.target.value })}
                    disabled={editForm.is_instant}
                  />
                </div>
              </div>
            </div>

            <div className="modal__footer">
              <button className="btn btn--secondary" onClick={() => setShowEditModal(false)}>
                {lt('Hủy', 'Cancel')}
              </button>
              <button
                className="btn btn--primary"
                onClick={handleSaveEdit}
                disabled={isSaving || !editForm.title}
              >
                {isSaving ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    {lt('Đang lưu...', 'Saving...')}
                  </>
                ) : (
                  <>
                    <Save size={16} />
                    {lt('Lưu thay đổi', 'Save changes')}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="modal-overlay" onClick={() => setShowDeleteConfirm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px' }}>
            <div className="modal__header">
              <h2 className="modal__title" style={{ color: 'var(--error)' }}>
                <Trash2 size={20} />
                {lt('Xóa cuộc họp', 'Delete meeting')}
              </h2>
              <button className="btn btn--ghost btn--icon" onClick={() => setShowDeleteConfirm(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="modal__body">
              <p style={{ marginBottom: 'var(--space-base)' }}>
                {lt('Bạn có chắc chắn muốn xóa cuộc họp này?', 'Are you sure you want to delete this meeting?')}
              </p>
              <div className="card" style={{ background: 'var(--bg-elevated)', padding: 'var(--space-base)' }}>
                <strong>{meeting.title}</strong>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {startTime?.toLocaleString(dateLocale)}
                </div>
              </div>
              <p style={{ marginTop: 'var(--space-base)', fontSize: '13px', color: 'var(--text-muted)' }}>
                {lt('Hành động này không thể hoàn tác.', 'This action cannot be undone.')}
              </p>
            </div>

            <div className="modal__footer">
              <button className="btn btn--secondary" onClick={() => setShowDeleteConfirm(false)}>
                {lt('Hủy', 'Cancel')}
              </button>
              <button
                className="btn btn--error"
                onClick={handleDelete}
                disabled={isDeleting}
                style={{ background: 'var(--error)' }}
              >
                {isDeleting ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    {lt('Đang xóa...', 'Deleting...')}
                  </>
                ) : (
                  <>
                    <Trash2 size={16} />
                    {lt('Xóa cuộc họp', 'Delete meeting')}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Join meeting modal */}
      {showJoinModal && (
        <div className="modal-overlay" onClick={() => setShowJoinModal(false)}>
          <div className="modal join-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '640px' }}>
            <div className="modal__header join-modal__header">
              <div className="join-modal__header-left">
                <div className="join-modal__icon">
                  <Video size={18} />
                </div>
                <div>
                  <h2 className="modal__title">Minute Capture</h2>
                  <p className="join-modal__subtitle">{lt('Chọn tab Google khác để capture.', 'Select another Google tab to capture.')}</p>
                </div>
              </div>
              <button className="btn btn--ghost btn--icon" onClick={() => setShowJoinModal(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal__body join-modal__body">
              <div className="join-modal__notice">
                {lt('Chọn tab Google khác để capture.', 'Select another Google tab to capture.')}
              </div>
              <div className="form-group">
                <label className="form-label">{lt('Stream ID', 'Stream ID')}</label>
                <input
                  type="text"
                  className="form-input"
                  value={sessionIdValue}
                  onChange={e => setStreamSessionId(e.target.value)}
                  placeholder={lt('session_id (mặc định: meeting.id)', 'session_id (default: meeting.id)')}
                />
                <p className="form-hint">{lt('Stream ID được dùng cho realtime transcript.', 'Stream ID is used for realtime transcript.')}</p>
              </div>
              {sessionInitError && (
                <div className="join-modal__alert join-modal__alert--error">
                  {sessionInitError}
                </div>
              )}
            </div>
            <div className="modal__footer join-modal__footer">
              <button className="btn btn--secondary" onClick={() => setShowJoinModal(false)}>
                {lt('Đóng', 'Close')}
              </button>
              <button
                className="btn btn--primary"
                onClick={handleInitRealtimeSession}
                disabled={!sessionIdValue}
              >
                {isInitSessionLoading ? lt('Đang kết nối...', 'Connecting...') : lt('Kết nối', 'Connect')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MeetingDetail;

