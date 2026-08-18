<script setup lang="ts">
import { computed, ref } from "vue"
import { useMessage } from "naive-ui"
import { useTheme } from "../composables/useTheme"
import {
  uploadGisFile,
  runGisAssistant,
  objectUrlFor,
  type GisAssistantResult,
} from "../api/gis"

useTheme()

const message = useMessage()

const request = ref("把 gdp_demo.csv 按省份做分级设色图，并导出分级统计 summary.csv")
const dataFile = ref("")
const fileName = ref("")
const uploading = ref(false)
const running = ref(false)
const error = ref("")
const result = ref<GisAssistantResult | null>(null)
const pngArtifacts = ref<{ name: string; url: string }[]>([])
const fileArtifacts = ref<{ name: string; url: string; ext: string }[]>([])

const canSubmit = computed(() => request.value.trim().length > 0 && !running.value)

// 工具分组（仅供展示）
const toolGroups = [
  { label: "数据接入", tools: ["load_data", "inspect_data"] },
  { label: "空间分析", tools: ["buffer", "overlay", "summarize"] },
  { label: "可视化", tools: ["choropleth", "scatter_plot"] },
  { label: "导出", tools: ["export_geojson", "finish"] },
]

async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploading.value = true
  error.value = ""
  try {
    const res = await uploadGisFile(file)
    if (!res.success || !res.path) {
      error.value = res.error || "上传失败"
      return
    }
    dataFile.value = res.path
    fileName.value = file.name
    message.success(`已上传 ${file.name}`)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    uploading.value = false
    input.value = ""
  }
}

function toolStatusText(step: { result: Record<string, unknown> }): string {
  const st = String(step.result.status ?? "?")
  if (st === "ok") return "成功"
  if (st === "error") return String(step.result.error ?? "失败")
  return st
}

function toolArgsText(args: Record<string, unknown>): string {
  try {
    return JSON.stringify(args)
  } catch {
    return ""
  }
}

function stepStatus(step: { result: Record<string, unknown> }): "ok" | "err" | "other" {
  const st = String(step.result.status ?? "?")
  if (st === "ok") return "ok"
  if (st === "error") return "err"
  return "other"
}

async function onSubmit() {
  if (!canSubmit.value) return
  running.value = true
  error.value = ""
  result.value = null
  pngArtifacts.value = []
  fileArtifacts.value = []
  try {
    const res = await runGisAssistant(request.value, dataFile.value || undefined)
    result.value = res
    if (res.stage === "error") {
      error.value = res.error_message || "执行失败"
      return
    }
    for (const name of res.outputs) {
      const url = await objectUrlFor(name)
      if (name.toLowerCase().endsWith(".png")) {
        pngArtifacts.value.push({ name, url })
      } else {
        const ext = name.split(".").pop()?.toUpperCase() || "FILE"
        fileArtifacts.value.push({ name, url, ext })
      }
    }
    message.success(`完成，共 ${res.outputs.length} 个产物`)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    running.value = false
  }
}

function download(url: string, name: string) {
  const a = document.createElement("a")
  a.href = url
  a.download = name
  a.click()
}
</script>

