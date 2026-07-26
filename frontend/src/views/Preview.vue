<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import { useProjectStore } from "../stores/project"
import { useWsStore } from "../stores/ws"
import ContentPanel from "../components/ContentPanel.vue"
import ReviewReport from "../components/ReviewReport.vue"
import ProgressTimeline from "../components/ProgressTimeline.vue"

const route = useRoute()
const projectStore = useProjectStore()
const wsStore = useWsStore()

const projectId = route.params.projectId as string
const activeTab = ref("gongzhonghao")

const channels = [
  { key: "gongzhonghao", label: "公众号", icon: "📰" },
  { key: "zhihu", label: "知乎", icon: "💡" },
  { key: "xiaohongshu", label: "小红书", icon: "✨" },
  { key: "review", label: "审校报告", icon: "🔍" },
]

onMounted(async () => {
  wsStore.connect()
  await projectStore.refresh()
})

function getContent(channel: string): string | null {
  return projectStore.status?.contents?.[channel]?.full_content ?? null
}

function getReviewReport(): string | null {
  return projectStore.status?.review_report?.full_content ?? null
}

const stageTag = computed(() => {
  const map: Record<string, { cls: string; text: string }> = {
    generating: { cls: "tag-warning", text: "生成中" },
    done: { cls: "tag-success", text: "已完成" },
    review: { cls: "tag-warning", text: "审校中" },
  }
  return map[projectStore.stage] ?? { cls: "tag-accent", text: "等待中" }
})
</script>

<template>
  <div class="h-full overflow-y-auto">
    <div class="max-w-3xl mx-auto px-8 py-10 space-y-6">
      <!-- 页头 -->
      <div class="flex items-center justify-between animate-enter">
        <div>
          <h2 class="heading-display text-2xl">内容预览</h2>
          <p class="text-sm text-dim mt-1">三篇内容并行生成 · 审校完成后可导出</p>
        </div>
        <span :class="stageTag.cls">{{ stageTag.text }}</span>
      </div>

      <!-- 进度 -->
      <ProgressTimeline />

      <!-- 内容Tab -->
      <n-tabs
        v-model:value="activeTab"
        type="line"
        animated
        class="animate-enter stagger-2"
      >
        <n-tab-pane
          v-for="ch in channels"
          :key="ch.key"
          :name="ch.key"
          :tab="`${ch.icon} ${ch.label}`"
        >
          <div class="pt-5">
            <ReviewReport
              v-if="ch.key === 'review'"
              :report="getReviewReport()"
              :loading="projectStore.stage === 'generating' || projectStore.stage === 'review'"
            />
            <ContentPanel
              v-else
              :channel="ch.key"
              :label="ch.label"
              :icon="ch.icon"
              :content="getContent(ch.key)"
              :loading="projectStore.stage === 'generating' && !getContent(ch.key)"
            />
          </div>
        </n-tab-pane>
      </n-tabs>
    </div>
  </div>
</template>
