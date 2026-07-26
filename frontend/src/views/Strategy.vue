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

function handleModify() {
  modifying.value = true
}

async function submitModify() {
  if (!feedbackText.value.trim()) return
  await projectStore.confirm(feedbackText.value)
  modifying.value = false
  feedbackText.value = ""
}
</script>

<template>
  <div class="h-full overflow-y-auto p-8">
    <div class="max-w-3xl mx-auto space-y-6">
      <!-- 顶栏 -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-bold">策略确认</h2>
          <p class="text-sm text-dim mt-1">确认内容策略后再开始生成</p>
        </div>
        <n-tag type="info" size="small">策略阶段</n-tag>
      </div>

      <!-- 策略卡片 -->
      <StrategyCard
        :strategy="projectStore.status?.strategy?.full_content ?? ''"
        :loading="projectStore.loading"
        @confirm="handleConfirm"
        @modify="handleModify"
      />

      <!-- 修改反馈区域 -->
      <div v-if="modifying" class="card space-y-3">
        <h3 class="text-sm font-semibold">策略修改意见</h3>
        <n-input
          v-model:value="feedbackText"
          type="textarea"
          :rows="4"
          placeholder="描述您希望的策略调整方向，例如：更强调安全卖点、目标用户增加中小企业..."
        />
        <div class="flex gap-3">
          <n-button type="primary" @click="submitModify" :disabled="!feedbackText.trim()">
            提交修改
          </n-button>
          <n-button @click="modifying = false">取消</n-button>
        </div>
      </div>

      <!-- 进度预览 -->
      <ProgressTimeline />
    </div>
  </div>
</template>