<template>
  <div class="gis-page">
    <!-- 氛围背景 -->
    <div class="gis-bg" aria-hidden="true">
      <div class="gis-bg-grid" />
      <div class="gis-bg-glow" />
    </div>

    <!-- 顶部 -->
    <header class="gis-header">
      <div class="mx-auto max-w-7xl px-6 lg:px-8 py-5 flex items-center justify-between gap-4">
        <div class="flex items-center gap-4 min-w-0">
          <div class="gis-seal shrink-0">制</div>
          <div class="min-w-0">
            <h1 class="font-display text-xl font-black tracking-tight">GIS 智能助手</h1>
            <p class="text-xs text-dim mt-0.5 tracking-wide truncate">自然语言驱动 GIS 引擎 · 工具调用全轨迹可审计</p>
          </div>
        </div>
        <div class="flex items-center gap-2.5 shrink-0">
          <span class="gis-badge">9 工具就绪</span>
          <span class="gis-status">
            <span class="gis-status-dot" />
            引擎在线
          </span>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-7xl px-6 lg:px-8 pb-10 grid gap-6 lg:grid-cols-[400px_1fr] items-start">
      <!-- ===== 左：输入区 ===== -->
      <section class="space-y-5">
        <!-- ① 数据文件 -->
        <div class="gis-card animate-enter">
          <div class="flex items-center gap-2.5 mb-4">
            <span class="gis-step-no">一</span>
            <h2 class="heading-section">数据文件</h2>
            <span class="text-xs text-muted ml-auto">可选</span>
          </div>

          <label class="gis-upload" :class="{ 'gis-upload-done': fileName }">
            <input type="file" accept=".csv,.geojson,.json,.zip" class="hidden" :disabled="running" @change="onFileSelected" />

            <!-- 未上传 -->
            <template v-if="!fileName">
              <span class="gis-upload-icon">🗺</span>
              <span class="text-sm font-medium">点击选择数据文件</span>
              <span class="text-xs text-muted">支持 CSV / GeoJSON / JSON / ZIP</span>
              <span class="text-[11px] text-muted/70 mt-1">未上传时，将尝试从引擎演示数据目录查找</span>
            </template>

            <!-- 已上传 -->
            <template v-else>
              <div class="flex items-center gap-3 w-full">
                <span class="gis-file-icon">📄</span>
                <div class="text-left min-w-0 flex-1">
                  <p class="text-sm font-medium truncate">{{ fileName }}</p>
                  <p class="text-xs text-muted">{{ uploading ? "上传中…" : "已就绪 · 点击可重新选择" }}</p>
                </div>
                <span class="gis-chip gis-chip-ok shrink-0">✓ 已上传</span>
              </div>
            </template>
          </label>
        </div>

        <!-- ② 你的需求 -->
        <div class="gis-card animate-enter stagger-1">
          <div class="flex items-center gap-2.5 mb-4">
            <span class="gis-step-no">二</span>
            <h2 class="heading-section">你的需求</h2>
          </div>
          <n-input
            v-model:value="request"
            type="textarea"
            :rows="5"
            placeholder="例如：找出 gdp_demo.csv 中 gdp 最高的省份并画散点图"
            :disabled="running"
          />
          <div class="mt-2 flex items-center justify-between text-xs text-muted">
            <span>自然语言描述分析目标与出图要求</span>
            <span class="font-mono">{{ request.length }}</span>
          </div>
        </div>

        <!-- ③ 可用工具 -->
        <div class="gis-card animate-enter stagger-2">
          <div class="flex items-center gap-2.5 mb-4">
            <span class="gis-step-no">三</span>
            <h2 class="heading-section">可用工具</h2>
            <span class="text-xs text-muted ml-auto">9 个已就绪</span>
          </div>
          <div v-for="group in toolGroups" :key="group.label" class="mb-3.5 last:mb-0">
            <p class="gis-group-label">{{ group.label }}</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="t in group.tools" :key="t" class="gis-tool-pill">{{ t }}</span>
            </div>
          </div>
        </div>

        <!-- 执行按钮 -->
        <button class="gis-run-btn animate-enter stagger-3" :disabled="!canSubmit" @click="onSubmit">
          <span v-if="!running">▸ 开始分析</span>
          <span v-else class="flex items-center gap-2.5">
            <span class="gis-spinner" />
            GIS 引擎执行中…
          </span>
        </button>

        <p v-if="error" class="gis-error animate-enter">{{ error }}</p>
      </section>

      <!-- ===== 右：结果区 ===== -->
      <section class="space-y-5 min-w-0">
        <!-- 运行中 -->
        <div v-if="running" class="gis-card p-10 flex flex-col items-center gap-4 text-sm text-dim">
          <span class="gis-spinner gis-spinner-lg" />
          <p class="font-display tracking-wide">引擎正在调用 GIS 工具…</p>
          <p class="text-xs text-muted">每个工具调用都会被记录并展示在下方轨迹中</p>
        </div>

        <!-- 空状态 -->
        <div v-else-if="!result" class="gis-card gis-empty animate-enter">
          <div class="gis-empty-compass">⌖</div>
          <p class="font-display text-base font-semibold">等待分析指令</p>
          <p class="text-sm text-muted mt-2 leading-relaxed max-w-md">
            输入需求后点击「开始分析」。引擎将自动编排工具调用，生成地图与统计产物。
          </p>
          <div class="mt-5 w-full max-w-md">
            <div class="h-px bg-gradient-to-r from-transparent via-[var(--border)] to-transparent" />
            <p class="text-[11px] tracking-[0.2em] text-muted mt-3">示例</p>
            <p class="text-xs text-dim/80 mt-1.5 leading-relaxed">
              “把 gdp_demo.csv 按省份做分级设色图，并导出分级统计 summary.csv”
            </p>
          </div>
        </div>

        <!-- 结果 -->
        <template v-else>
          <!-- 结论 -->
          <div v-if="result.final" class="gis-card animate-enter relative overflow-hidden">
            <div class="flex items-start gap-4">
              <div class="gis-seal gis-seal-sm shrink-0">结</div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-3 mb-3">
                  <div class="accent-line" />
                  <h3 class="heading-section">结论</h3>
                </div>
                <p class="text-sm text-[var(--text)]/90 leading-relaxed whitespace-pre-wrap">{{ result.final }}</p>
              </div>
            </div>
          </div>

          <!-- 工具调用轨迹 -->
          <div class="gis-card animate-enter stagger-1">
            <div class="flex items-center gap-3 mb-5">
              <div class="accent-line" />
              <h3 class="heading-section">工具调用轨迹</h3>
              <span class="gis-chip gis-chip-accent ml-auto shrink-0">{{ result.steps }} 步</span>
            </div>

            <ol class="gis-timeline">
              <li
                v-for="t in result.trajectory"
                :key="`${t.step}-${t.tool}`"
                class="gis-timeline-item"
                :class="`stagger-${Math.min(t.step, 5)}`"
              >
                <span class="gis-timeline-node" :class="`gis-node-${stepStatus(t)}`" />
                <div class="gis-timeline-card">
                  <div class="flex items-center gap-2.5 min-w-0">
                    <span class="gis-step-index shrink-0">#{{ t.step }}</span>
                    <code class="gis-tool-name shrink-0">{{ t.tool }}</code>
                    <span class="gis-tool-args min-w-0">{{ toolArgsText(t) }}</span>
                    <span class="ml-auto shrink-0" :class="stepStatus(t) === 'ok' ? 'text-[var(--success)]' : stepStatus(t) === 'err' ? 'text-[var(--danger)]' : 'text-muted'">
                      {{ toolStatusText(t) }}
                    </span>
                  </div>
                </div>
              </li>
            </ol>
          </div>

          <!-- 产物 -->
          <div class="gis-card animate-enter stagger-2">
            <div class="flex items-center gap-3 mb-5">
              <div class="accent-line" />
              <h3 class="heading-section">产物</h3>
              <span class="gis-chip gis-chip-accent ml-auto shrink-0">{{ result.outputs.length }} 个</span>
            </div>

            <!-- PNG 画廊 -->
            <div v-if="pngArtifacts.length" class="grid gap-4 md:grid-cols-2">
              <figure v-for="p in pngArtifacts" :key="p.name" class="gis-artifact animate-enter">
                <img :src="p.url" :alt="p.name" class="w-full block" />
                <figcaption class="flex items-center justify-between gap-2">
                  <span class="truncate text-xs text-dim font-mono">{{ p.name }}</span>
                  <a class="gis-download-link shrink-0" @click="download(p.url, p.name)">下载</a>
                </figcaption>
              </figure>
            </div>

            <!-- 其他文件 -->
            <div v-if="fileArtifacts.length" class="space-y-2">
              <div v-for="f in fileArtifacts" :key="f.name" class="gis-file-row animate-enter">
                <span class="gis-file-ext shrink-0">{{ f.ext }}</span>
                <span class="text-sm truncate">{{ f.name }}</span>
                <a class="gis-download-link ml-auto shrink-0" @click="download(f.url, f.name)">下载</a>
              </div>
            </div>

            <p v-if="!pngArtifacts.length && !fileArtifacts.length" class="text-sm text-muted py-4 text-center">
              本次任务没有声明产物。
            </p>
          </div>
        </template>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* ---- 页面骨架 ---- */
