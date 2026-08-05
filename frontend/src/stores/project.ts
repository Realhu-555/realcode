import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { createProject, getProjectStatus, listProjects, type CreateProjectPayload, type ProjectStatus, type ProjectListItem } from "../api/client"
import { useWsStore } from "./ws"
import { MOCK_STATUS_STRATEGY, MOCK_STATUS_PREVIEW } from "./mock"

export const useProjectStore = defineStore("project", () => {
  const currentProjectId = ref<string | null>(null)
  const status = ref<ProjectStatus | null>(null)
  const projectList = ref<ProjectListItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentRequestId = ref<string | null>(null)

  const stage = computed(() => status.value?.stage ?? "idle")

  async function submit(payload: CreateProjectPayload) {
    loading.value = true
    error.value = null
    try {
      const result = await createProject(payload)
      currentProjectId.value = result.project_id
      status.value = result
      return result
    } catch (e: any) {
      // 后端不可用时注入 mock 数据
      console.warn("[dev] API 不可用，使用模拟策略数据")
      currentProjectId.value = "mock-strategy"
      status.value = MOCK_STATUS_STRATEGY
      return { project_id: "mock-strategy" }
    } finally {
      loading.value = false
    }
  }

  async function refresh() {
    if (!currentProjectId.value) return
    try {
      status.value = await getProjectStatus(currentProjectId.value)
    } catch (e: any) {
      console.warn("[dev] API 不可用，使用模拟数据")
      if (currentProjectId.value === "mock-strategy" || status.value?.stage === "confirming") {
        status.value = MOCK_STATUS_STRATEGY
      } else {
        status.value = MOCK_STATUS_PREVIEW
      }
    }
  }

  // ── 三操作（通过 WebSocket 发送，唤醒后端 ApprovalGate） ──
  function approve(requestId: string) {
    currentRequestId.value = null
    useWsStore().sendApprovalAction(requestId, "approve")
  }

  function revise(requestId: string, feedback: string) {
    currentRequestId.value = null
    useWsStore().sendApprovalAction(requestId, "revise", feedback)
  }

  function redo(requestId: string) {
    currentRequestId.value = null
    useWsStore().sendApprovalAction(requestId, "redo")
  }

  // 兼容旧 UI（直接确认策略 → 已废弃，改用 approve/revise/redo）
  async function confirm(_feedback?: string) {
    if (!currentRequestId.value) return
    if (_feedback) {
      revise(currentRequestId.value, _feedback)
    } else {
      approve(currentRequestId.value)
    }
  }

  function setCurrentRequestId(requestId: string) {
    currentRequestId.value = requestId
  }

  async function loadProjects() {
    try {
      const result = await listProjects()
      projectList.value = result.projects || []
    } catch {
      // 后端不可用时忽略
    }
  }

  function reset() {
    currentProjectId.value = null
    status.value = null
    error.value = null
    currentRequestId.value = null
  }

  return {
    currentProjectId, status, projectList, loading, error, stage,
    currentRequestId,
    submit, refresh, confirm, reset, loadProjects,
    approve, revise, redo, setCurrentRequestId,
  }
})
