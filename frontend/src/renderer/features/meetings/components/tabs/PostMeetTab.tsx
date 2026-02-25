/**
 * Post-Meeting Tab V2 - Notion AI Style
 * Editable, clean, professional meeting minutes editor
 */
import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import {
  Sparkles,
  Edit3,
  Check,
  X,
  Copy,
  Download,
  Mail,
  ChevronDown,
  ChevronRight,
  CheckCircle,
  Clock,
  Trash2,
} from 'lucide-react';
import type { MeetingWithParticipants } from '../../../../shared/dto/meeting';
import { minutesApi, type MeetingMinutes } from '../../../../lib/api/minutes';
import { itemsApi, type ActionItem, type DecisionItem, type RiskItem } from '../../../../lib/api/items';
import { transcriptsApi } from '../../../../lib/api/transcripts';
import { meetingsApi } from '../../../../lib/api/meetings';

interface PostMeetTabV2Props {
  meeting: MeetingWithParticipants;
  onRefresh: () => void;
}

type ActionPriority = 'low' | 'medium' | 'high' | 'critical';
type ActionStatus = 'proposed' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled';

type DecisionStatus = 'proposed' | 'confirmed' | 'revised';

type RiskSeverity = 'low' | 'medium' | 'high' | 'critical';
type RiskStatus = 'identified' | 'proposed' | 'confirmed' | 'in_progress' | 'mitigated' | 'closed';

const ACTION_PRIORITY_LABEL: Record<ActionPriority, string> = {
  low: 'Thấp',
  medium: 'Trung bình',
  high: 'Cao',
  critical: 'Khẩn cấp',
};

const DECISION_STATUS_LABEL: Record<DecisionStatus, string> = {
  proposed: 'Đề xuất',
  confirmed: 'Đã xác nhận',
  revised: 'Đã chỉnh sửa',
};

const RISK_STATUS_LABEL: Record<RiskStatus, string> = {
  identified: 'Đã nhận diện',
  proposed: 'Đề xuất',
  confirmed: 'Đã xác nhận',
  in_progress: 'Đang xử lý',
  mitigated: 'Đã giảm thiểu',
  closed: 'Đã đóng',
};