.gis-page {
  position: relative;
  height: 100vh;
  height: 100dvh;
  overflow-y: auto;
  overflow-x: hidden;
  background-color: var(--bg);
  color: var(--text);
}

/* ---- 氛围背景：制图网格 + 顶部光晕 ---- */
.gis-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.gis-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(var(--border) 1px, transparent 1px),
    linear-gradient(90deg, var(--border) 1px, transparent 1px);
  background-size: 48px 48px;
  opacity: 0.18;
  -webkit-mask-image: radial-gradient(ellipse 100% 72% at 50% 0%, black 25%, transparent 78%);
  mask-image: radial-gradient(ellipse 100% 72% at 50% 0%, black 25%, transparent 78%);
}
.gis-bg-glow {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 70% 40% at 50% -5%, var(--accent-glow) 0%, transparent 65%),
    radial-gradient(ellipse 40% 30% at 100% 100%, rgba(212, 168, 83, 0.05) 0%, transparent 70%);
}

/* ---- 头部 ---- */
.gis-header {
  position: sticky;
  top: 0;
  z-index: 20;
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg) 82%, transparent);
  backdrop-filter: blur(10px);
}
.gis-seal {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 5px;
  background: linear-gradient(145deg, #d0484e, var(--seal-red));
  color: #faf3ea;
  font-family: var(--font-display);
  font-weight: 900;
  font-size: 1.3rem;
  box-shadow:
    inset 0 0 0 2px rgba(250, 243, 234, 0.28),
    0 4px 14px rgba(196, 52, 58, 0.35);
  transform: rotate(-2deg);
  user-select: none;
}
.gis-seal-sm {
  width: 34px;
  height: 34px;
  font-size: 1.05rem;
  border-radius: 4px;
}
.gis-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.08em;
  color: var(--accent);
  background: var(--accent-dim);
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
}
.gis-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.08em;
  color: var(--success);
  background: var(--success-dim);
  border: 1px solid color-mix(in srgb, var(--success) 30%, transparent);
}
.gis-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
  animation: gisPulse 2.2s ease-in-out infinite;
}
@keyframes gisPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.45; transform: scale(0.82); }
}

