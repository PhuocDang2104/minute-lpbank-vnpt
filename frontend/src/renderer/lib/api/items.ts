// ============================================
// ITEMS API (Actions, Decisions, Risks)
// ============================================

import api from '../apiClient';

type ItemPriority = 'low' | 'medium' | 'high' | 'critical';
type ActionStatus = 'proposed' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled';
type DecisionStatus = 'proposed' | 'confirmed' | 'revised';
type RiskSeverity = 'low' | 'medium' | 'high' | 'critical';
type RiskStatus = 'identified' | 'proposed' | 'confirmed' | 'in_progress' | 'mitigated' | 'closed';

// Action Items
export interface ActionItem {
  id: string;
  meeting_id: string;
  owner_user_id?: string;
  owner_name?: string;
  title?: string; // UI alias of description
  meeting_title?: string;
  description: string;
  deadline?: string;
  due_date?: string; // UI alias of deadline
  priority: ItemPriority;
  status: ActionStatus;
  source_text?: string;
  external_task_link?: string;
  external_task_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface ActionItemCreate {
  meeting_id: string;
  title?: string;
  description?: string;
  owner_user_id?: string;
  deadline?: string;
  due_date?: string;
  priority?: ItemPriority | string;
  status?: ActionStatus | string;
  external_task_link?: string;
}

export interface ActionItemUpdate {
  title?: string;
  description?: string;
  owner_user_id?: string;
  deadline?: string;
  due_date?: string;
  priority?: ItemPriority | string;
  status?: ActionStatus | string;
  external_task_link?: string;
  external_task_id?: string;
}

export interface ActionItemFilters {
  status?: string;
  priority?: string;
  owner_user_id?: string;
  overdue_only?: boolean;
}

export interface ActionItemList {
  items: ActionItem[];
  total: number;
}

// Decisions
export interface DecisionItem {
  id: string;
  meeting_id: string;
  title?: string; // UI alias of description
  description: string;
  rationale?: string;
  impact?: string; // UI-only optional field
  status?: DecisionStatus;
  confirmed_by?: string;
  confirmed_at?: string;
  source_text?: string;
  created_at: string;
  updated_at?: string;
}

export interface DecisionItemCreate {
  meeting_id: string;
  title?: string;
  description?: string;
  rationale?: string;
  status?: DecisionStatus | string;
  source_text?: string;
}

export interface DecisionItemUpdate {
  title?: string;
  description?: string;
  rationale?: string;
  status?: DecisionStatus | string;
}

export interface DecisionItemList {
  items: DecisionItem[];
  total: number;
}

// Risks
export interface RiskItem {
  id: string;
  meeting_id: string;
  title?: string; // UI alias of description
  description: string;
  severity: RiskSeverity;
  mitigation?: string;
  status: RiskStatus;
  owner_user_id?: string;
  owner_name?: string;
  source_text?: string;
  created_at: string;
  updated_at?: string;
}

export interface RiskItemCreate {
  meeting_id: string;
  title?: string;
  description?: string;
  severity?: RiskSeverity | string;
  mitigation?: string;
  status?: RiskStatus | string;
  owner_user_id?: string;
  source_text?: string;
}

export interface RiskItemUpdate {
  title?: string;
  description?: string;
  severity?: RiskSeverity | string;
  mitigation?: string;
  status?: RiskStatus | string;
  owner_user_id?: string;
}

export interface RiskItemList {
  items: RiskItem[];
  total: number;
}

const ENDPOINT = '/items';

const normalizeActionItem = (item: Partial<ActionItem>): ActionItem => {
  const description = item.description || item.title || '';
  const deadline = item.deadline || item.due_date;

  return {
    ...(item as ActionItem),
    description,
    title: item.title || description,
    deadline,
    due_date: item.due_date || deadline,
    updated_at: item.updated_at || item.created_at,
  };
};

const normalizeDecisionItem = (item: Partial<DecisionItem>): DecisionItem => {
  const description = item.description || item.title || '';

  return {
    ...(item as DecisionItem),
    description,
    title: item.title || description,
    updated_at: item.updated_at || item.created_at,
  };
};

const normalizeRiskItem = (item: Partial<RiskItem>): RiskItem => {
  const description = item.description || item.title || '';

  return {
    ...(item as RiskItem),
    description,
    title: item.title || description,
    updated_at: item.updated_at || item.created_at,
  };
};

const getActionDescription = (data: { title?: string; description?: string }): string => {
  const description = (data.description || data.title || '').trim();
  if (!description) {
    throw new Error('Action item description is required');
  }
  return description;
};

const getDecisionDescription = (data: { title?: string; description?: string }): string => {
  const description = (data.description || data.title || '').trim();
  if (!description) {
    throw new Error('Decision description is required');
  }
  return description;
};

const getRiskDescription = (data: { title?: string; description?: string }): string => {
  const description = (data.description || data.title || '').trim();
  if (!description) {
    throw new Error('Risk description is required');
  }
  return description;
};

export const itemsApi = {
  // Action Items - List all with filters
  listAllActions: async (filters?: ActionItemFilters): Promise<ActionItemList> => {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.owner_user_id) params.append('owner_user_id', filters.owner_user_id);
    if (filters?.overdue_only) params.append('overdue_only', 'true');

    const query = params.toString();
    const response = await api.get<ActionItemList>(`${ENDPOINT}/actions${query ? `?${query}` : ''}`);
    const items = (response.items || []).map(normalizeActionItem);
    return {
      items,
      total: response.total ?? items.length,
    };
  },

