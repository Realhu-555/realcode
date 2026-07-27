import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { createProject, getProjectStatus, confirmStrategy, type CreateProjectPayload, type ProjectStatus } from "../api/client"
import { MOCK_STATUS_STRATEGY, MOCK_STATUS_PREVIEW } from "./mock"

export const useProjectStore = defineStore("project", () => {
  const currentProjectId = ref<string | null>(null)
  const status = ref<ProjectStatus | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

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

  async function confirm(feedback?: string) {
    if (!currentProjectId.value) return
    loading.value = true
    try {
      const result = await confirmStrategy(currentProjectId.value, true, feedback)
      status.value = result
      return result
    } catch (e: any) {
      console.warn("[dev] API 不可用，使用模拟生成数据")
      currentProjectId.value = "mock-preview"
      status.value = MOCK_STATUS_PREVIEW
      return { project_id: "mock-preview" }
    } finally {
      loading.value = false
    }
  }

  function reset() {
    currentProjectId.value = null
    status.value = null
    error.value = null
  }

  return { currentProjectId, status, loading, error, stage, submit, refresh, confirm, reset }
})
