<script setup lang="ts">
defineProps<{
  report: string | null
  loading: boolean
}>()
</script>

<template>
  <div class="card !p-0 overflow-hidden ribbon-review animate-enter">
    <!-- 面板头部 -->
    <div class="flex items-center gap-3 px-6 py-4 bg-[var(--bg-card-hover)] border-b border-[var(--border)]">
      <span class="text-xl">🔍</span>
      <div>
        <h3 class="heading-section !mb-0">审校报告</h3>
        <p class="text-xs text-muted mt-0.5">质量检查 · 一致性校验</p>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="p-6">
      <n-spin :show="loading">
        <div v-if="report" class="prose-content text-sm max-h-[600px] overflow-y-auto">
          {{ report }}
        </div>
        <div v-else-if="loading" class="flex flex-col items-center py-12 text-dim gap-3">
          <div class="w-12 h-12 skeleton rounded-full" />
          <div class="w-48 h-3 skeleton" />
        </div>
        <div v-else class="flex flex-col items-center py-12 text-muted gap-2">
          <span class="text-2xl opacity-40">✅</span>
          <p class="text-sm">等待审校</p>
        </div>
      </n-spin>
    </div>
  </div>
</template>
