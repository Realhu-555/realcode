<script setup lang="ts">
defineProps<{
  strategy: string
  loading: boolean
}>()

defineEmits<{
  confirm: []
  modify: []
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
        <p class="text-sm">策略分析中...</p>
      </div>
    </n-spin>

    <n-divider />

    <!-- 操作按钮 -->
    <div class="flex gap-3">
      <button
        class="btn-primary flex items-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed"
        :disabled="!strategy || loading"
        @click="$emit('confirm')"
      >
        <span>✓</span>
        <span>确认策略，开始生成</span>
      </button>
      <n-popover trigger="click" placement="bottom-start" :width="380">
        <template #trigger>
          <button
            class="btn-ghost flex items-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed"
            :disabled="!strategy || loading"
          >
            <span>✎</span>
            <span>我要修改</span>
          </button>
        </template>
        <div class="p-3">
          <p class="text-sm font-medium mb-3">希望如何调整策略？</p>
          <n-input type="textarea" :rows="3" placeholder="例如：更强调安全卖点、目标用户增加中小企业..." />
          <button class="btn-primary w-full mt-3 text-sm">
            提交修改意见
          </button>
        </div>
      </n-popover>
    </div>
  </div>
</template>
