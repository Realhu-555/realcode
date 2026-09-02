<script setup lang="ts">
import { computed, ref } from "vue"
import { useMessage } from "naive-ui"
import { useRouter } from "vue-router"
import { addGisModel, testGisModel, type GisModelInfo } from "../api/gis"

interface ModelPreset {
  key: string
  label: string
  base_url: string
  model: string
  need_key: boolean
  note?: string
}

const PRESETS: ModelPreset[] = [
  { key: "deepseek", label: "DeepSeek", base_url: "https://api.deepseek.com", model: "deepseek-chat", need_key: true },
  { key: "qwen", label: "Qwen 通义", base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1", model: "qwen-plus", need_key: true },
  { key: "zhipu", label: "Zhipu GLM", base_url: "https://open.bigmodel.cn/api/paas/v4", model: "glm-4-plus", need_key: true },
  { key: "kimi", label: "Kimi", base_url: "https://api.moonshot.cn/v1", model: "moonshot-v1-8k", need_key: true },
  { key: "minimax", label: "MiniMax", base_url: "https://api.minimaxi.com/v1", model: "MiniMax-Text-01", need_key: true },
  { key: "openrouter", label: "OpenRouter", base_url: "https://openrouter.ai/api/v1", model: "auto", need_key: true },
  { key: "ollama", label: "Ollama Local", base_url: "http://localhost:11434/v1", model: "qwen2.5:7b", need_key: false, note: "本地模型无需 Key，请把模型名改成你本机 ollama list 里的名称" },
  { key: "custom", label: "Custom 自定义", base_url: "", model: "", need_key: true },
]

const router = useRouter()
const message = useMessage()

const form = ref<{ label: string; base_url: string; model: string; api_key: string }>({
  label: "",
  base_url: "",
  model: "",
  api_key: "",
})
const activeKey = ref("")
const saving = ref(false)
const testing = ref(false)
const savedModel = ref<GisModelInfo | null>(null)

const selectedPreset = computed(() => PRESETS.find((p) => p.key === activeKey.value) ?? null)
const needKey = computed(() => selectedPreset.value?.need_key ?? true)

function pickPreset(p: ModelPreset) {
  activeKey.value = p.key
  savedModel.value = null
  form.value = { label: p.label, base_url: p.base_url, model: p.model, api_key: "" }
}

function validate() {
  if (!form.value.label.trim()) return "请填写模型名称"
  if (!form.value.base_url.trim() || !/^https?:\/\//i.test(form.value.base_url.trim())) {
    return "Base URL 必须以 http:// 或 https:// 开头"
  }
  if (!form.value.model.trim()) return "请填写模型名"
  return ""
}

async function submit(testAfter = false) {
  const err = validate()
  if (err) {
    message.warning(err)
    return
  }
  saving.value = true
  try {
    const m = await addGisModel({
      label: form.value.label.trim(),
      base_url: form.value.base_url.trim(),
      model: form.value.model.trim(),
      api_key: form.value.api_key.trim() || undefined,
      capabilities: ["chat", "tools"],
    })
    savedModel.value = m
    if (!testAfter) {
      message.success(`已添加 ${m.label}`)
    } else {
      await runTest(m.id)
    }
  } catch (e) {
    message.error(e instanceof Error ? e.message : String(e))
  } finally {
    saving.value = false
  }
}

async function runTest(modelId: string) {
  testing.value = true
  try {
    const res = await testGisModel(modelId)
    message[res.ok ? "success" : "error"](
      res.ok ? `连接成功${res.latency_ms ? `（${res.latency_ms}ms）` : ""}` : res.message || "连接失败",
    )
  } catch (e) {
    message.error(e instanceof Error ? e.message : String(e))
  } finally {
    testing.value = false
  }
}

function goBack() {
  router.push("/gis")
}
</script>

<template>
  <div class="addmodel-page">
    <header class="addmodel-header">
      <button class="addmodel-back" @click="goBack">← 返回</button>
      <h1 class="addmodel-title">添加模型</h1>
      <span class="addmodel-sub">选一个预置模板，只需填 API Key</span>
    </header>

    <main class="addmodel-main">
      <!-- 预置模板选择 -->
      <div class="addmodel-presets">
        <button
          v-for="p in PRESETS"
          :key="p.key"
          class="addmodel-preset"
          :class="{ active: activeKey === p.key }"
          @click="pickPreset(p)"
        >
          <span class="addmodel-preset-name">{{ p.label }}</span>
          <span class="addmodel-preset-url">{{ p.base_url || "手动填写" }}</span>
        </button>
      </div>

      <!-- 表单 -->
      <div class="addmodel-form">
        <label class="addmodel-field">
          <span>名称</span>
          <input v-model="form.label" class="addmodel-input" placeholder="模型显示名称" />
        </label>
        <label class="addmodel-field">
          <span>Base URL</span>
          <input v-model="form.base_url" class="addmodel-input" placeholder="https://api.example.com/v1" />
        </label>
        <label class="addmodel-field">
          <span>模型名</span>
          <input v-model="form.model" class="addmodel-input" placeholder="如 deepseek-chat / qwen2.5:7b" />
        </label>
        <div v-if="needKey" class="addmodel-field">
          <span>API Key</span>
          <input v-model="form.api_key" type="password" class="addmodel-input" placeholder="粘贴你的 API Key" />
        </div>
        <div v-else class="addmodel-field">
          <span>API Key</span>
          <div class="addmodel-local-tip">本地模型无需 Key</div>
        </div>

        <p v-if="selectedPreset?.note" class="addmodel-note">{{ selectedPreset.note }}</p>

        <div class="addmodel-actions">
          <button class="addmodel-btn primary" :disabled="saving" @click="submit(false)">
            {{ saving ? "保存中…" : "保存模型" }}
          </button>
          <button class="addmodel-btn" :disabled="saving || testing" @click="submit(true)">
            {{ testing ? "测试中…" : "保存并测试" }}
          </button>
          <button class="addmodel-btn" :disabled="!savedModel" @click="savedModel && runTest(savedModel.id)">
            测试已保存模型
          </button>
        </div>
        <p v-if="savedModel" class="addmodel-saved">
          已添加：{{ savedModel.label }}（{{ savedModel.id }}），可回主界面在设置里把它设为默认模型。
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.addmodel-page {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
}
.addmodel-header {
  display: flex;
  align-items: baseline;
  gap: 14px;
  padding: 22px 28px 16px;
  border-bottom: 1px solid var(--border);
}
.addmodel-back {
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-dim);
  padding: 5px 14px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 13px;
}
.addmodel-back:hover { color: var(--accent); border-color: var(--accent); }
.addmodel-title {
  font-size: 20px;
  font-weight: 800;
  margin: 0;
}
.addmodel-sub { font-size: 12.5px; color: var(--text-muted); }
.addmodel-main {
  max-width: 720px;
  margin: 24px auto 0;
  padding: 0 20px 60px;
}
.addmodel-presets {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}
.addmodel-preset {
  text-align: left;
  border: 1px solid var(--border);
  background: var(--bg-input);
  border-radius: 12px;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.addmodel-preset:hover { border-color: var(--accent); }
.addmodel-preset.active { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
.addmodel-preset-name { display: block; font-weight: 700; font-size: 13.5px; }
.addmodel-preset-url { display: block; margin-top: 3px; font-size: 11px; color: var(--text-muted); word-break: break-all; }
.addmodel-form {
  margin-top: 22px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--bg-card);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.addmodel-field { display: flex; flex-direction: column; gap: 6px; }
.addmodel-field > span { font-size: 12px; font-weight: 600; color: var(--text-dim); }
.addmodel-input {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  color: var(--text);
  font-size: 13px;
  outline: none;
}
.addmodel-input:focus { border-color: var(--accent); }
.addmodel-local-tip { font-size: 12px; color: var(--success); }
.addmodel-note { margin: 0; font-size: 12px; color: var(--text-muted); background: var(--bg-input); padding: 8px 10px; border-radius: 8px; }
.addmodel-actions { display: flex; gap: 10px; margin-top: 4px; }
.addmodel-btn {
  border: 1px solid var(--border);
  background: var(--bg-input);
  color: var(--text);
  border-radius: 8px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 13px;
}
.addmodel-btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 700; }
.addmodel-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.addmodel-saved { margin: 4px 0 0; font-size: 12.5px; color: var(--success); }
</style>
