<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useProjectStore } from "../stores/project"
import { useWsStore } from "../stores/ws"
import StrategyCard from "../components/StrategyCard.vue"
import ProgressTimeline from "../components/ProgressTimeline.vue"

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const wsStore = useWsStore()

const projectId = route.params.projectId as string
const modifying = ref(false)
const feedbackText = ref("")

onMounted(async () => {
  wsStore.connect()
  await projectStore.refresh()
})

async function handleConfirm() {
  await projectStore.confirm()
  router.push(`/preview/${projectId}`)
}

async function submitModify() {
  if (!feedbackText.value.trim()) return
  await projectStore.confirm(feedbackText.value)
  modifying.value = false
  feedbackText.value = ""
}
</script>

<template>
  <div class="h-full overflow-y-auto">
    <div class="max-w-2xl mx-auto px-8 py-10 space-y-6">
      <!-- 页头 -->
      <div class="flex items-center justify-between animate-enter">
        <div>
          <h2 class="heading-display text-2xl">策略确认</h2>
          <p class="text-sm text-dim mt-1">确认内容策略后再开始生成</p>
        </div>
        <span class="tag-accent">策略阶段</span>
      </div>

      <!-- 策略卡片 -->
      <StrategyCard
        :strategy="projectStore.status?.strategy?.full_content ?? ''"
        :loading="projectStore.loading"
        @confirm="handleConfirm"
        @modify="modifying = true"
      />

      <!-- 修改反馈 -->
      <div v-if="modifying" class="card animate-enter space-y-4">
        <div class="flex items-center gap-3">
          <div class="accent-line" />
          <h3 class="heading-section">策略修改意见</h3>
        </div>
        <n-input
          v-model:value="feedbackText"
          type="textarea"
          :rows="4"
          placeholder="描述您希望的策略调整方向，例如：更强调安全卖点、目标用户增加中小企业..."
        />
        <div class="flex gap-3">
          <button class="btn-primary text-sm" :disabled="!feedbackText.trim()" @click="submitModify">
            提交修改
          </button>
          <button class="btn-ghost text-sm" @click="modifying = false">取消</button>
        </div>
      </div>

      <!-- 进度 -->
      <ProgressTimeline />
    </div>
  </div>
</template>
