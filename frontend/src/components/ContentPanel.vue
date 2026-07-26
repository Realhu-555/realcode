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

const channelClass = computed(() => {
  const map: Record<string, string> = {
    gongzhonghao: "border-t-[var(--green)]",
    zhihu: "border-t-[var(--accent)]",
    xiaohongshu: "border-t-[var(--red)]",
  }
  return map[props.channel] ?? "border-t-[var(--purple)]"
})
</script>

<template>
  <div class="card border-t-3" :class="channelClass">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-base font-semibold flex items-center gap-2">
        <span>{{ icon }}</span>
        {{ label }}
      </h3>
      <div v-if="content" class="flex gap-2">
        <n-button text size="small" @click="copyContent(content)">
          {{ copied ? '✅ 已复制' : '📋 复制' }}
        </n-button>
        <n-button text size="small" @click="downloadMarkdown(content, channel)">
          📥 下载
        </n-button>
      </div>
    </div>

    <n-spin :show="loading">
      <div v-if="content" class="prose prose-invert max-w-none text-sm leading-relaxed whitespace-pre-wrap max-h-600px overflow-y-auto">
        {{ content }}
      </div>
      <div v-else-if="loading" class="text-dim text-center py-8">
        正在生成{{ label }}...
      </div>
      <div v-else class="text-dim text-center py-8">
        等待生成
      </div>
    </n-spin>
  </div>
</template>
