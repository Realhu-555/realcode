import axios from "axios"

const client = axios.create({
  baseURL: "/api/v1",
  timeout: 120_000,
  headers: { "Content-Type": "application/json" },
})

export interface CreateProjectPayload {
  mode: "form" | "free"
  product_name?: string
  product_description?: string
  target_users?: string
  key_selling_points?: string[]
  brand_tone?: string
  competitors?: string[]
  user_idea?: string
  image_urls?: string[]   // base64 编码的图片（data:image/...;base64,...）
}

export interface ProjectStatus {
  project_id: string
  stage: string
  strategy: any | null
  contents: Record<string, any | null>
  review_report: any | null
  created_at: string
  updated_at: string
}

export async function createProject(payload: CreateProjectPayload) {
  const { data } = await client.post("/content-projects", payload)
  return data
}

export async function getProjectStatus(projectId: string): Promise<ProjectStatus> {
  const { data } = await client.get(`/content-projects/${projectId}`)
  return data
}

export async function confirmStrategy(projectId: string, confirmed: boolean, feedback?: string) {
  const { data } = await client.post(`/content-projects/${projectId}/confirm-strategy`, {
    confirmed,
    feedback,
  })
  return data
}

export async function getChannelContent(projectId: string, channel: string) {
  const { data } = await client.get(`/content-projects/${projectId}/content/${channel}`)
  return data
}

export async function getReviewReport(projectId: string) {
  const { data } = await client.get(`/content-projects/${projectId}/review`)
  return data
}

export async function exportProject(projectId: string) {
  const { data } = await client.get(`/content-projects/${projectId}/export`)
  return data
}

export default client
