<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useProjectStore } from "../stores/project"
import { useWsStore } from "../stores/ws"
import GuidedForm from "../components/GuidedForm.vue"
import FreeInput from "../components/FreeInput.vue"

const router = useRouter()
const projectStore = useProjectStore()
const wsStore = useWsStore()

const mode = ref<"guided" | "free">("guided")
const submitting = ref(false)

wsStore.connect()

async function handleFormSubmit(payload: any) {
  submitting.value = true
  try {
    const result = await projectStore.submit({ mode: "form", ...payload })
    router.push(`/strategy/${result.project_id}`)
  } finally {
    submitting.value = false
  }
}

async function handleFreeSubmit(idea: string) {
  submitting.value = true
  try {
    const result = await projectStore.submit({ mode: "free", user_idea: idea })
    router.push(`/strategy/${result.project_id}`)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- 模式切换 -->
    <div class="border-b border-[var(--border)] bg-[var(--bg-card)]/50 backdrop-blur-sm">
      <div class="max-w-2xl mx-auto px-8 py-3 flex items-center gap-1">
        <button
          class="relative px-5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer"
          :class="mode === 'guided'
            ? 'bg-[var(--accent-dim)] text-[var(--accent)]'
            : 'text-dim hover:text-[var(--text)] hover:bg-[var(--bg-hover)]'"
          @click="mode = 'guided'"
        >
          📝 引导模式
        </button>
        <button
          class="relative px-5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer"
          :class="mode === 'free'
            ? 'bg-[var(--accent-dim)] text-[var(--accent)]'
            : 'text-dim hover:text-[var(--text)] hover:bg-[var(--bg-hover)]'"
          @click="mode = 'free'"
        >
          ✍️ 自由模式
        </button>
        <span class="text-xs text-muted ml-auto hidden sm:block">
          {{ mode === 'guided' ? '填表单，AI 整理策略' : '写描述，AI 自主策划' }}
        </span>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="flex-1 overflow-hidden">
      <n-spin :show="submitting" size="large">
        <GuidedForm v-if="mode === 'guided'" @submit="handleFormSubmit" />
        <FreeInput v-else @submit="handleFreeSubmit" />
      </n-spin>
    </div>
  </div>
</template>
