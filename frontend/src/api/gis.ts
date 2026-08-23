import client, { getApiKey } from "./client"

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

export type GisStreamEvent =
  | { type: "session_start"; session_id: string }
  | { type: "text_delta"; delta: string }
  | {
      type: "tool_call"
      step: number
      tool: string
      args: Record<string, unknown>
    }
  | {
      type: "tool_result"
      step: number
      tool: string
      result: Record<string, unknown>
    }
  | {
      type: "approval_request"
      approval_id: string
      tool: string
      args: Record<string, unknown>
      message?: string
    }
  | { type: "done"; final: string; outputs: string[]; steps: number; timed_out: boolean }
  | { type: "error"; error: string }

/** 流式运行 GIS 助手（SSE）；事件按输出顺序实时回调 */
export async function streamGisAssistant(
  userRequest: string,
  dataFile: string | undefined,
  sessionId: string | undefined,
  onEvent: (ev: GisStreamEvent) => void | Promise<void>,
): Promise<void> {
  const params = new URLSearchParams({ user_request: userRequest })
  if (dataFile) params.set("data_file", dataFile)
  if (sessionId) params.set("session_id", sessionId)
  let resp: Response
  try {
    resp = await fetch(`/api/v1/gis-assistant/run/stream?${params.toString()}`, {
      headers: { "X-API-Key": getApiKey(), Accept: "text/event-stream" },
    })
  } catch (err) {
    // 网络层失败（后端未启动/连接中断），给出可理解提示
    throw new Error("无法连接后端服务，请确认后端已启动（python start.bat）")
  }
  if (!resp.ok || !resp.body) {
    const detail = await resp.text().catch(() => "")
    throw new Error(`流式请求失败 (${resp.status})${detail ? `: ${detail}` : ""}`)
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let sep: number
      while ((sep = buffer.indexOf("\n\n")) >= 0) {
        const block = buffer.slice(0, sep)
        buffer = buffer.slice(sep + 2)
        const line = block.split("\n").find((l) => l.startsWith("data:"))
        if (!line) continue
        const payload = line.slice(5).trim()
        if (!payload) continue
        try {
          await onEvent(JSON.parse(payload) as GisStreamEvent)
        } catch {
          // 忽略无法解析的事件
        }
      }
    }
  } catch {
    // 流式读取中途断连（后端重启/崩溃），给出可理解提示
    throw new Error("连接中断：后端服务异常退出，请检查后端日志后重试")
  }
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


export interface GisSessionSummary {
  session_id: string
  title: string
  created_at: number
  updated_at: number
  rounds: number
}

export interface GisSessionRound {
  user: string
  final: string
  steps: number
  outputs: string[]
  trajectory: GisTrajectoryStep[]
  timed_out: boolean
}

export interface GisSessionDetail {
  session_id: string
  title: string
  created_at: number
  updated_at: number
  rounds: GisSessionRound[]
}

/** 当前用户的会话列表 */
export async function listGisSessions(): Promise<GisSessionSummary[]> {
  const { data } = await client.get("/gis-assistant/sessions")
  return data.sessions ?? []
}

/** 会话详情（恢复对话历史） */
export async function getGisSessionDetail(sessionId: string): Promise<GisSessionDetail> {
  const { data } = await client.get(`/gis-assistant/sessions/${sessionId}`)
  return data
}

/** 删除会话 */
export async function deleteGisSession(sessionId: string): Promise<void> {
  await client.delete(`/gis-assistant/sessions/${sessionId}`)
}

/** HITL 审批：允许 / 拒绝危险操作 */
export async function approveGisApproval(
  sessionId: string,
  approvalId: string,
  action: "approve" | "reject",
): Promise<{ ok: boolean; status?: string }> {
  const { data } = await client.post(
    `/gis-assistant/sessions/${sessionId}/approvals/${approvalId}`,
    null,
    { params: { action } },
  )
  return data as { ok: boolean; status?: string }
}

/** 切换会话权限模式：readonly / auto / ask */
export async function setGisPermission(
  sessionId: string,
  mode: "readonly" | "auto" | "ask",
): Promise<{ ok: boolean; mode: string }> {
  const { data } = await client.post(
    `/gis-assistant/sessions/${sessionId}/permission`,
    null,
    { params: { mode } },
  )
  return data as { ok: boolean; mode: string }
}