/* ---- 卡片 ---- */
.gis-card {
  position: relative;
  z-index: 1;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg-card) 92%, transparent);
  backdrop-filter: blur(6px);
  padding: 1.25rem 1.375rem;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease;
}
.gis-card:hover {
  border-color: var(--border-light);
  box-shadow: var(--shadow-md);
}
.gis-step-no {
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--accent-dim);
  color: var(--accent);
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 12px;
}

/* ---- 上传区 ---- */
.gis-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 26px 18px;
  border: 1.5px dashed var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: center;
  transition: border-color 0.25s ease, background 0.25s ease, box-shadow 0.25s ease;
}
.gis-upload:hover {
  border-color: var(--accent);
  background: var(--bg-hover);
  box-shadow: var(--accent-glow);
}
.gis-upload-done {
  border-style: solid;
  border-color: color-mix(in srgb, var(--success) 45%, var(--border));
  background: var(--success-dim);
}
.gis-upload-done:hover {
  border-color: var(--success);
  box-shadow: 0 0 18px rgba(91, 154, 124, 0.18);
}
.gis-upload-icon {
  font-size: 26px;
  filter: grayscale(0.2);
  transition: transform 0.25s ease;
}
.gis-upload:hover .gis-upload-icon {
  transform: translateY(-3px) scale(1.08);
}
.gis-file-icon {
  font-size: 20px;
}
.gis-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.gis-chip-accent {
  color: var(--accent);
  background: var(--accent-dim);
}
.gis-chip-ok {
  color: var(--success);
  background: color-mix(in srgb, var(--success) 14%, transparent);
}

/* ---- 工具分组 ---- */
.gis-group-label {
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 7px;
}
.gis-tool-pill {
  padding: 4px 10px;
  border-radius: 7px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-dim);
  background: var(--bg-input);
  border: 1px solid var(--border);
  transition: all 0.2s ease;
}
.gis-tool-pill:hover {
  color: var(--accent);
  border-color: color-mix(in srgb, var(--accent) 45%, transparent);
  background: var(--accent-dim);
  transform: translateY(-1px);
}

/* ---- 执行按钮 ---- */
.gis-run-btn {
  position: relative;
  z-index: 1;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 13px 0;
  border: none;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--accent-hover), var(--accent) 60%);
  color: var(--text-on-accent);
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: 0.08em;
  box-shadow: var(--accent-glow);
  cursor: pointer;
  transition: filter 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
}
.gis-run-btn:hover:not(:disabled) {
  filter: brightness(1.07);
  transform: translateY(-1px);
  box-shadow: 0 6px 26px rgba(212, 168, 83, 0.32);
}
.gis-run-btn:active:not(:disabled) {
  transform: scale(0.98);
}
.gis-run-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ---- 错误提示 ---- */
.gis-error {
  position: relative;
  z-index: 1;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: var(--danger-dim);
  border: 1px solid color-mix(in srgb, var(--danger) 35%, transparent);
  color: var(--danger);
  font-size: 12px;
  line-height: 1.6;
}