export const PostMeetTabV2 = ({ meeting, onRefresh }: PostMeetTabV2Props) => {
  const [minutes, setMinutes] = useState<MeetingMinutes | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    loadMinutes();
  }, [meeting.id]);

  const loadMinutes = async () => {
    setIsLoading(true);
    try {
      const data = await minutesApi.getLatest(meeting.id);
      setMinutes(data);
    } catch (err) {
      console.error('Load minutes failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      try {
        const transcriptList = await transcriptsApi.list(meeting.id);
        if (!transcriptList.chunks || transcriptList.chunks.length === 0) {
          const inferenceResult = await meetingsApi.triggerInference(meeting.id);
          if (!inferenceResult.transcript_count) {
            console.warn('Inference finished but no transcripts created.');
          }
        }
      } catch (infErr) {
        console.error('Auto-transcript generation failed:', infErr);
        if (!confirm('Không tìm thấy transcript và không thể tự động tạo. Bạn có muốn tiếp tục tạo biên bản không?')) {
          setIsGenerating(false);
          return;
        }
      }

      const generated = await minutesApi.generate({
        meeting_id: meeting.id,
        include_transcript: true,
        include_actions: true,
        include_decisions: true,
        include_risks: true,
        prompt_strategy: 'structured_json',
        include_quiz: false,
        include_knowledge_table: false,
        format: 'markdown',
      });
      setMinutes(generated);
      onRefresh();
    } catch (err) {
      console.error('Generate failed:', err);
      alert('Không thể tạo biên bản. Vui lòng thử lại.');
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="notion-editor">
        <div className="notion-editor__loading">
          <div className="spinner" />
          <p>Đang tải biên bản họp...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="notion-editor">
      <div className="notion-editor__header">
        <div className="notion-editor__header-left">
          <h1 className="notion-editor__title">📝 Biên bản họp</h1>
          <div className="notion-editor__meta">
            {minutes ? (
              <>
                <StatusBadge status={minutes.status} />
                <span className="notion-editor__meta-item">
                  v{minutes.version} • {new Date(minutes.generated_at).toLocaleString('vi-VN')}
                </span>
              </>
            ) : (
              <span className="notion-editor__meta-item">Chưa có biên bản</span>
            )}
          </div>
        </div>

        <div className="notion-editor__header-actions">
          {minutes && (
            <>
              <ActionButton
                icon={<Copy size={16} />}
                label="Sao chép"
                onClick={async () => {
                  await navigator.clipboard.writeText(minutes.minutes_markdown || '');
                  alert('Đã sao chép biên bản');
                }}
              />
              <ActionButton
                icon={<Download size={16} />}
                label="Xuất file"
                onClick={() => {
                  alert('Sắp hỗ trợ xuất PDF/DOCX.');
                }}
              />
              <ActionButton
                icon={<Mail size={16} />}
                label="Gửi"
                onClick={() => {
                  alert('Sắp hỗ trợ gửi email phân phối.');
                }}
              />
            </>
          )}

          <button className="btn btn--primary" onClick={handleGenerate} disabled={isGenerating} style={{ marginLeft: 8 }}>
            <Sparkles size={16} style={{ marginRight: 6 }} />
            {isGenerating ? 'Đang tạo...' : minutes ? 'Tạo lại' : 'Tạo biên bản'}
          </button>
        </div>
      </div>

      {!minutes ? (
        <EmptyState onGenerate={handleGenerate} isGenerating={isGenerating} />
      ) : (
        <div className="notion-editor__content">
          <EditableBlock
            title="Tóm tắt"
            icon="📋"
            content={minutes.executive_summary || ''}
            onSave={async (content) => {
              await minutesApi.update(minutes.id, { executive_summary: content });
              setMinutes({ ...minutes, executive_summary: content });
            }}
            placeholder="AI sẽ tạo tóm tắt ngắn gọn về cuộc họp..."
          />

          <EditableBlock
            title="Biên bản chi tiết"
            icon="📄"
            content={minutes.minutes_markdown || ''}
            onSave={async (content) => {
              await minutesApi.update(minutes.id, { minutes_markdown: content });
              setMinutes({ ...minutes, minutes_markdown: content });
            }}
            placeholder="AI sẽ tạo biên bản đầy đủ từ transcript..."
            isMarkdown
            large
          />

          <ActionItemsBlockV2 meetingId={meeting.id} />
          <DecisionsBlockV2 meetingId={meeting.id} />
          <RisksBlockV2 meetingId={meeting.id} />
        </div>
      )}
    </div>
  );
};

const EmptyState = ({ onGenerate, isGenerating }: { onGenerate: () => void; isGenerating: boolean }) => {
  return (
    <div className="notion-empty-state">
      <div className="notion-empty-state__icon">
        <Sparkles size={48} strokeWidth={1.5} />
      </div>
      <h3 className="notion-empty-state__title">Tạo biên bản với AI</h3>
      <p className="notion-empty-state__description">
        AI sẽ phân tích transcript và tạo biên bản đầy đủ bao gồm:
        <br />Tóm tắt • Việc cần làm • Quyết định • Rủi ro
      </p>
      <button className="btn btn--primary btn--lg" onClick={onGenerate} disabled={isGenerating}>
        <Sparkles size={18} style={{ marginRight: 8 }} />
        {isGenerating ? 'Đang tạo biên bản...' : 'Tạo biên bản với AI'}
      </button>
    </div>
  );
};

