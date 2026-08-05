<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue"

const props = defineProps<{
  stage: string           // 当前阶段名称，如 "策略"
  content: string         // 待审批内容
  requestId: string       // 审批请求 ID
  timeoutSeconds: number  // 初始超时秒数
}>()

const emit = defineEmits<{
  approve: []
  revise: [feedback: string]
  redo: []
}>()

// ── 倒计时 ──
const countdown = ref(props.timeoutSeconds)
let timer: ReturnType<typeof setInterval> | null = null

const isExpiring = computed(() => countdown.value <= 60)
const displayTime = computed(() => {
  const m = Math.floor(countdown.value / 60)
  const s = countdown.value % 60
  return `${m}:${s.toString().padStart(2, "0")}`
})

onMounted(() => {
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer!)
      emit("approve")
    }
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

watch(() => props.timeoutSeconds, (val) => {
  countdown.value = val
})

// ── 修改模式 ──
const revising = ref(false)
const feedbackText = ref("")

function submitRevise() {
  if (!feedbackText.value.trim()) return
  emit("revise", feedbackText.value.trim())
  revising.value = false
  feedbackText.value = ""
}

function handleReviseClick() {
  revising.value = true
}

function cancelRevise() {
  revising.value = false
  feedbackText.value = ""
}

// ── 重做确认 ──
const showRedoConfirm = ref(false)

function confirmRedo() {
  showRedoConfirm.value = false
  emit("redo")
}

// ── 阶段名称映射 ──
const stageLabel = computed(() => {
  const map: Record<string, string> = {
    strategy: "策略文档",
    gongzhonghao: "公众号内容",
    zhihu: "知乎内容",
    xiaohongshu: "小红书内容",
  }
  return map[props.stage] || props.stage
})
</script>

<template>
  <div class="card animate-enter">
    <!-- 头部：阶段 + 倒计时 -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <div class="accent-line" />
        <h3 class="heading-section">{{ stageLabel }} 已生成</h3>
      </div>
      <div
        class="countdown-tag"
        :class="{ 'countdown-expiring': isExpiring }"
      >
        ⏱ {{ displayTime }}
      </div>
    </div>

    <!-- 内容预览 -->
    <div class="prose-content text-sm max-h-[300px] overflow-y-auto mb-5 p-4 bg-bg-raised rounded-lg border border-border-muted">
      <pre class="whitespace-pre-wrap font-sans text-sm">{{ content }}</pre>
    </div>

    <!-- 三按钮 -->
    <div v-if="!revising" class="flex gap-3">
      <button class="btn-primary flex items-center gap-2" @click="emit('approve')">
        <span>✅</span>
        <span>确认</span>
      </button>
      <button class="btn-ghost flex items-center gap-2" @click="handleReviseClick">
        <span>✏️</span>
        <span>修改</span>
      </button>
      <button class="btn-danger-outline flex items-center gap-2" @click="showRedoConfirm = true">
        <span>🔄</span>
        <span>重做</span>
      </button>
    </div>

    <!-- 修改意见输入 -->
    <div v-if="revising" class="space-y-3">
      <n-input
        v-model:value="feedbackText"
        type="textarea"
        :rows="3"
        placeholder="描述您希望的调整方向…"
      />
      <div class="flex gap-3">
        <button
          class="btn-primary text-sm"
          :disabled="!feedbackText.trim()"
          @click="submitRevise"
        >
          提交修改
        </button>
        <button class="btn-ghost text-sm" @click="cancelRevise">取消</button>
      </div>
    </div>

    <!-- 重做确认弹窗 -->
    <n-modal
      :show="showRedoConfirm"
      preset="dialog"
      title="确认重做"
      content="当前产出将被丢弃并重新生成。确定要重做吗？"
      positive-text="确定重做"
      negative-text="取消"
      @positive-click="confirmRedo"
      @negative-click="showRedoConfirm = false"
      @close="showRedoConfirm = false"
    />
  </div>
</template>

<style scoped>
.countdown-tag {
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: var(--tag-bg, rgba(100, 100, 255, 0.1));
  color: var(--tag-color, #6366f1);
  transition: all 0.3s ease;
}

.countdown-expiring {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  animation: pulse-red 1s ease-in-out infinite;
}

@keyframes pulse-red {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.btn-danger-outline {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  background: transparent;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-danger-outline:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.5);
}
</style>
