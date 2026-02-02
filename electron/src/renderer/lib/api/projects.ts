import api from '../apiClient'
import { ProjectListResponse, Project } from '../../shared/dto/project'
import { DocumentListResponse } from '../../shared/dto/document'
import { MeetingListResponse } from '../../shared/dto/meeting'
import { ProjectMemberList } from '../../shared/dto/projectMember'

const base = '/projects'

const projectsApi = {
  list: (params?: { skip?: number; limit?: number; search?: string; department_id?: string; organization_id?: string }) =>
    api.get<ProjectListResponse>(base, params),

  get: (projectId: string) => api.get<Project>(`${base}/${projectId}`),

  update: (projectId: string, data: Partial<Project>) => api.patch<Project>(`${base}/${projectId}`, data),

  remove: (projectId: string) => api.delete<void>(`${base}/${projectId}`),

  listMembers: (projectId: string) => api.get<ProjectMemberList>(`${base}/${projectId}/members`),
  addMember: (projectId: string, user_id: string, role: string = 'member') =>
    api.post(`${base}/${projectId}/members?user_id=${encodeURIComponent(user_id)}&role=${encodeURIComponent(role)}`),

  listDocuments: (projectId: string) => api.get<DocumentListResponse>(`${base}/${projectId}/documents`),

  listMeetings: (projectId: string) => api.get<MeetingListResponse>(`${base}/${projectId}/meetings`),
}

export default projectsApi
