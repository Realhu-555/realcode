<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { useProjectStore } from "../stores/project"
import { useWsStore } from "../stores/ws"
import { useImageUpload } from "../composables/useImageUpload"
import { listModels, type ModelInfo } from "../api/client"
import GuidedForm from "../components/GuidedForm.vue"
import FreeInput from "../components/FreeInput.vue"

const router = useRouter()
const projectStore = useProjectStore()
const wsStore = useWsStore()
const { images, uploading, error: imgError, addImages, removeImage, clear: clearImages } = useImageUpload(5)

const mode = ref<"guided" | "free">("guided")
const submitting = ref(false)

// 模型选择（留空 = 跟随系统默认）
const models = ref<ModelInfo[]>([])
const modelPreference = ref<string>("")
const modelOptions = computed(() =>
  models.value.map((m) => ({ label: m.label, value: m.id }))
)

onMounted(async () => {
  try {
    const res = await listModels()
    models.value = res.models
  } catch {
    models.value = []
  }
})

wsStore.connect()

async function handleFormSubmit(payload: any) {
  submitting.value = true
  try {
    const result = await projectStore.submit({
      mode: "form",
      ...payload,
      image_urls: images.value.length > 0 ? [...images.value] : undefined,
      model_preference: modelPreference.value || undefined,
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
      image_urls: images.value.length > 0 ? [...images.value] : undefined,
      model_preference: modelPreference.value || undefined,
    })
    router.push(`/strategy/${result.project_id}`)
  } finally {
    submitting.value = false
  }
}

// 文件拖拽/选择
function onFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    addImages(input.files)
    input.value = "" // 允许重复选同一文件
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

    <!-- 模型选择（两种模式共用） -->
    <div class="border-b border-[var(--border)] bg-[var(--bg-card)]/50">
      <div class="max-w-2xl mx-auto px-8 py-2 flex items-center gap-3">
        <span class="text-xs text-muted shrink-0">🤖 生成模型</span>
        <n-select
          v-model:value="modelPreference"
          :options="modelOptions"
          size="small"
          clearable
          placeholder="跟随系统默认（DeepSeek）"
          class="!w-56"
        />
        <span class="text-xs text-muted hidden sm:block">主模型故障自动切换备用，全程无感</span>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="flex-1 overflow-hidden">
      <n-spin :show="submitting" size="large">
        <div class="h-full flex flex-col">
          <div class="flex-1 overflow-hidden">
            <GuidedForm v-if="mode === 'guided'" @submit="handleFormSubmit" />
            <FreeInput v-else @submit="handleFreeSubmit" />
          </div>

          <!-- 图片上传区（两种模式共用） -->
          <div class="shrink-0 border-t border-[var(--border)] bg-[var(--bg-card)]/50">
            <div class="max-w-2xl mx-auto px-8 py-3">
              <div class="flex items-center gap-4">
                <!-- 上传按钮 -->
                <label class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-dim border border-dashed border-[var(--border)] cursor-pointer hover:border-[var(--accent)] hover:text-[var(--accent)] transition-colors">
                  <span>🖼</span>
                  <span>{{ uploading ? '处理中…' : '添加图片' }}</span>
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    class="hidden"
                    @change="onFileInput"
                    :disabled="uploading"
                  />
                </label>

                <!-- 缩略图预览 -->
                <div class="flex items-center gap-2 flex-1 overflow-x-auto">
                  <div
                    v-for="(url, i) in images"
                    :key="i"
                    class="relative group shrink-0"
                  >
                    <img
                      :src="url"
                      class="w-10 h-10 rounded object-cover border border-[var(--border)]"
                    />
                    <button
                      class="absolute -top-1.5 -right-1.5 w-4 h-4 flex items-center justify-center rounded-full bg-[var(--bg-card)] border border-[var(--border)] text-[10px] text-muted opacity-0 group-hover:opacity-100 hover:text-[var(--danger)] transition-all cursor-pointer"
                      @click="removeImage(i)"
                    >
                      ×
                    </button>
                  </div>
                </div>

                <!-- 提示 -->
                <span v-if="images.length === 0" class="text-xs text-muted shrink-0">
                  支持上传产品截图、海报等
                </span>

                <!-- 错误 -->
                <span v-if="imgError" class="text-xs text-[var(--danger)] shrink-0">{{ imgError }}</span>
              </div>
            </div>
          </div>
        </div>
      </n-spin>
    </div>
  </div>
</template>
