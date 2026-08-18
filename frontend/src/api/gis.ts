import client from "./client"

export interface GisTrajectoryStep {
  step: number
  tool: string
  args: Record<string, unknown>
  result: Record<string, unknown>
}

export interface GisAssistantResult {
  project_id: string
  session_id: string
  stage: string
  error_message?: string
  trajectory: GisTrajectoryStep[]
  outputs: string[]
  final: string
  steps: number
  timed_out: boolean
  out_dir: string
}

export interface UploadResult {
  success: boolean
  path?: string
  filename?: string
  error?: string
}

/** 上传 GIS 数据文件（CSV / GeoJSON / JSON / zip） */
export async function uploadGisFile(file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append("file", file)
  const { data } = await client.post("/gis/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  return data
}

/** 同步运行工具调用版 GIS 助手；带 sessionId 时继续上一会话（复用图层与对话历史） */
export async function runGisAssistant(
  userRequest: string,
  dataFile?: string,
  sessionId?: string,
): Promise<GisAssistantResult> {
  const { data } = await client.post("/gis-assistant/run", {
    user_request: userRequest,
    data_file: dataFile,
    session_id: sessionId,
  })
  return data
}

/** 以 blob 获取指定会话的产物文件（携带 X-API-Key） */
export async function fetchGisFile(name: string, sessionId: string): Promise<Blob> {
  const { data } = await client.get(
    `/gis-assistant/files/${encodeURIComponent(sessionId)}/${encodeURIComponent(name)}`,
    { responseType: "blob" },
  )
  return data as Blob
}

/** 产物 blob 转可预览/下载的 object URL */
export async function objectUrlFor(name: string, sessionId: string): Promise<string> {
  const blob = await fetchGisFile(name, sessionId)
  return URL.createObjectURL(blob)
}
