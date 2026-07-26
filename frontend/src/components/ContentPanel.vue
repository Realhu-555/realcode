<script setup lang="ts">
import { computed } from "vue"
import { useExport } from "../composables/useExport"

const props = defineProps<{
  channel: string
  label: string
  icon: string
  content: string | null
  loading: boolean
}>()

const { copyContent, downloadMarkdown, copied } = useExport()

const ribbonClass = computed(() => `ribbon-${props.channel}`)

const channelMeta = computed(() => {
  const map: Record<string, { color: string; description: string }> = {
    gongzhonghao: { color: "var(--ch-gongzhonghao)", description: "深度长文 · 专业调性" },
    zhihu: { color: "var(--ch-zhihu)", description: "知识分享 · 理性洞察" },
    xiaohongshu: { color: "var(--ch-xiaohongshu)", description: "种草笔记 · 视觉引导" },
  }
  return map[props.channel] ?? { color: "var(--accent)", description: "" }
})
</script>

<template>
  <div class="card !p-0 overflow-hidden animate-enter" :class="ribbonClass">
    <!-- 面板头部 -->
    <div class="flex items-center justify-between px-6 py-4 bg-[var(--bg-card-hover)] border-b border-[var(--border)]">
      <div class="flex items-center gap-3">
        <span class="text-xl">{{ icon }}</span>
        <div>
          <h3 class="heading-section !mb-0">{{ label }}</h3>
          <p class="text-xs text-muted mt-0.5">{{ channelMeta.description }}</p>
        </div>
      </div>
      <div v-if="content" class="flex gap-1">
        <button
          class="btn-ghost text-xs !px-3 !py-1.5"
          @click="copyContent(content)"
        >
          {{ copied ? '✓ 已复制' : '📋 复制' }}
        </button>
        <button
          class="btn-ghost text-xs !px-3 !py-1.5"
          @click="downloadMarkdown(content, channel)"
        >
          📥 下载
        </button>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="p-6">
      <n-spin :show="loading">
        <div v-if="content" class="prose-content text-sm max-h-[600px] overflow-y-auto">
          {{ content }}
        </div>
        <div v-else-if="loading" class="flex flex-col items-center py-12 text-dim gap-3">
          <div class="w-12 h-12 skeleton rounded-full" />
          <div class="w-48 h-3 skeleton" />
        </div>
        <div v-else class="flex flex-col items-center py-12 text-muted gap-2">
          <span class="text-2xl opacity-40">📝</span>
          <p class="text-sm">等待生成</p>
        </div>
      </n-spin>
    </div>
  </div>
</template>