const StatusBadge = ({ status }: { status: string }) => {
  const statusConfig = {
    draft: { label: 'Nháp', color: '#6b7280', icon: <Edit3 size={12} /> },
    reviewed: { label: 'Đã duyệt', color: '#3b82f6', icon: <CheckCircle size={12} /> },
    approved: { label: 'Phê duyệt', color: '#10b981', icon: <CheckCircle size={12} /> },
    distributed: { label: 'Đã gửi', color: '#0ea5e9', icon: <CheckCircle size={12} /> },
  };

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;

  return (
    <div
      className="status-badge"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '4px 8px',
        background: `${config.color}15`,
        color: config.color,
        borderRadius: 6,
        fontSize: 12,
        fontWeight: 500,
      }}
    >
      {config.icon}
      {config.label}
    </div>
  );
};

const ActionButton = ({ icon, label, onClick }: { icon: ReactNode; label: string; onClick: () => void }) => {
  return (
    <button className="notion-action-btn" onClick={onClick}>
      {icon}
      <span>{label}</span>
    </button>
  );
};

interface EditableBlockProps {
  title: string;
  icon: string;
  content: string;
  onSave: (content: string) => Promise<void>;
  placeholder?: string;
  isMarkdown?: boolean;
  large?: boolean;
}

const EditableBlock = ({ title, icon, content, onSave, placeholder, isMarkdown, large }: EditableBlockProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(content);
  const [isSaving, setIsSaving] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    setEditContent(content);
  }, [content]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(editContent);
      setIsEditing(false);
    } catch (err) {
      console.error('Save failed:', err);
      alert('Lưu thất bại');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditContent(content);
    setIsEditing(false);
  };

  return (
    <div
      className={`notion-block ${large ? 'notion-block--large' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="notion-block__header">
        <div className="notion-block__title">
          <span className="notion-block__icon">{icon}</span>
          <span className="notion-block__title-text">{title}</span>
        </div>

        {!isEditing && isHovered && content && (
          <div className="notion-block__actions">
            <button className="notion-icon-btn" onClick={() => setIsEditing(true)} title="Chỉnh sửa">
              <Edit3 size={14} />
            </button>
            <button
              className="notion-icon-btn"
              onClick={async () => {
                await navigator.clipboard.writeText(content);
                alert('Đã sao chép');
              }}
              title="Sao chép"
            >
              <Copy size={14} />
            </button>
          </div>
        )}
      </div>

      <div className="notion-block__content">
        {isEditing ? (
          <>
            <textarea
              className="notion-textarea"
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              placeholder={placeholder}
              rows={large ? 20 : 10}
              autoFocus
            />
            <div className="notion-block__edit-actions">
              <button className="btn btn--sm btn--ghost" onClick={handleCancel} disabled={isSaving}>
                <X size={14} style={{ marginRight: 4 }} />
                Hủy
              </button>
              <button className="btn btn--sm btn--primary" onClick={handleSave} disabled={isSaving}>
                <Check size={14} style={{ marginRight: 4 }} />
                {isSaving ? 'Đang lưu...' : 'Lưu'}
              </button>
            </div>
          </>
        ) : (
          <div className={`notion-content ${!content ? 'notion-content--empty' : ''}`} onClick={() => !content && setIsEditing(true)}>
            {content ? (
              isMarkdown ? (
                <MarkdownRenderer content={content} />
              ) : (
                <p style={{ whiteSpace: 'pre-wrap' }}>{content}</p>
              )
            ) : (
              <p className="notion-content__placeholder">{placeholder}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const MarkdownRenderer = ({ content }: { content: string }) => {
  const html = useMemo(() => {
    const rawHtml = marked.parse(content || '', {
      gfm: true,
      breaks: true,
    }) as string;

    return DOMPurify.sanitize(rawHtml, { ADD_ATTR: ['target'] });
  }, [content]);

  return <div className="notion-markdown" dangerouslySetInnerHTML={{ __html: html }} />;
};

interface ActionItemsBlockV2Props {
  meetingId: string;
}

const ActionItemsBlockV2 = ({ meetingId }: ActionItemsBlockV2Props) => {
  const [items, setItems] = useState<ActionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [newItem, setNewItem] = useState({ title: '', owner_user_id: '', due_date: '', priority: 'medium' as ActionPriority });

  useEffect(() => {
    loadItems();
  }, [meetingId]);

  const loadItems = async () => {
    setIsLoading(true);
    try {
      const data = await itemsApi.listActions(meetingId);
      setItems(data.items || []);
    } catch (err) {
      console.error('Load actions failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setNewItem({ title: '', owner_user_id: '', due_date: '', priority: 'medium' });
    setIsAdding(false);
    setEditingId(null);
  };

  const handleAdd = async () => {
    if (!newItem.title.trim()) return;

    setIsSaving(true);
    try {
      await itemsApi.createAction({
        meeting_id: meetingId,
        title: newItem.title.trim(),
        owner_user_id: newItem.owner_user_id || undefined,
        due_date: newItem.due_date || undefined,
        priority: newItem.priority,
      });
      await loadItems();
      resetForm();
    } catch (err) {
      console.error('Add action failed:', err);
      alert('Thêm action thất bại');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!editingId || !newItem.title.trim()) return;

    setIsSaving(true);
    try {
      await itemsApi.updateAction(editingId, {
        title: newItem.title.trim(),
        owner_user_id: newItem.owner_user_id || undefined,
        due_date: newItem.due_date || undefined,
        priority: newItem.priority,
      });
      await loadItems();
      resetForm();
    } catch (err) {
      console.error('Update action failed:', err);
      alert('Cập nhật action thất bại');
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleStatus = async (item: ActionItem) => {
    const newStatus: ActionStatus = item.status === 'completed' ? 'in_progress' : 'completed';
    try {
      await itemsApi.updateAction(item.id, { status: newStatus });
      setItems(items.map((i) => (i.id === item.id ? { ...i, status: newStatus } : i)));
    } catch (err) {
      console.error('Update status failed:', err);
    }
  };

  const handleDelete = async (itemId: string) => {
    if (!confirm('Xóa action item này?')) return;

    try {
      await itemsApi.deleteAction(itemId);
      setItems(items.filter((item) => item.id !== itemId));
      if (editingId === itemId) {
        resetForm();
      }
    } catch (err) {
      console.error('Delete action failed:', err);
      alert('Xóa action thất bại');
    }
  };

  const startEdit = (item: ActionItem) => {
    setEditingId(item.id);
    setIsAdding(true);
    setNewItem({
      title: item.title || item.description,
      owner_user_id: item.owner_user_id || '',
      due_date: item.due_date || item.deadline || '',
      priority: (item.priority || 'medium') as ActionPriority,
    });
  };

  return (
    <div className="notion-block">
      <div className="notion-block__header" onClick={() => setIsExpanded(!isExpanded)} style={{ cursor: 'pointer' }}>
        <div className="notion-block__title">
          <button className="notion-toggle-btn">{isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</button>
          <span className="notion-block__icon">✅</span>
          <span className="notion-block__title-text">Việc cần làm</span>
          <span className="notion-block__count">{items.length}</span>
        </div>

        {isExpanded && (
          <button
            className="notion-icon-btn"
            onClick={(e) => {
              e.stopPropagation();
              setEditingId(null);
              setIsAdding(true);
            }}
            title="Thêm action"
          >
            <span style={{ fontSize: 18, lineHeight: 1 }}>+</span>
          </button>
        )}
      </div>

      {isExpanded && (
        <div className="notion-block__content">
          {isLoading ? (
            <div className="notion-block__loading">
              <div className="spinner spinner--sm" />
              <span>Đang tải...</span>
            </div>
          ) : (
            <>
              <div className="notion-checklist">
                {items.map((item) => (
                  <NotionChecklistItem
                    key={item.id}
                    item={item}
                    onToggle={() => handleToggleStatus(item)}
                    onEdit={() => startEdit(item)}
                    onDelete={() => handleDelete(item.id)}
                  />
                ))}
              </div>

              {isAdding && (
                <div className="notion-add-item">
                  <input
                    className="notion-input"
                    placeholder="Tiêu đề việc cần làm..."
                    value={newItem.title}
                    onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
                    autoFocus
                  />
                  <div className="notion-add-item__row">
                    <input
                      className="notion-input notion-input--sm"
                      placeholder="Người phụ trách"
                      value={newItem.owner_user_id}
                      onChange={(e) => setNewItem({ ...newItem, owner_user_id: e.target.value })}
                    />
                    <input
                      className="notion-input notion-input--sm"
                      type="date"
                      value={newItem.due_date}
                      onChange={(e) => setNewItem({ ...newItem, due_date: e.target.value })}
                    />
                    <select
                      className="notion-select notion-select--sm"
                      value={newItem.priority}
                      onChange={(e) => setNewItem({ ...newItem, priority: e.target.value as ActionPriority })}
                    >
                      <option value="low">Thấp</option>
                      <option value="medium">Trung bình</option>
                      <option value="high">Cao</option>
                      <option value="critical">Khẩn cấp</option>
                    </select>
                  </div>
                  <div className="notion-add-item__actions">
                    <button className="btn btn--sm btn--ghost" onClick={resetForm} disabled={isSaving}>
                      Hủy
                    </button>
                    <button
                      className="btn btn--sm btn--primary"
                      onClick={editingId ? handleSaveEdit : handleAdd}
                      disabled={isSaving || !newItem.title.trim()}
                    >
                      {isSaving ? 'Đang lưu...' : editingId ? 'Cập nhật' : 'Thêm'}
                    </button>
                  </div>
                </div>
              )}

              {items.length === 0 && !isAdding && (
                <div className="notion-empty-hint" onClick={() => setIsAdding(true)}>
                  Nhấn để thêm việc cần làm...
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

const NotionChecklistItem = ({
  item,
  onToggle,
  onEdit,
  onDelete,
}: {
  item: ActionItem;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
}) => {
  const isCompleted = item.status === 'completed';
  const dueDate = item.due_date || item.deadline;
  const isOverdue = dueDate && new Date(dueDate) < new Date() && !isCompleted;

  return (
    <div className={`notion-checklist-item ${isCompleted ? 'notion-checklist-item--completed' : ''}`}>
      <button className="notion-checkbox" onClick={onToggle}>
        {isCompleted && <Check size={14} strokeWidth={3} />}
      </button>

      <div className="notion-checklist-item__content">
        <div className="notion-list-item__header">
          <span className="notion-checklist-item__text">{item.title || item.description}</span>
          <div className="notion-list-item__actions">
            <button className="notion-icon-btn" onClick={onEdit} title="Sửa action">
              <Edit3 size={14} />
            </button>
            <button className="notion-icon-btn" onClick={onDelete} title="Xóa action">
              <Trash2 size={14} />
            </button>
          </div>
        </div>

        <div className="notion-checklist-item__meta">
          {item.owner_user_id && <span className="notion-tag">👤 {item.owner_user_id}</span>}

          {dueDate && (
            <span className={`notion-tag ${isOverdue ? 'notion-tag--error' : ''}`}>
              <Clock size={12} />
              {new Date(dueDate).toLocaleDateString('vi-VN')}
            </span>
          )}

          {item.priority && item.priority !== 'medium' && (
            <span className={`notion-tag notion-tag--${item.priority}`}>{ACTION_PRIORITY_LABEL[item.priority]}</span>
          )}
        </div>
      </div>
    </div>
  );
};

const DecisionsBlockV2 = ({ meetingId }: { meetingId: string }) => {
  const [items, setItems] = useState<DecisionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    description: '',
    rationale: '',
    status: 'proposed' as DecisionStatus,
  });

  useEffect(() => {
    loadItems();
  }, [meetingId]);

  const loadItems = async () => {
    setIsLoading(true);
    try {
      const data = await itemsApi.listDecisions(meetingId);
      setItems(data.items || []);
    } catch (err) {
      console.error('Load decisions failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setForm({ description: '', rationale: '', status: 'proposed' });
    setEditingId(null);
    setIsEditorOpen(false);
  };

  const startEdit = (item: DecisionItem) => {
    setForm({
      description: item.title || item.description,
      rationale: item.rationale || '',
      status: (item.status || 'proposed') as DecisionStatus,
    });
    setEditingId(item.id);
    setIsEditorOpen(true);
  };

  const handleSave = async () => {
    if (!form.description.trim()) return;

    setIsSaving(true);
    try {
      if (editingId) {
        await itemsApi.updateDecision(editingId, {
          description: form.description.trim(),
          rationale: form.rationale || undefined,
          status: form.status,
        });
      } else {
        await itemsApi.createDecision({
          meeting_id: meetingId,
          description: form.description.trim(),
          rationale: form.rationale || undefined,
          status: form.status,
        });
      }

      await loadItems();
      resetForm();
    } catch (err) {
      console.error('Save decision failed:', err);
      alert('Lưu quyết định thất bại');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Xóa quyết định này?')) return;

    try {
      await itemsApi.deleteDecision(id);
      setItems(items.filter((item) => item.id !== id));
      if (editingId === id) {
        resetForm();
      }
    } catch (err) {
      console.error('Delete decision failed:', err);
      alert('Xóa quyết định thất bại');
    }
  };

  return (
    <div className="notion-block">
      <div className="notion-block__header" onClick={() => setIsExpanded(!isExpanded)} style={{ cursor: 'pointer' }}>
        <div className="notion-block__title">
          <button className="notion-toggle-btn">{isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</button>
          <span className="notion-block__icon">💡</span>
          <span className="notion-block__title-text">Quyết định</span>
          <span className="notion-block__count">{items.length}</span>
        </div>

        {isExpanded && (
          <button
            className="notion-icon-btn"
            onClick={(e) => {
              e.stopPropagation();
              setEditingId(null);
              setIsEditorOpen(true);
            }}
            title="Thêm quyết định"
          >
            <span style={{ fontSize: 18, lineHeight: 1 }}>+</span>
          </button>
        )}
      </div>

      {isExpanded && (
        <div className="notion-block__content">
          {isLoading ? (
            <div className="notion-block__loading">
              <div className="spinner spinner--sm" />
            </div>
          ) : (
            <>
              {items.length === 0 && !isEditorOpen && <div className="notion-empty-hint">Không có quyết định nào được ghi nhận</div>}

              {items.length > 0 && (
                <div className="notion-list">
                  {items.map((item, index) => (
                    <div key={item.id} className="notion-list-item">
                      <div className="notion-list-item__number">{index + 1}</div>
                      <div className="notion-list-item__content">
                        <div className="notion-list-item__header">
                          <div className="notion-list-item__title">{item.title || item.description}</div>
                          <div className="notion-list-item__actions">
                            <button className="notion-icon-btn" onClick={() => startEdit(item)} title="Sửa quyết định">
                              <Edit3 size={14} />
                            </button>
                            <button className="notion-icon-btn" onClick={() => handleDelete(item.id)} title="Xóa quyết định">
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </div>
                        {item.rationale && <div className="notion-list-item__subtitle">Lý do: {item.rationale}</div>}
                        <div className="notion-list-item__meta">
                          <span className="notion-tag">{DECISION_STATUS_LABEL[(item.status || 'proposed') as DecisionStatus] || item.status}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {isEditorOpen && (
                <div className="notion-add-item" style={{ marginTop: 12 }}>
                  <input
                    className="notion-input"
                    placeholder="Nội dung quyết định..."
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    autoFocus
                  />
                  <div className="notion-add-item__row" style={{ gridTemplateColumns: '1fr 160px' }}>
                    <input
                      className="notion-input notion-input--sm"
                      placeholder="Lý do / bối cảnh"
                      value={form.rationale}
                      onChange={(e) => setForm({ ...form, rationale: e.target.value })}
                    />
                    <select
                      className="notion-select notion-select--sm"
                      value={form.status}
                      onChange={(e) => setForm({ ...form, status: e.target.value as DecisionStatus })}
                    >
                      <option value="proposed">Đề xuất</option>
                      <option value="confirmed">Đã xác nhận</option>
                      <option value="revised">Đã chỉnh sửa</option>
                    </select>
                  </div>
                  <div className="notion-add-item__actions">
                    <button className="btn btn--sm btn--ghost" onClick={resetForm} disabled={isSaving}>
                      Hủy
                    </button>
                    <button className="btn btn--sm btn--primary" onClick={handleSave} disabled={isSaving || !form.description.trim()}>
                      {isSaving ? 'Đang lưu...' : editingId ? 'Cập nhật' : 'Thêm'}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

const RisksBlockV2 = ({ meetingId }: { meetingId: string }) => {
  const [items, setItems] = useState<RiskItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    description: '',
    mitigation: '',
    severity: 'medium' as RiskSeverity,
    status: 'proposed' as RiskStatus,
    owner_user_id: '',
  });

  useEffect(() => {
    loadItems();
  }, [meetingId]);

  const loadItems = async () => {
    setIsLoading(true);
    try {
      const data = await itemsApi.listRisks(meetingId);
      setItems(data.items || []);
    } catch (err) {
      console.error('Load risks failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const severityConfig = {
    low: { color: '#10b981', icon: '🟢', label: 'Thấp' },
    medium: { color: '#f59e0b', icon: '🟡', label: 'Trung bình' },
    high: { color: '#ef4444', icon: '🔴', label: 'Cao' },
    critical: { color: '#dc2626', icon: '🔴🔴', label: 'Khẩn cấp' },
  };

  const resetForm = () => {
    setForm({ description: '', mitigation: '', severity: 'medium', status: 'proposed', owner_user_id: '' });
    setEditingId(null);
    setIsEditorOpen(false);
  };

  const startEdit = (item: RiskItem) => {
    setForm({
      description: item.title || item.description,
      mitigation: item.mitigation || '',
      severity: (item.severity || 'medium') as RiskSeverity,
      status: (item.status || 'proposed') as RiskStatus,
      owner_user_id: item.owner_user_id || '',
    });
    setEditingId(item.id);
    setIsEditorOpen(true);
  };

  const handleSave = async () => {
    if (!form.description.trim()) return;

    setIsSaving(true);
    try {
      if (editingId) {
        await itemsApi.updateRisk(editingId, {
          description: form.description.trim(),
          mitigation: form.mitigation || undefined,
          severity: form.severity,
          status: form.status,
          owner_user_id: form.owner_user_id || undefined,
        });
      } else {
        await itemsApi.createRisk({
          meeting_id: meetingId,
          description: form.description.trim(),
          mitigation: form.mitigation || undefined,
          severity: form.severity,
          status: form.status,
          owner_user_id: form.owner_user_id || undefined,
        });
      }

      await loadItems();
      resetForm();
    } catch (err) {
      console.error('Save risk failed:', err);
      alert('Lưu rủi ro thất bại');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Xóa rủi ro này?')) return;

    try {
      await itemsApi.deleteRisk(id);
      setItems(items.filter((item) => item.id !== id));
      if (editingId === id) {
        resetForm();
      }
    } catch (err) {
      console.error('Delete risk failed:', err);
      alert('Xóa rủi ro thất bại');
    }
  };

  return (
    <div className="notion-block">
      <div className="notion-block__header" onClick={() => setIsExpanded(!isExpanded)} style={{ cursor: 'pointer' }}>
        <div className="notion-block__title">
          <button className="notion-toggle-btn">{isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</button>
          <span className="notion-block__icon">⚠️</span>
          <span className="notion-block__title-text">Rủi ro</span>
          <span className="notion-block__count">{items.length}</span>
        </div>

        {isExpanded && (
          <button
            className="notion-icon-btn"
            onClick={(e) => {
              e.stopPropagation();
              setEditingId(null);
              setIsEditorOpen(true);
            }}
            title="Thêm rủi ro"
          >
            <span style={{ fontSize: 18, lineHeight: 1 }}>+</span>
          </button>
        )}
      </div>

      {isExpanded && (
        <div className="notion-block__content">
          {isLoading ? (
            <div className="notion-block__loading">
              <div className="spinner spinner--sm" />
            </div>
          ) : (
            <>
              {items.length === 0 && !isEditorOpen && <div className="notion-empty-hint">Không có rủi ro nào được ghi nhận</div>}

              {items.length > 0 && (
                <div className="notion-list">
                  {items.map((item) => {
                    const config = severityConfig[(item.severity || 'medium') as RiskSeverity] || severityConfig.medium;
                    return (
                      <div key={item.id} className="notion-list-item">
                        <div className="notion-list-item__icon" style={{ color: config.color }}>
                          {config.icon}
                        </div>
                        <div className="notion-list-item__content">
                          <div className="notion-list-item__header">
                            <div className="notion-list-item__title">{item.title || item.description}</div>
                            <div className="notion-list-item__actions">
                              <button className="notion-icon-btn" onClick={() => startEdit(item)} title="Sửa rủi ro">
                                <Edit3 size={14} />
                              </button>
                              <button className="notion-icon-btn" onClick={() => handleDelete(item.id)} title="Xóa rủi ro">
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </div>
                          {item.mitigation && <div className="notion-list-item__subtitle">Giải pháp: {item.mitigation}</div>}
                          <div className="notion-list-item__meta">
                            <span className="notion-tag" style={{ background: `${config.color}20`, color: config.color }}>
                              {config.label}
                            </span>
                            <span className="notion-tag">{RISK_STATUS_LABEL[(item.status || 'proposed') as RiskStatus] || item.status}</span>
                            {item.owner_user_id && <span className="notion-tag">👤 {item.owner_user_id}</span>}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {isEditorOpen && (
                <div className="notion-add-item" style={{ marginTop: 12 }}>
                  <input
                    className="notion-input"
                    placeholder="Nội dung rủi ro..."
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    autoFocus
                  />
                  <div className="notion-add-item__row" style={{ gridTemplateColumns: '1fr 140px 180px' }}>
                    <select
                      className="notion-select notion-select--sm"
                      value={form.severity}
                      onChange={(e) => setForm({ ...form, severity: e.target.value as RiskSeverity })}
                    >
                      <option value="low">Thấp</option>
                      <option value="medium">Trung bình</option>
                      <option value="high">Cao</option>
                      <option value="critical">Khẩn cấp</option>
                    </select>
                    <select
                      className="notion-select notion-select--sm"
                      value={form.status}
                      onChange={(e) => setForm({ ...form, status: e.target.value as RiskStatus })}
                    >
                      <option value="identified">Đã nhận diện</option>
                      <option value="proposed">Đề xuất</option>
                      <option value="confirmed">Đã xác nhận</option>
                      <option value="in_progress">Đang xử lý</option>
                      <option value="mitigated">Đã giảm thiểu</option>
                      <option value="closed">Đã đóng</option>
                    </select>
                    <input
                      className="notion-input notion-input--sm"
                      placeholder="Owner"
                      value={form.owner_user_id}
                      onChange={(e) => setForm({ ...form, owner_user_id: e.target.value })}
                    />
                  </div>
                  <input
                    className="notion-input notion-input--sm"
                    style={{ marginTop: 8 }}
                    placeholder="Kế hoạch giảm thiểu"
                    value={form.mitigation}
                    onChange={(e) => setForm({ ...form, mitigation: e.target.value })}
                  />
                  <div className="notion-add-item__actions">
                    <button className="btn btn--sm btn--ghost" onClick={resetForm} disabled={isSaving}>
                      Hủy
                    </button>
                    <button className="btn btn--sm btn--primary" onClick={handleSave} disabled={isSaving || !form.description.trim()}>
                      {isSaving ? 'Đang lưu...' : editingId ? 'Cập nhật' : 'Thêm'}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default PostMeetTabV2;
