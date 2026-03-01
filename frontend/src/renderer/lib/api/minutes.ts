// ============================================
// MINUTES API
// API functions for meeting minutes operations
// ============================================

import api from '../apiClient';

const USER_STORAGE_KEY = 'minute_user';

export interface MeetingMinutes {
  id: string;
  meeting_id: string;
  version: number;
  minutes_text?: string;
  minutes_html?: string;
  minutes_markdown?: string;
  executive_summary?: string;
  minutes_doc_url?: string;
  status: 'draft' | 'reviewed' | 'approved' | 'distributed';
  generated_at: string;
  edited_by?: string;
  edited_at?: string;
  approved_by?: string;
  approved_at?: string;
}

export interface MeetingMinutesList {
  minutes: MeetingMinutes[];
  total: number;
}

export interface GenerateMinutesRequest {
  meeting_id: string;
  request_user_id?: string;
  template_id?: string; // Template ID to use for generation
  include_transcript?: boolean;
  include_actions?: boolean;
  include_decisions?: boolean;
  include_risks?: boolean;
  prompt_strategy?: 'context_json' | 'structured_json';
  session_type?: 'meeting' | 'course';
  include_topic_tracker?: boolean;
  include_ai_filters?: boolean;
  include_quiz?: boolean;
  include_knowledge_table?: boolean;
  format?: 'markdown' | 'html' | 'text';
}

export interface DistributeMinutesRequest {
  minutes_id: string;
  meeting_id: string;
  channels?: string[]; // email, teams, sharepoint
  recipients?: string[]; // user_ids, undefined = all participants
}

export interface DistributionLog {
  id: string;
  minutes_id: string;
  meeting_id: string;
  user_id?: string;
  channel: string;
  recipient_email?: string;
  sent_at: string;
  status: string;
  error_message?: string;
}

export interface DistributionLogList {
  logs: DistributionLog[];
  total: number;
}

const ENDPOINT = '/minutes';
type LatestMinutesEnvelope = {
  meeting_id: string;
  minutes: MeetingMinutes | null;
  message?: string;
};

const isMeetingMinutes = (value: unknown): value is MeetingMinutes => {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<MeetingMinutes>;
  return (
    typeof candidate.id === 'string' &&
    typeof candidate.meeting_id === 'string' &&
    typeof candidate.version === 'number' &&
    typeof candidate.status === 'string' &&
    typeof candidate.generated_at === 'string'
  );
};

const resolveRequestUserId = (): string | undefined => {
  if (typeof localStorage === 'undefined') return undefined;
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return undefined;
    const parsed = JSON.parse(raw) as { id?: string };
    const id = String(parsed.id || '').trim();
    return id || undefined;
  } catch {
    return undefined;
  }
};

export const minutesApi = {
  /**
   * List all minutes versions for a meeting
   */
  list: async (meetingId: string): Promise<MeetingMinutesList> => {
    return api.get<MeetingMinutesList>(`${ENDPOINT}/${meetingId}`);
  },

  /**
   * Get the latest minutes for a meeting
   */
  getLatest: async (meetingId: string): Promise<MeetingMinutes | null> => {
    const response = await api.get<LatestMinutesEnvelope | MeetingMinutes>(`${ENDPOINT}/${meetingId}/latest`);

    // Backward-compatible parsing:
    // - New/expected: { meeting_id, minutes }
    // - Legacy: direct MeetingMinutes object
    if (isMeetingMinutes(response)) {
      return response;
    }

    if (response && typeof response === 'object' && 'minutes' in response) {
      const nested = (response as LatestMinutesEnvelope).minutes;
      return isMeetingMinutes(nested) ? nested : null;
    }

    return null;
  },

  /**
   * Generate minutes using AI
   */
  generate: async (request: GenerateMinutesRequest): Promise<MeetingMinutes> => {
    const payload: GenerateMinutesRequest = { ...request };
    if (!payload.request_user_id) {
      payload.request_user_id = resolveRequestUserId();
    }
    return api.post<MeetingMinutes>(`${ENDPOINT}/generate`, payload);
  },

  /**
   * Update minutes
   */
  update: async (minutesId: string, data: Partial<MeetingMinutes>): Promise<MeetingMinutes> => {
    return api.put<MeetingMinutes>(`${ENDPOINT}/${minutesId}`, data);
  },

  /**
   * Approve minutes
   */
  approve: async (minutesId: string, approvedBy: string): Promise<MeetingMinutes> => {
    return api.post<MeetingMinutes>(`${ENDPOINT}/${minutesId}/approve?approved_by=${encodeURIComponent(approvedBy)}`, null);
  },

  /**
   * Get distribution logs for a meeting
   */
  getDistributionLogs: async (meetingId: string): Promise<DistributionLogList> => {
    return api.get<DistributionLogList>(`${ENDPOINT}/${meetingId}/distribution`);
  },

  /**
   * Distribute minutes to participants
   */
  distribute: async (request: DistributeMinutesRequest): Promise<{
    status: string;
    distributed_to: number;
    channels: string[];
    logs: DistributionLog[];
  }> => {
    return api.post(`${ENDPOINT}/distribute`, request);
  },
};

export default minutesApi;
