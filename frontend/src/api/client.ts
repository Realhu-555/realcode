import axios from "axios"

export function getApiKey(): string {
  let key = localStorage.getItem("suxuan-api-key") || ""
  if (!key) {
    key = "demo-" + Math.random().toString(36).slice(2, 10)
    localStorage.setItem("suxuan-api-key", key)
  }
  return key
}

const client = axios.create({
  baseURL: "/api/v1",
  timeout: 600_000,
  headers: { "Content-Type": "application/json" },
})

// 自动注入 X-API-Key
client.interceptors.request.use((config) => {
  config.headers["X-API-Key"] = getApiKey()
  return config
})

export interface ModelInfo {
  id: string
  label: string
  capabilities: string[]
}

export interface ModelsResponse {
  models: ModelInfo[]
  default: string
}

export async function listModels(): Promise<ModelsResponse> {
  const { data } = await client.get("/models")
  return data
}

export default client
