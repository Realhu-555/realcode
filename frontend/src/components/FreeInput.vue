<script setup lang="ts">
import { ref } from "vue"

const emit = defineEmits<{
  submit: [idea: string]
}>()

const idea = ref("")
</script>

<template>
  <div class="h-full overflow-y-auto">
    <div class="max-w-xl mx-auto px-8 py-10">
      <!-- 标题区 -->
      <div class="mb-10 animate-enter">
        <h2 class="heading-display text-3xl mb-2">自由模式</h2>
        <p class="text-dim text-sm">直接描述产品与营销需求，AI 自主分析策划</p>
      </div>

      <!-- 输入卡片 -->
      <div class="card animate-enter stagger-1 !p-0 overflow-hidden">
        <n-input
          v-model:value="idea"
          type="textarea"
          :autosize="{ minRows: 10, maxRows: 22 }"
          placeholder="例如：

我要推广一个开源 RAG 问答系统。
- 目标用户：技术团队负责人
- 核心卖点：支持多格式文档、引用可追溯、内置安全防护
- 品牌调性：专业技术向
- 竞品：ChatPDF、AnythingLLM

请帮我生成公众号、知乎、小红书的营销内容。"
          class="!border-0 !rounded-none"
        />
        <div
          class="flex items-center justify-between px-5 py-3 border-t border-[var(--border)] bg-[var(--bg-card-hover)]"
        >
          <span class="text-xs text-muted">{{ idea.length > 0 ? `${idea.length} 字` : '描述越详细，结果越精准' }}</span>
          <button
            class="btn-primary text-sm disabled:opacity-30 disabled:cursor-not-allowed"
            :disabled="!idea.trim()"
            @click="emit('submit', idea.trim())"
          >
            开始生成 →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
