import { defineStore } from "pinia"
import { ref } from "vue"
import { useWebSocket } from "@vueuse/core"

export interface AgentProgress {
  agent: string      // celve / gongzhonghao / zhihu / xiaohongshu / shenjiao / export
  status: string     // running / done / error
  message: string
  timestamp: number
}

export interface ApprovalRequiredEvent {
  type: "approval_required"
  request_id: string
  project_id: string
  stage: string
  artifact: {
    full_content: string
    summary: string
    version: number
  }
}

export const useWsStore = defineStore("ws", () => {
  const connected = ref(false)
  const events = ref<AgentProgress[]>([])
  const currentApproval = ref<ApprovalRequiredEvent | null>(null)
  const wsUrl = `ws://${window.location.host}/ws`

  let ws: ReturnType<typeof useWebSocket> | null = null

  function connect() {
    if (ws) return
    ws = useWebSocket(wsUrl, {
      immediate: true,
      onConnected() {
        connected.value = true
      },
      onDisconnected() {
        connected.value = false
      },
      onMessage(_ws, event) {
        try {
          const data = JSON.parse(event.data)
          // 审批消息
          if (data.type === "approval_required") {
            currentApproval.value = data as ApprovalRequiredEvent
            return
          }
          // 进度消息
          events.value.push(data as AgentProgress)
          // 只保留最近 100 条
          if (events.value.length > 100) {
            events.value = events.value.slice(-100)
          }
        } catch {
          // ignore non-JSON messages
        }
      },
    })
  }

  function disconnect() {
    ws?.close()
    ws = null
    connected.value = false
  }

  function clearEvents() {
    events.value = []
  }

  function sendApprovalAction(
    requestId: string,
    action: "approve" | "revise" | "redo",
    feedback?: string,
  ) {
    if (!ws) return
    ws.send(JSON.stringify({
      action,
      request_id: requestId,
      ...(feedback ? { feedback } : {}),
    }))
    currentApproval.value = null
  }

  function clearApproval() {
    currentApproval.value = null
  }

  function subscribe(projectId: string) {
    if (!ws) return
    ws.send(JSON.stringify({
      action: "subscribe",
      project_id: projectId,
    }))
  }

  return {
    connected, events, currentApproval,
    connect, disconnect, clearEvents,
    sendApprovalAction, clearApproval,
    subscribe,
  }
})
