<script setup lang="ts">
import { ref } from "vue"

const emit = defineEmits<{
  submit: [idea: string]
}>()

const idea = ref("")
</script>

<template>
  <div class="h-full overflow-y-auto p-8">
    <div class="max-w-2xl mx-auto">
      <h2 class="text-2xl font-bold mb-2">自由模式</h2>
      <p class="text-dim mb-8">直接描述您的产品和营销需求，一切由 AI 分析和策划</p>

      <div class="card">
        <n-input
          v-model:value="idea"
          type="textarea"
          :autosize="{ minRows: 8, maxRows: 20 }"
          placeholder="例如：

我要推广一个开源 RAG 问答系统。
- 目标用户：技术团队负责人
- 核心卖点：支持多格式文档、引用可追溯、内置安全防护
- 品牌调性：专业技术向
- 竞品：ChatPDF、AnythingLLM

请帮我生成公众号、知乎、小红书的营销内容。"
        />
        <div class="mt-4">
          <n-button type="primary" size="large" @click="emit('submit', idea.trim())" :disabled="!idea.trim()">
            开始生成 →
          </n-button>
        </div>
      </div>
    </div>
  </div>
</template>