/* ---- 空状态 ---- */
.gis-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 64px 24px;
}
.gis-empty-compass {
  width: 64px;
  height: 64px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-size: 26px;
  color: var(--accent);
  background: var(--accent-dim);
  border: 1px dashed color-mix(in srgb, var(--accent) 45%, transparent);
  box-shadow: var(--accent-glow);
  margin-bottom: 18px;
}

/* ---- 轨迹时间线 ---- */
.gis-timeline {
  position: relative;
  margin: 0;
  padding: 0;
  list-style: none;
}
.gis-timeline::before {
  content: "";
  position: absolute;
  left: 7px;
  top: 10px;
  bottom: 10px;
  width: 2px;
  border-radius: 1px;
  background: linear-gradient(to bottom, var(--accent) 0%, var(--border) 90%);
}
.gis-timeline-item {
  position: relative;
  padding-left: 30px;
  padding-bottom: 14px;
}
.gis-timeline-item:last-child {
  padding-bottom: 2px;
}
.gis-timeline-node {
  position: absolute;
  left: 0;
  top: 16px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  border: 3px solid var(--bg-card);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 45%, transparent);
}
.gis-node-ok {
  background: var(--success);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--success) 45%, transparent);
}
.gis-node-err {
  background: var(--danger);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--danger) 45%, transparent);
}
.gis-node-other {
  background: var(--text-muted);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--text-muted) 45%, transparent);
}
.gis-timeline-card {
  display: flex;
  align-items: center;
  padding: 9px 12px;
  border-radius: var(--radius-md);
  background: var(--bg-input);
  border: 1px solid var(--border);
  transition: border-color 0.2s ease, background 0.2s ease;
}
.gis-timeline-item:hover .gis-timeline-card {
  border-color: color-mix(in srgb, var(--accent) 40%, transparent);
  background: var(--bg-hover);
}
.gis-step-index {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}
.gis-tool-name {
  font-family: var(--font-mono);
  font-size: 12.5px;
  font-weight: 600;
  color: var(--accent);
}
.gis-tool-args {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ---- 产物 ---- */
.gis-artifact {
  margin: 0;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  overflow: hidden;
  background: var(--bg-input);
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}
.gis-artifact:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: color-mix(in srgb, var(--accent) 40%, transparent);
}
.gis-artifact img {
  aspect-ratio: 4 / 3;
  object-fit: cover;
  background:
    linear-gradient(45deg, var(--bg-input) 25%, transparent 25%, transparent 75%, var(--bg-input) 75%),
    linear-gradient(45deg, var(--bg-input) 25%, var(--bg-card) 25%, var(--bg-card) 75%, var(--bg-input) 75%);
  background-size: 20px 20px;
  background-position: 0 0, 10px 10px;
}
.gis-artifact figcaption {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid var(--border);
}
.gis-download-link {
  color: var(--accent);
  font-size: 12px;
  cursor: pointer;
  transition: opacity 0.2s ease;
}
.gis-download-link:hover {
  opacity: 0.75;
  text-decoration: underline;
}
.gis-file-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: var(--radius-md);
  background: var(--bg-input);
  border: 1px solid var(--border);
  transition: border-color 0.2s ease;
}
.gis-file-row:hover {
  border-color: color-mix(in srgb, var(--accent) 40%, transparent);
}
.gis-file-ext {
  padding: 1px 7px;
  border-radius: 5px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--accent);
  background: var(--accent-dim);
}

/* ---- 加载 ---- */
.gis-spinner {
  width: 15px;
  height: 15px;
  border-radius: 50%;
  border: 2px solid color-mix(in srgb, var(--text-on-accent) 35%, transparent);
  border-top-color: var(--text-on-accent);
  animation: gisSpin 0.8s linear infinite;
}
.gis-spinner-lg {
  width: 26px;
  height: 26px;
  border-width: 3px;
  border-color: var(--border-light);
  border-top-color: var(--accent);
}
@keyframes gisSpin {
  to { transform: rotate(360deg); }
}
</style>