  // Action Items - List by meeting
  listActions: async (meetingId: string): Promise<ActionItemList> => {
    const response = await api.get<ActionItemList>(`${ENDPOINT}/actions/${meetingId}`);
    const items = (response.items || []).map(normalizeActionItem);
    return {
      items,
      total: response.total ?? items.length,
    };
  },

  getAction: async (itemId: string): Promise<ActionItem> => {
    const response = await api.get<ActionItem>(`${ENDPOINT}/actions/item/${itemId}`);
    return normalizeActionItem(response);
  },

  createAction: async (data: ActionItemCreate): Promise<ActionItem> => {
    const payload = {
      meeting_id: data.meeting_id,
      description: getActionDescription(data),
      owner_user_id: data.owner_user_id,
      deadline: data.deadline || data.due_date,
      priority: data.priority,
      status: data.status,
      external_task_link: data.external_task_link,
    };
    const response = await api.post<ActionItem>(`${ENDPOINT}/actions`, payload);
    return normalizeActionItem(response);
  },

  updateAction: async (itemId: string, data: ActionItemUpdate): Promise<ActionItem> => {
    const payload: Record<string, unknown> = {
      ...data,
      deadline: data.deadline ?? data.due_date,
    };

    if (data.title !== undefined || data.description !== undefined) {
      payload.description = getActionDescription(data);
    }

    delete payload.title;
    delete payload.due_date;

    const response = await api.put<ActionItem>(`${ENDPOINT}/actions/${itemId}`, payload);
    return normalizeActionItem(response);
  },

  deleteAction: async (itemId: string): Promise<void> => {
    return api.delete(`${ENDPOINT}/actions/${itemId}`);
  },

  // Decisions
  listDecisions: async (meetingId: string): Promise<DecisionItemList> => {
    const response = await api.get<DecisionItemList>(`${ENDPOINT}/decisions/${meetingId}`);
    const items = (response.items || []).map(normalizeDecisionItem);
    return {
      items,
      total: response.total ?? items.length,
    };
  },

  getDecision: async (itemId: string): Promise<DecisionItem> => {
    const response = await api.get<DecisionItem>(`${ENDPOINT}/decisions/item/${itemId}`);
    return normalizeDecisionItem(response);
  },

  createDecision: async (data: DecisionItemCreate): Promise<DecisionItem> => {
    const payload = {
      meeting_id: data.meeting_id,
      description: getDecisionDescription(data),
      rationale: data.rationale,
      status: data.status,
      source_text: data.source_text,
    };
    const response = await api.post<DecisionItem>(`${ENDPOINT}/decisions`, payload);
    return normalizeDecisionItem(response);
  },

  updateDecision: async (itemId: string, data: DecisionItemUpdate): Promise<DecisionItem> => {
    const payload: Record<string, unknown> = { ...data };
    if (data.title !== undefined || data.description !== undefined) {
      payload.description = getDecisionDescription(data);
    }
    delete payload.title;

    const response = await api.put<DecisionItem>(`${ENDPOINT}/decisions/${itemId}`, payload);
    return normalizeDecisionItem(response);
  },

  deleteDecision: async (itemId: string): Promise<void> => {
    return api.delete(`${ENDPOINT}/decisions/${itemId}`);
  },

  // Risks
  listRisks: async (meetingId: string): Promise<RiskItemList> => {
    const response = await api.get<RiskItemList>(`${ENDPOINT}/risks/${meetingId}`);
    const items = (response.items || []).map(normalizeRiskItem);
    return {
      items,
      total: response.total ?? items.length,
    };
  },

  getRisk: async (itemId: string): Promise<RiskItem> => {
    const response = await api.get<RiskItem>(`${ENDPOINT}/risks/item/${itemId}`);
    return normalizeRiskItem(response);
  },

  createRisk: async (data: RiskItemCreate): Promise<RiskItem> => {
    const payload = {
      meeting_id: data.meeting_id,
      description: getRiskDescription(data),
      severity: data.severity || 'medium',
      mitigation: data.mitigation,
      status: data.status || 'proposed',
      owner_user_id: data.owner_user_id,
      source_text: data.source_text,
    };
    const response = await api.post<RiskItem>(`${ENDPOINT}/risks`, payload);
    return normalizeRiskItem(response);
  },

  updateRisk: async (itemId: string, data: RiskItemUpdate): Promise<RiskItem> => {
    const payload: Record<string, unknown> = { ...data };
    if (data.title !== undefined || data.description !== undefined) {
      payload.description = getRiskDescription(data);
    }
    delete payload.title;

    const response = await api.put<RiskItem>(`${ENDPOINT}/risks/${itemId}`, payload);
    return normalizeRiskItem(response);
  },

  deleteRisk: async (itemId: string): Promise<void> => {
    return api.delete(`${ENDPOINT}/risks/${itemId}`);
  },
};

export default itemsApi;
