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

function getStatusClass(agentId: string) {
  if (isDone(agentId)) return "text-[var(--success)]"
  if (isRunning(agentId)) return "text-[var(--accent)]"
  return "text-muted"
}
</script>

<template>
  <div class="card animate-enter stagger-5">
    <div class="flex items-center gap-3 mb-5">
      <div class="accent-line" />
      <h3 class="heading-section">生成进度</h3>
    </div>

    <div class="space-y-1">
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="flex items-center gap-3 py-2 px-2 -mx-2 rounded-lg transition-colors hover:bg-[var(--bg-hover)]"
      >
        <!-- 图标 + 名称 -->
        <span class="text-lg w-8 text-center shrink-0" :class="{ 'opacity-40': !isDone(agent.id) && !isRunning(agent.id) }">
          {{ agent.icon }}
        </span>
        <span class="text-sm w-20 shrink-0" :class="getStatusClass(agent.id)">
          {{ agent.label }}
        </span>

        <!-- 进度条 -->
        <div class="flex-1">
          <n-progress
            v-if="isRunning(agent.id)"
            type="line"
            :percentage="50"
            :height="5"
            :show-indicator="false"
            processing
          />
          <n-progress
            v-else-if="isDone(agent.id)"
            type="line"
            :percentage="100"
            :height="5"
            :show-indicator="false"
            :color="'var(--success)'"
          />
          <div v-else class="h-[5px] bg-[var(--border)] rounded-full" />
        </div>

        <!-- 状态文字 -->
        <span class="text-xs w-14 text-right shrink-0" :class="getStatusClass(agent.id)">
          <template v-if="isDone(agent.id)">✓ 完成</template>
          <template v-else-if="isRunning(agent.id)">⏳ 中</template>
          <template v-else>等待</template>
        </span>
      </div>
    </div>

    <!-- 汇总信息 -->
    <div
      v-if="totalGenerating > 0"
      class="mt-4 pt-4 border-t border-[var(--border)] text-xs text-center text-muted"
    >
      并行生成 {{ totalGenerating }} 篇内容 &nbsp;·&nbsp; 已完成 {{ totalDone }}/3
    </div>
  </div>
</template>
