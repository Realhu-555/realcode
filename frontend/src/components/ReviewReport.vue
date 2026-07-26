<script setup lang="ts">
defineProps<{
  report: string | null
  loading: boolean
}>()
</script>

<template>
  <div class="card border-t-3 border-t-[var(--yellow)]">
    <h3 class="section-title flex items-center gap-2">
      <span>🔍</span>
      审校报告
    </h3>

    <n-spin :show="loading">
      <div v-if="report" class="prose prose-invert max-w-none text-sm leading-relaxed whitespace-pre-wrap max-h-600px overflow-y-auto">
        {{ report }}
      </div>
      <div v-else-if="loading" class="text-dim text-center py-8">
        审校中...
      </div>
      <div v-else class="text-dim text-center py-8">
        等待审校
      </div>
    </n-spin>
  </div>
</template>
