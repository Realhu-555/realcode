import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { createProject, getProjectStatus, confirmStrategy, type CreateProjectPayload, type ProjectStatus } from "../api/client"

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
      error.value = e?.message ?? "提交失败"
      throw e
    } finally {
      loading.value = false
    }
  }

  async function refresh() {
    if (!currentProjectId.value) return
    try {
      status.value = await getProjectStatus(currentProjectId.value)
    } catch (e: any) {
      error.value = e?.message ?? "刷新失败"
    }
  }

  async function confirm(feedback?: string) {
    if (!currentProjectId.value) return
    loading.value = true
    try {
      const result = await confirmStrategy(currentProjectId.value, true, feedback)
      status.value = result
      return result
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
