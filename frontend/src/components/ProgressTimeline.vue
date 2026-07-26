<script setup lang="ts">
import { useAgentProgress } from "../composables/useAgentProgress"

const { isRunning, isDone, totalDone, totalGenerating } = useAgentProgress()

const agents = [
  { id: "celve", label: "策略分析", icon: "🧠" },
  { id: "gongzhonghao", label: "公众号", icon: "📰" },
  { id: "zhihu", label: "知乎", icon: "💡" },
  { id: "xiaohongshu", label: "小红书", icon: "✨" },
  { id: "shenjiao", label: "审校", icon: "🔍" },
]
</script>

<template>
  <div class="card">
    <h3 class="section-title">生成进度</h3>

    <div class="space-y-3">
      <div v-for="agent in agents" :key="agent.id" class="flex items-center gap-3">
        <span class="text-lg w-8">{{ agent.icon }}</span>
        <span class="text-sm w-20">{{ agent.label }}</span>
        <n-progress
          v-if="isRunning(agent.id)"
          type="line"
          :percentage="50"
          :height="6"
          :indicator-placement="'none'"
          processing
          class="flex-1"
        />
        <n-progress
          v-else-if="isDone(agent.id)"
          type="line"
          :percentage="100"
          :height="6"
          :indicator-placement="'none'"
          color="var(--green)"
          class="flex-1"
        />
        <div v-else class="flex-1 h-6px bg-[var(--border)] rounded-full" />
        <span class="text-xs text-dim w-16 text-right">
          {{ isDone(agent.id) ? '✅ 完成' : isRunning(agent.id) ? '生成中...' : '等待' }}
        </span>
      </div>
    </div>

    <div v-if="totalGenerating > 0" class="mt-4 text-sm text-dim text-center">
      正在并行生成 {{ totalGenerating }} 篇内容（已完成 {{ totalDone }}/3）
    </div>
  </div>
</template>
