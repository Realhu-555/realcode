<script setup lang="ts">
defineProps<{
  strategy: string
  loading: boolean
}>()

defineEmits<{
  confirm: [feedback?: string]
  modify: [feedback: string]
}>()
</script>

<template>
  <div class="card">
    <h3 class="section-title">📋 内容策略</h3>

    <n-spin :show="loading">
      <div v-if="strategy" class="prose prose-invert max-w-none text-sm leading-relaxed whitespace-pre-wrap">
        {{ strategy }}
      </div>
      <div v-else class="text-dim text-center py-12">
        策略生成中...
      </div>
    </n-spin>

    <n-divider />

    <div class="flex gap-3">
      <n-button type="primary" @click="$emit('confirm')" :disabled="!strategy || loading">
        ✅ 确认策略，开始生成内容
      </n-button>
      <n-popover trigger="click" placement="bottom-start" :width="400">
        <template #trigger>
          <n-button secondary :disabled="!strategy || loading">
            📝 我要修改
          </n-button>
        </template>
        <div class="p-2">
          <p class="text-sm text-dim mb-2">请描述您希望如何调整策略：</p>
          <n-input type="textarea" :rows="3" placeholder="例如：希望更强调安全性卖点..." />
          <n-button type="primary" size="small" class="mt-2 w-full">
            提交修改意见
          </n-button>
        </div>
      </n-popover>
    </div>
  </div>
</template>
