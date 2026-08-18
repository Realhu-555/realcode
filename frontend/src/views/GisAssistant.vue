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
  <div class="min-h-screen bg-[var(--bg)] text-[var(--text)]">
    <!-- 顶部 -->
    <header class="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--bg)]/80 backdrop-blur">
      <div class="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
        <div>
          <h1 class="text-lg font-bold tracking-wide">GIS 智能助手</h1>
          <p class="text-xs text-[var(--text-dim)] mt-0.5">自然语言驱动 GIS 引擎 · 工具调用全轨迹可审计</p>
        </div>
        <div class="flex items-center gap-2 text-xs text-[var(--text-dim)]">
          <span class="inline-block w-2 h-2 rounded-full bg-[var(--success)]" />
          DeepSeek 引擎在线
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-6 py-6 grid gap-6 lg:grid-cols-[380px_1fr]">
      <!-- 左：输入区 -->
      <section class="space-y-4">
        <div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--bg-card)] p-5 space-y-4">
          <div>
            <div class="text-sm font-semibold mb-2">① 数据文件</div>
            <label
              class="flex items-center justify-center gap-2 rounded-[var(--radius-md)] border border-dashed border-[var(--border-light)] bg-[var(--bg-input)] px-4 py-6 text-sm text-[var(--text-dim)] cursor-pointer hover:border-[var(--accent)] hover:text-[var(--accent)] transition-colors"
            >
              <input type="file" accept=".csv,.geojson,.json,.zip" class="hidden" :disabled="running" @change="onFileSelected" />
              <span>{{ uploading ? "上传中…" : fileName || "点击选择 CSV / GeoJSON / ZIP（可选）" }}</span>
            </label>
          </div>

          <div>
            <div class="text-sm font-semibold mb-2">② 你的需求</div>
            <n-input
              v-model:value="request"
              type="textarea"
              :rows="5"
              placeholder="例如：找出 gdp_demo.csv 中 gdp 最高的省份并画散点图"
              :disabled="running"
            />
          </div>

          <n-button
            type="primary"
            size="large"
            block
            :loading="running"
            :disabled="!canSubmit"
            color="#D4A853"
            text-color="#0D0B09"
            @click="onSubmit"
          >
            {{ running ? "GIS 引擎执行中…" : "开始分析" }}
          </n-button>

          <p v-if="error" class="text-xs text-[var(--danger)] bg-[var(--danger-dim)] rounded-md px-3 py-2">
            {{ error }}
          </p>
        </div>

        <div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--bg-card)] p-5 text-xs text-[var(--text-dim)] space-y-1.5">
          <div class="text-sm font-semibold text-[var(--text)] mb-1">可用工具（9 个）</div>
          <div>load_data · inspect_data · buffer · overlay</div>
          <div>choropleth · scatter_plot · summarize</div>
          <div>export_geojson · finish</div>
        </div>
      </section>

      <!-- 右：结果区 -->
      <section class="space-y-4">
        <!-- 运行中 -->
        <div v-if="running" class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--bg-card)] p-10 flex flex-col items-center gap-3 text-sm text-[var(--text-dim)]">
          <span class="inline-block w-6 h-6 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin" />
          引擎正在调用 GIS 工具…
        </div>

        <!-- 空状态 -->
        <div v-else-if="!result" class="rounded-[var(--radius-lg)] border border-dashed border-[var(--border-light)] bg-[var(--bg-card)] p-10 text-center text-sm text-[var(--text-muted)]">
          输入需求后点击「开始分析」，这里会展示工具调用轨迹与产物。
        </div>

        <!-- 结果 -->
        <template v-else>
          <div v-if="result.final" class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--bg-card)] p-5">
            <div class="text-sm font-semibold mb-2">结论</div>
            <p class="text-sm text-[var(--text)]/90 leading-relaxed whitespace-pre-wrap">{{ result.final }}</p>
          </div>

          <div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--bg-card)] p-5">
            <div class="text-sm font-semibold mb-3">工具调用轨迹（{{ result.steps }} 步）</div>
            <ol class="space-y-2">
              <li v-for="t in result.trajectory" :key="`${t.step}-${t.tool}`" class="flex items-start gap-3 rounded-md px-3 py-2 bg-[var(--bg-input)]">
                <span class="mt-0.5 shrink-0 text-xs text-[var(--text-muted)]">#{{ t.step }}</span>
                <code class="shrink-0 text-xs text-[var(--accent)] font-mono">{{ t.tool }}</code>
                <span class="shrink-0 text-xs text-[var(--text-muted)] font-mono truncate max-w-[180px]">{{ toolArgsText(t.args) }}</span>
                <span
                  class="ml-auto shrink-0 text-xs"
                  :class="t.result.status === 'error' ? 'text-[var(--danger)]' : 'text-[var(--success)]'"
                >
                  {{ toolStatusText(t) }}
                </span>
              </li>
            </ol>
          </div>

          <div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--bg-card)] p-5">
            <div class="text-sm font-semibold mb-3">产物（{{ result.outputs.length }}）</div>
            <div v-if="pngArtifacts.length" class="grid gap-4 md:grid-cols-2">
              <figure v-for="p in pngArtifacts" :key="p.name" class="space-y-1.5">
                <img :src="p.url" :alt="p.name" class="w-full rounded-md border border-[var(--border)] bg-black/30" />
                <figcaption class="text-xs text-[var(--text-dim)] flex items-center justify-between">
                  <span>{{ p.name }}</span>
                  <a class="text-[var(--accent)] hover:underline cursor-pointer" @click="download(p.url, p.name)">下载</a>
                </figcaption>
              </figure>
            </div>
            <div v-if="fileArtifacts.length" class="space-y-2 mt-2">
              <div v-for="f in fileArtifacts" :key="f.name" class="flex items-center gap-3 rounded-md px-3 py-2 bg-[var(--bg-input)]">
                <span class="shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-[var(--accent-dim)] text-[var(--accent)]">{{ f.ext }}</span>
                <span class="text-sm text-[var(--text)]">{{ f.name }}</span>
                <a class="ml-auto text-xs text-[var(--accent)] hover:underline cursor-pointer" @click="download(f.url, f.name)">下载</a>
              </div>
            </div>
            <p v-if="!pngArtifacts.length && !fileArtifacts.length" class="text-sm text-[var(--text-muted)]">本次任务没有声明产物。</p>
          </div>
        </template>
      </section>
    </main>
  </div>
</template>
