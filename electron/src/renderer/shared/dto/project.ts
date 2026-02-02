export interface Project {
  id: string
  name: string
  code?: string
  description?: string
  objective?: string  // Project objectives/goals
  organization_id?: string
  department_id?: string
  owner_id?: string
  created_at?: string
  updated_at?: string
}

export interface ProjectListResponse {
  projects: Project[]
  total: number
}

