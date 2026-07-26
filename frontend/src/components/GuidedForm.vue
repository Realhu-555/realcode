<script setup lang="ts">
import { ref } from "vue"

const emit = defineEmits<{
  submit: [payload: {
    product_name: string
    product_description: string
    target_users: string
    key_selling_points: string[]
    brand_tone: string
    competitors: string[]
  }]
}>()

const productName = ref("")
const productDescription = ref("")
const targetUsers = ref("")
const sellingPoints = ref<string[]>([""])
const brandTone = ref("专业")
const competitors = ref<string[]>([""])

const toneOptions = [
  { label: "专业严谨", value: "专业" },
  { label: "轻松亲切", value: "轻松" },
  { label: "极客硬核", value: "极客" },
]

function addSellingPoint() {
  if (sellingPoints.value.length < 5) sellingPoints.value.push("")
}
function removeSellingPoint(index: number) {
  if (sellingPoints.value.length > 1) sellingPoints.value.splice(index, 1)
}
function addCompetitor() {
  competitors.value.push("")
}
function removeCompetitor(index: number) {
  if (competitors.value.length > 1) competitors.value.splice(index, 1)
}

const canSubmit = computed(() =>
  productName.value.trim() && productDescription.value.trim() && targetUsers.value.trim()
)

function handleSubmit() {
  emit("submit", {
    product_name: productName.value.trim(),
    product_description: productDescription.value.trim(),
    target_users: targetUsers.value.trim(),
    key_selling_points: sellingPoints.value.map(s => s.trim()).filter(Boolean),
    brand_tone: brandTone.value,
    competitors: competitors.value.map(s => s.trim()).filter(Boolean),
  })
}
</script>

<template>
  <div class="h-full overflow-y-auto">
    <div class="max-w-xl mx-auto px-8 py-10">
      <!-- 标题区 -->
      <div class="mb-10 animate-enter">
        <h2 class="heading-display text-3xl mb-2">创建营销内容</h2>
        <p class="text-dim text-sm">填写产品信息，AI 为您生成多渠道营销物料</p>
      </div>

      <!-- 表单 -->
      <n-form label-placement="top" size="large" class="space-y-1">
        <!-- 产品名称 -->
        <n-form-item class="animate-enter stagger-1">
          <template #label>
            <span class="font-display text-sm font-semibold tracking-wide">产品名称</span>
          </template>
          <n-input
            v-model:value="productName"
            placeholder="例如：RAG 智能问答系统"
            size="large"
          />
        </n-form-item>

        <!-- 一句话描述 -->
        <n-form-item class="animate-enter stagger-2">
          <template #label>
            <span class="font-display text-sm font-semibold tracking-wide">一句话描述</span>
          </template>
          <n-input
            v-model:value="productDescription"
            type="textarea"
            :rows="2"
            placeholder="用一句话概括产品是什么、解决什么问题"
          />
        </n-form-item>

        <!-- 目标用户 -->
        <n-form-item class="animate-enter stagger-2">
          <template #label>
            <span class="font-display text-sm font-semibold tracking-wide">目标用户</span>
          </template>
          <n-input
            v-model:value="targetUsers"
            placeholder="例如：技术团队负责人、CTO、技术总监"
          />
        </n-form-item>

        <!-- 核心卖点 -->
        <n-form-item class="animate-enter stagger-3">
          <template #label>
            <span class="font-display text-sm font-semibold tracking-wide">核心卖点</span>
          </template>
          <div class="space-y-2 w-full">
            <div v-for="(_, i) in sellingPoints" :key="i" class="flex items-center gap-2">
              <span class="text-xs text-muted w-5 text-right shrink-0">{{ i + 1 }}.</span>
              <n-input
                v-model:value="sellingPoints[i]"
                :placeholder="`卖点 ${i + 1}`"
                class="flex-1"
              />
              <button
                v-if="sellingPoints.length > 1"
                class="w-7 h-7 flex items-center justify-center rounded text-muted hover:text-[var(--danger)] hover:bg-[var(--danger-dim)] transition-colors cursor-pointer shrink-0"
                @click="removeSellingPoint(i)"
              >
                ×
              </button>
            </div>
            <button
              v-if="sellingPoints.length < 5"
              class="text-xs text-[var(--accent)] hover:brightness-110 transition cursor-pointer mt-1"
              @click="addSellingPoint"
            >
              + 添加卖点
            </button>
          </div>
        </n-form-item>

        <!-- 品牌调性 -->
        <n-form-item class="animate-enter stagger-4">
          <template #label>
            <span class="font-display text-sm font-semibold tracking-wide">品牌调性</span>
          </template>
          <n-radio-group v-model:value="brandTone">
            <n-radio-button v-for="opt in toneOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
          </n-radio-group>
        </n-form-item>

        <!-- 竞品 -->
        <n-form-item class="animate-enter stagger-5">
          <template #label>
            <span class="font-display text-sm font-semibold tracking-wide">竞品 <span class="text-muted font-normal">（可选）</span></span>
          </template>
          <div class="space-y-2 w-full">
            <div v-for="(_, i) in competitors" :key="i" class="flex items-center gap-2">
              <n-input v-model:value="competitors[i]" :placeholder="`竞品 ${i + 1}`" class="flex-1" />
              <button
                v-if="competitors.length > 1"
                class="w-7 h-7 flex items-center justify-center rounded text-muted hover:text-[var(--danger)] hover:bg-[var(--danger-dim)] transition-colors cursor-pointer shrink-0"
                @click="removeCompetitor(i)"
              >
                ×
              </button>
            </div>
            <button
              class="text-xs text-[var(--accent)] hover:brightness-110 transition cursor-pointer mt-1"
              @click="addCompetitor"
            >
              + 添加竞品
            </button>
          </div>
        </n-form-item>

        <!-- 提交按钮 -->
        <div class="pt-4 animate-enter stagger-5">
          <button
            class="btn-primary w-full text-base py-3 disabled:opacity-30 disabled:cursor-not-allowed"
            :disabled="!canSubmit"
            @click="handleSubmit"
          >
            开始生成 →
          </button>
        </div>
      </n-form>
    </div>
  </div>
</template>
