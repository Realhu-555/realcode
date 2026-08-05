<script setup lang="ts">
import { ref, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useProjectStore } from "../stores/project"
import { useWsStore } from "../stores/ws"
import StrategyCard from "../components/StrategyCard.vue"
import ApprovalPanel from "../components/ApprovalPanel.vue"
import ProgressTimeline from "../components/ProgressTimeline.vue"
import { confirmStrategy } from "../api/client"

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const wsStore = useWsStore()

const projectId = route.params.projectId as string
const confirming = ref(false)

onMounted(async () => {
  wsStore.connect()
  // 等 WebSocket 连上后订阅项目
  await new Promise(r => setTimeout(r, 300))
  wsStore.subscribe(projectId)
  await projectStore.refresh()
})

// ── 开始确认（调用 confirm-strategy API，阻塞等待审批+生成） ──
async function handleStartConfirm() {
  confirming.value = true
  try {
    const result = await confirmStrategy(projectId)
    projectStore.status = result
    router.push(`/preview/${projectId}`)
  } catch (e: any) {
    // API 不可用时，走 mock 跳转
    console.warn("[dev] confirmStrategy 失败，使用模拟数据", e)
    router.push(`/preview/${projectId}`)
  } finally {
    confirming.value = false
  }
}

// ── ApprovalPanel 事件处理 ──
function handleApprove() {
  const approval = wsStore.currentApproval
  if (!approval) return
  wsStore.sendApprovalAction(approval.request_id, "approve")
}

function handleRevise(feedback: string) {
  const approval = wsStore.currentApproval
  if (!approval) return
  wsStore.sendApprovalAction(approval.request_id, "revise", feedback)
}

function handleRedo() {
  const approval = wsStore.currentApproval
  if (!approval) return
  wsStore.sendApprovalAction(approval.request_id, "redo")
}

// 策略版本跟随审批更新（revise/redo 后 version 变化）
const strategyContent = ref(projectStore.status?.strategy?.full_content ?? "")
const strategyVersion = ref(1)

watch(() => wsStore.currentApproval, (approval) => {
  if (approval) {
    strategyContent.value = approval.artifact.full_content
    strategyVersion.value = approval.artifact.version
  }
})
</script>

<template>
  <div class="h-full overflow-y-auto">
    <div class="max-w-2xl mx-auto px-8 py-10 space-y-6">
      <!-- 页头 -->
      <div class="flex items-center justify-between animate-enter">
        <div>
          <h2 class="heading-display text-2xl">策略确认</h2>
          <p class="text-sm text-dim mt-1">
            确认内容策略后再开始生成
            <span v-if="strategyVersion > 1" class="text-accent">（v{{ strategyVersion }}）</span>
          </p>
        </div>
        <span class="tag-accent">策略阶段</span>
      </div>

      <!-- 策略卡片（纯展示） -->
      <StrategyCard
        :strategy="strategyContent || (projectStore.status?.strategy?.full_content ?? '')"
        :loading="projectStore.loading"
      />

      <!-- 确认按钮 / ApprovalPanel -->
      <div v-if="!wsStore.currentApproval" class="animate-enter">
        <button
          class="btn-primary flex items-center gap-2 px-6 py-3 text-base disabled:opacity-30 disabled:cursor-not-allowed"
          :disabled="confirming || !projectStore.status?.strategy?.full_content"
          @click="handleStartConfirm"
        >
          <n-spin :size="18" v-if="confirming" />
          <span v-else>✅</span>
          <span>{{ confirming ? "处理中…" : "确认策略，开始生成" }}</span>
        </button>
      </div>

      <ApprovalPanel
        v-if="wsStore.currentApproval"
        :stage="wsStore.currentApproval.stage"
        :content="wsStore.currentApproval.artifact.full_content"
        :request-id="wsStore.currentApproval.request_id"
        :timeout-seconds="300"
        @approve="handleApprove"
        @revise="handleRevise"
        @redo="handleRedo"
      />

      <!-- 进度 -->
      <ProgressTimeline />
    </div>
  </div>
</template>
