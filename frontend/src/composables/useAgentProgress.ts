import { computed } from "vue"
import { useWsStore, type AgentProgress } from "../stores/ws"

export function useAgentProgress() {
  const wsStore = useWsStore()

  const agentStatuses = computed(() => {
    const map = new Map<string, AgentProgress>()
    for (const e of wsStore.events) {
      map.set(e.agent, e)
    }
    return map
  })

  function isRunning(agent: string): boolean {
    return agentStatuses.value.get(agent)?.status === "running"
  }

  function isDone(agent: string): boolean {
    return agentStatuses.value.get(agent)?.status === "done"
  }

  function getMessage(agent: string): string {
    return agentStatuses.value.get(agent)?.message ?? ""
  }

  const totalDone = computed(() =>
    ["gongzhonghao", "zhihu", "xiaohongshu"].filter(isDone).length
  )
  const totalGenerating = computed(() =>
    ["gongzhonghao", "zhihu", "xiaohongshu"].filter(isRunning).length
  )

  wsStore.connect()

  return { agentStatuses, isRunning, isDone, getMessage, totalDone, totalGenerating }
}
