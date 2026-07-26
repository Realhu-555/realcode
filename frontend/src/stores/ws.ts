import { defineStore } from "pinia"
import { ref } from "vue"
import { useWebSocket } from "@vueuse/core"

export interface AgentProgress {
  agent: string      // celve / gongzhonghao / zhihu / xiaohongshu / shenjiao / export
  status: string     // running / done / error
  message: string
  timestamp: number
}

export const useWsStore = defineStore("ws", () => {
  const connected = ref(false)
  const events = ref<AgentProgress[]>([])
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
          const data = JSON.parse(event.data) as AgentProgress
          events.value.push(data)
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

  return { connected, events, connect, disconnect, clearEvents }
})
