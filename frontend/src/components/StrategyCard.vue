<script setup lang="ts">
defineProps<{
  strategy: string
  loading: boolean
}>()
</script>

<template>
  <div class="card animate-enter">
    <!-- 标题行 -->
    <div class="flex items-center gap-3 mb-5">
      <div class="accent-line" />
      <h3 class="heading-section">内容策略</h3>
    </div>

    <!-- 策略内容 -->
    <n-spin :show="loading">
      <div v-if="strategy" class="prose-content text-sm max-h-[500px] overflow-y-auto">
        {{ strategy }}
      </div>
      <div v-else class="flex flex-col items-center justify-center py-14 text-dim gap-3">
        <div class="text-3xl opacity-50 animate-pulse">🧠</div>
        <p class="text-sm">策略分析中…</p>
      </div>
    </n-spin>
  </div>
</template>
