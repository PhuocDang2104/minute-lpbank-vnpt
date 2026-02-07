import api from '../apiClient';
import type {
  User,
  UserListResponse,
  DepartmentListResponse,
  Department,
  LlmSettings,
  LlmSettingsUpdate,
} from '../../shared/dto/user';

const ENDPOINT = '/users';

export const usersApi = {
  list: async (params?: { search?: string; department_id?: string }): Promise<UserListResponse> => {
    return api.get<UserListResponse>(`${ENDPOINT}/`, params as Record<string, string>);
  },

  getMe: async (): Promise<User> => {
    return api.get<User>(`${ENDPOINT}/me`);
  },

  get: async (id: string): Promise<User> => {
    return api.get<User>(`${ENDPOINT}/${id}`);
  },

  getLlmSettings: async (id: string): Promise<LlmSettings> => {
    return api.get<LlmSettings>(`${ENDPOINT}/${id}/llm-settings`);
  },

  updateLlmSettings: async (id: string, payload: LlmSettingsUpdate): Promise<LlmSettings> => {
    return api.put<LlmSettings>(`${ENDPOINT}/${id}/llm-settings`, payload);
  },

  getDepartments: async (): Promise<DepartmentListResponse> => {
    return api.get<DepartmentListResponse>(`${ENDPOINT}/departments`);
  },
};

// Named exports for convenience
export async function listUsers(params?: { search?: string; department_id?: string }): Promise<UserListResponse> {
  return usersApi.list(params);
}

export async function listDepartments(): Promise<DepartmentListResponse> {
  return usersApi.getDepartments();
}

export async function getUser(id: string): Promise<User> {
  return usersApi.get(id);
}

// Re-export types
export type { User, Department, UserListResponse, DepartmentListResponse };

export default usersApi;
