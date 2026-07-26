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
  <div class="h-full overflow-y-auto p-8">
    <div class="max-w-2xl mx-auto">
      <h2 class="text-2xl font-bold mb-2">创建营销内容</h2>
      <p class="text-dim mb-8">填写产品信息，AI 将为您生成多渠道营销物料</p>

      <n-form label-placement="top" size="large">
        <n-form-item label="产品名称" required>
          <n-input v-model:value="productName" placeholder="例如：RAG 智能问答系统" />
        </n-form-item>

        <n-form-item label="一句话描述" required>
          <n-input v-model:value="productDescription" type="textarea" :rows="2"
            placeholder="用一句话概括产品是什么、解决什么问题" />
        </n-form-item>

        <n-form-item label="目标用户" required>
          <n-input v-model:value="targetUsers"
            placeholder="例如：技术团队负责人、CTO、技术总监" />
        </n-form-item>

        <n-form-item label="核心卖点" required>
          <div class="space-y-2 w-full">
            <div v-for="(_, i) in sellingPoints" :key="i" class="flex gap-2">
              <n-input v-model:value="sellingPoints[i]" :placeholder="`卖点 ${i + 1}`" class="flex-1" />
              <n-button v-if="sellingPoints.length > 1" @click="removeSellingPoint(i)" text type="error" size="small">
                ✕
              </n-button>
            </div>
            <n-button v-if="sellingPoints.length < 5" @click="addSellingPoint" text type="primary" size="small">
              + 添加卖点
            </n-button>
          </div>
        </n-form-item>

        <n-form-item label="品牌调性">
          <n-radio-group v-model:value="brandTone">
            <n-radio-button v-for="opt in toneOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
          </n-radio-group>
        </n-form-item>

        <n-form-item label="竞品（可选）">
          <div class="space-y-2 w-full">
            <div v-for="(_, i) in competitors" :key="i" class="flex gap-2">
              <n-input v-model:value="competitors[i]" :placeholder="`竞品 ${i + 1}`" class="flex-1" />
              <n-button v-if="competitors.length > 1" @click="removeCompetitor(i)" text type="error" size="small">
                ✕
              </n-button>
            </div>
            <n-button @click="addCompetitor" text type="primary" size="small">
              + 添加竞品
            </n-button>
          </div>
        </n-form-item>

        <div class="mt-6">
          <n-button type="primary" size="large" @click="handleSubmit"
            :disabled="!productName || !productDescription || !targetUsers">
            开始生成 →
          </n-button>
        </div>
      </n-form>
    </div>
  </div>
</template>
