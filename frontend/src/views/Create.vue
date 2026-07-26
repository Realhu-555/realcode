<script setup lang="ts">
import { ref, watch } from "vue"
import { useRouter } from "vue-router"
import { useProjectStore } from "../stores/project"
import { useWsStore } from "../stores/ws"
import GuidedForm from "../components/GuidedForm.vue"
import FreeInput from "../components/FreeInput.vue"

const router = useRouter()
const projectStore = useProjectStore()
const wsStore = useWsStore()

const mode = ref<"form" | "free">("form")
const submitting = ref(false)

// 连接 WebSocket
wsStore.connect()

async function handleFormSubmit(payload: any) {
  submitting.value = true
  try {
    const result = await projectStore.submit({
      mode: "form",
      ...payload,
    })
    router.push(`/strategy/${result.project_id}`)
  } finally {
    submitting.value = false
  }
}

async function handleFreeSubmit(idea: string) {
  submitting.value = true
  try {
    const result = await projectStore.submit({
      mode: "free",
      user_idea: idea,
    })
    router.push(`/strategy/${result.project_id}`)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- 模式切换标签 -->
    <div class="border-b border-[var(--border)] px-8 py-3 flex items-center gap-4">
      <button
        class="px-4 py-1.5 rounded-md text-sm font-medium transition cursor-pointer"
        :class="mode === 'form' ? 'bg-[var(--accent-dim)] text-[var(--accent)]' : 'text-dim hover:text-[var(--text)]'"
        @click="mode = 'form'"
      >
        📝 引导模式
      </button>
      <button
        class="px-4 py-1.5 rounded-md text-sm font-medium transition cursor-pointer"
        :class="mode === 'free' ? 'bg-[var(--accent-dim)] text-[var(--accent)]' : 'text-dim hover:text-[var(--text)]'"
        @click="mode = 'free'"
      >
        ✍️ 自由模式
      </button>
      <span class="text-xs text-dim ml-auto">引导模式填表单，自由模式写描述，效果一样</span>
    </div>

    <!-- 内容区 -->
    <div class="flex-1 overflow-hidden">
      <n-spin :show="submitting" size="large">
        <GuidedForm v-if="mode === 'form'" @submit="handleFormSubmit" />
        <FreeInput v-else @submit="handleFreeSubmit" />
      </n-spin>
    </div>
  </div>
</template>
