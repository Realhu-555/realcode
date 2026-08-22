<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue"
import { useMessage } from "naive-ui"
import { useTheme } from "../composables/useTheme"
import {
  uploadGisFile,
  streamGisAssistant,
  objectUrlFor,
  listGisSessions,
  getGisSessionDetail,
  deleteGisSession,
  type GisStreamEvent,
  type GisSessionSummary,
  type GisSessionDetail,
} from "../api/gis"

useTheme()

const message = useMessage()

const request = ref("")
const dataFile = ref("")
const fileName = ref("")
const uploading = ref(false)
const running = ref(false)
const error = ref("")
const sessionId = ref("")
const chatEl = ref<HTMLElement | null>(null)
const sessions = ref<GisSessionSummary[]>([])
const sidebarOpen = ref(true)

type ToolStatus = "running" | "ok" | "error" | "other"

type StreamItem =
  | { kind: "text"; content: string }
  | {
      kind: "tool"
      step: number
      tool: string
      args: Record<string, unknown>
      result?: Record<string, unknown>
      status: ToolStatus
    }
  | { kind: "artifact"; name: string; url: string; ext?: string }

interface ChatMessage {
  role: "user" | "assistant"
  content: string
  items: StreamItem[]
  error?: string
}
const messages = ref<ChatMessage[]>([])

const canSubmit = computed(() => request.value.trim().length > 0 && !running.value)

// 流式期间是否有正在执行的工具（有则不显示全局 spinner）
const hasActiveTool = computed(() =>
  messages.value.some((m) => m.items.some((it) => it.kind === "tool" && it.status === "running")),
)

// 消息更新后自动滚动到底部
watch([messages, running], async () => {
  await nextTick()
  if (chatEl.value) chatEl.value.scrollTop = chatEl.value.scrollHeight
})

onMounted(loadSessions)

function formatTime(ts: number): string {
  if (!ts) return ""
  const ms = ts * 1000
  const diff = Date.now() - ms
  if (diff < 60_000) return "刚刚"
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  const d = new Date(ms)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

async function loadSessions() {
  try {
    sessions.value = await listGisSessions()
  } catch {
    sessions.value = []
  }
}

async function selectSession(s: GisSessionSummary) {
  if (running.value) return
  if (s.session_id === sessionId.value && messages.value.length) return
  try {
    const detail = await getGisSessionDetail(s.session_id)
    await restoreMessages(detail)
  } catch {
    message.error("恢复会话失败")
  }
}

async function restoreMessages(detail: GisSessionDetail) {
  sessionId.value = detail.session_id
  messages.value = []
  for (const r of detail.rounds) {
    messages.value.push({ role: "user", content: r.user, items: [] })
    const items: StreamItem[] = [{ kind: "text", content: r.final }]
    for (const t of r.trajectory) {
      items.push({
        kind: "tool",
        step: t.step,
        tool: t.tool,
        args: t.args,
        result: t.result,
        status: t.result.status === "ok" ? "ok" : t.result.status === "error" ? "error" : "other",
      })
    }
    for (const name of r.outputs) {
      try {
        const url = await objectUrlFor(name, detail.session_id)
        items.push({
          kind: "artifact",
          name,
          url,
          ext: name.toLowerCase().endsWith(".png")
            ? undefined
            : name.split(".").pop()?.toUpperCase() || "FILE",
        })
      } catch {
        // 产物文件可能已被清理，跳过
      }
    }
    messages.value.push({ role: "assistant", content: r.final, items })
  }
  // 恢复完成后定位到最新一条对话（DOM 更新后再滚动）
  await nextTick()
  if (chatEl.value) chatEl.value.scrollTop = chatEl.value.scrollHeight
}

async function removeSession(s: GisSessionSummary, e: Event) {
  e.stopPropagation()
  if (running.value) return
  try {
    await deleteGisSession(s.session_id)
    if (sessionId.value === s.session_id) newConversation()
    await loadSessions()
    message.success("会话已删除")
  } catch {
    message.error("删除失败")
  }
}

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

function clearFile() {
  dataFile.value = ""
  fileName.value = ""
}

function toolArgsText(args: Record<string, unknown>): string {
  try {
    return JSON.stringify(args)
  } catch {
    return ""
  }
}

function toolItemText(item: Extract<StreamItem, { kind: "tool" }>): string {
  if (item.status === "running") return "执行中"
  if (item.status === "ok") return "成功"
  if (item.status === "error") return String(item.result?.error ?? "失败")
  return "完成"
}

async function onSubmit() {
  if (!canSubmit.value) return
  running.value = true
  error.value = ""
  const ask = request.value.trim()
  messages.value.push({ role: "user", content: ask, items: [] })
  request.value = ""
  const msg: ChatMessage = { role: "assistant", content: "", items: [] }
  messages.value.push(msg)
  try {
    await streamGisAssistant(
      ask,
      dataFile.value || undefined,
      sessionId.value || undefined,
      (ev) => handleStreamEvent(msg, ev),
    )
    message.success("完成")
  } catch (err) {
    msg.error = err instanceof Error ? err.message : String(err)
  } finally {
    running.value = false
    await loadSessions()
  }
}

async function handleStreamEvent(msg: ChatMessage, ev: GisStreamEvent) {
  switch (ev.type) {
    case "session_start":
      sessionId.value = ev.session_id
      break
    case "text_delta": {
      msg.content += ev.delta
      const last = msg.items[msg.items.length - 1]
      if (last && last.kind === "text") {
        last.content += ev.delta
      } else {
        msg.items.push({ kind: "text", content: ev.delta })
      }
      // 用宏任务让出渲染帧（nextTick 是微任务，浏览器无法在微任务间插帧渲染）
      await new Promise<void>((resolve) => setTimeout(resolve, 0))
      break
    }
    case "tool_call":
      msg.items.push({ kind: "tool", step: ev.step, tool: ev.tool, args: ev.args, status: "running" })
      break
    case "tool_result": {
      const item = msg.items.find(
        (x): x is Extract<StreamItem, { kind: "tool" }> =>
          x.kind === "tool" && x.step === ev.step && x.tool === ev.tool && x.status === "running",
      )
      if (item) {
        item.result = ev.result
        item.status = ev.result.status === "ok" ? "ok" : ev.result.status === "error" ? "error" : "other"
      }
      break
    }
    case "done":
      for (const name of ev.outputs) {
        void (async () => {
          try {
            const url = await objectUrlFor(name, sessionId.value)
            msg.items.push({
              kind: "artifact",
              name,
              url,
              ext: name.toLowerCase().endsWith(".png")
                ? undefined
                : name.split(".").pop()?.toUpperCase() || "FILE",
            })
          } catch {
            // 产物获取失败忽略
          }
        })()
      }
      break
    case "error":
      msg.error = ev.error
      break
  }
}

function newConversation() {
  sessionId.value = ""
  messages.value = []
  error.value = ""
  dataFile.value = ""
  fileName.value = ""
  message.info("已开启新对话")
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

    <!-- ===== 左侧：会话管理 ===== -->
    <aside class="gis-sidebar" :class="{ 'gis-sidebar-closed': !sidebarOpen }">
      <div class="gis-sidebar-head">
        <span class="text-[11px] tracking-[0.2em] text-muted font-semibold">会话</span>
        <button class="gis-sidebar-new" :disabled="running" @click="newConversation" title="新会话">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14" /></svg>
        </button>
      </div>

      <div class="gis-sidebar-list">
        <button
          v-for="s in sessions"
          :key="s.session_id"
          class="gis-session-item"
          :class="{ 'gis-session-active': s.session_id === sessionId }"
          :disabled="running"
          @click="selectSession(s)"
        >
          <div class="min-w-0 flex-1 text-left">
            <p class="gis-session-title">{{ s.title }}</p>
            <p class="gis-session-meta">{{ s.rounds }} 轮 · {{ formatTime(s.updated_at) }}</p>
          </div>
          <span
            class="gis-session-del"
            :title="'删除 ' + s.title"
            @click="removeSession(s, $event)"
          >
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /></svg>
          </span>
        </button>

        <p v-if="!sessions.length" class="gis-sidebar-empty">暂无历史会话</p>
      </div>
    </aside>

    <!-- ===== 主区域 ===== -->
    <div class="gis-main">
      <!-- 顶部 -->
      <header class="gis-header">
        <div class="mx-auto max-w-3xl px-6 py-4 flex items-center justify-between gap-4">
          <div class="flex items-center gap-3.5 min-w-0">
            <button class="gis-sidebar-toggle" @click="sidebarOpen = !sidebarOpen" title="切换会话栏">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 12h18M3 6h18M3 18h18" /></svg>
            </button>
            <div class="gis-seal shrink-0">制</div>
            <div class="min-w-0">
              <h1 class="font-display text-lg font-black tracking-tight">GIS 智能助手</h1>
              <p class="text-[11px] text-dim mt-0.5 tracking-wide truncate">多轮对话 · 工具调用全轨迹可审计</p>
            </div>
          </div>
          <div class="flex items-center gap-2.5 shrink-0">
            <button class="gis-new-btn" :disabled="running" @click="newConversation">↺ 新对话</button>
            <span class="gis-status">
              <span class="gis-status-dot" />
              <span class="hidden sm:inline">引擎在线</span>
            </span>
          </div>
        </div>
      </header>

      <!-- 主对话区 -->
      <main ref="chatEl" class="gis-chat">
        <div class="mx-auto max-w-3xl px-6 py-8 space-y-6">
          <!-- 空状态 -->
          <div v-if="!messages.length" class="gis-empty animate-enter">
            <div class="gis-empty-compass">⌖</div>
            <p class="font-display text-lg font-semibold">开始你的 GIS 对话</p>
            <p class="text-sm text-muted mt-2 leading-relaxed max-w-md">
              像和桌面助手聊天一样描述需求：支持多轮连续对话，引擎会记住当前图层与产物，
              随时可以继续追问或修改。
            </p>
            <div class="mt-6 w-full max-w-md text-left space-y-2">
              <p class="text-[11px] tracking-[0.2em] text-muted">示例</p>
              <button
                v-for="ex in ['把 gdp_demo.csv 按省份做分级设色图，并导出分级统计 summary.csv', '对 gdp_demo.csv 做 0.5 度缓冲区后导出 GeoJSON']"
                :key="ex"
                class="gis-example-chip"
                @click="request = ex"
              >
                {{ ex }}
              </button>
            </div>
          </div>

          <!-- 消息流 -->
          <template v-for="(m, i) in messages" :key="i">
            <!-- 用户消息 -->
            <div v-if="m.role === 'user'" class="gis-msg-row gis-msg-user animate-enter">
              <div class="gis-user-text">{{ m.content }}</div>
            </div>

            <!-- 助手回复（按输出顺序流式排版） -->
            <div v-else class="gis-msg-row gis-msg-assistant animate-enter">
              <div v-if="m.error" class="gis-error w-full">{{ m.error }}</div>

              <div v-else class="space-y-3 w-full">
                <template v-for="(item, k) in m.items" :key="k">
                  <!-- 文本块 -->
                  <div v-if="item.kind === 'text' && item.content" class="gis-answer">
                    <p class="whitespace-pre-wrap leading-relaxed text-[14.5px]">{{ item.content }}</p>
                  </div>

                  <!-- 工具调用（内联时间线） -->
                  <div v-else-if="item.kind === 'tool'" class="gis-timeline-item gis-tool-inline animate-enter">
                    <span class="gis-timeline-node" :class="`gis-node-${item.status === 'running' ? 'other' : item.status}`" />
                    <div class="gis-timeline-card">
                      <div class="flex items-center gap-2.5 min-w-0">
                        <span class="gis-step-index shrink-0">#{{ item.step }}</span>
                        <code class="gis-tool-name shrink-0">{{ item.tool }}</code>
                        <span class="gis-tool-args min-w-0">{{ toolArgsText(item.args) }}</span>
                        <span
                          v-if="item.status === 'running'"
                          class="ml-auto shrink-0 flex items-center gap-1.5 text-muted"
                        >
                          <span class="gis-spinner" />
                          <span class="text-[11px]">执行中</span>
                        </span>
                        <span
                          v-else
                          class="ml-auto shrink-0"
                          :class="item.status === 'ok' ? 'text-[var(--success)]' : item.status === 'error' ? 'text-[var(--danger)]' : 'text-muted'"
                        >
                          {{ toolItemText(item) }}
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- 图片产物 -->
                  <figure v-else-if="item.kind === 'artifact' && !item.ext" class="gis-artifact">
                    <img :src="item.url" :alt="item.name" class="w-full block" />
                    <figcaption class="flex items-center justify-between gap-2">
                      <span class="truncate text-xs text-dim font-mono">{{ item.name }}</span>
                      <a class="gis-download-link shrink-0" @click="download(item.url!, item.name!)">下载</a>
                    </figcaption>
                  </figure>

                  <!-- 文件产物 -->
                  <div v-else-if="item.kind === 'artifact'" class="gis-file-row">
                    <span class="gis-file-ext shrink-0">{{ item.ext }}</span>
                    <span class="text-sm truncate">{{ item.name }}</span>
                    <a class="gis-download-link ml-auto shrink-0" @click="download(item.url!, item.name!)">下载</a>
                  </div>
                </template>
              </div>
            </div>
          </template>

          <!-- 执行中 -->
          <div v-if="running && !hasActiveTool" class="gis-thinking animate-enter">
            <span class="gis-spinner gis-spinner-lg" />
            <span class="text-sm text-dim">正在生成…</span>
          </div>
        </div>
      </main>

      <!-- 底部输入区 -->
      <footer class="gis-composer">
        <div class="mx-auto max-w-3xl px-6 py-4">
          <div v-if="fileName" class="mb-2 flex items-center gap-2">
            <span class="gis-file-chip">
              📄 {{ fileName }}
              <button class="gis-file-chip-x" :disabled="running" @click="clearFile">×</button>
            </span>
            <span class="text-[11px] text-muted">该文件将用于本会话</span>
          </div>

          <div class="gis-input-row">
            <label class="gis-attach-btn" title="上传数据文件（CSV / GeoJSON / ZIP）">
              <input type="file" accept=".csv,.geojson,.json,.zip" class="hidden" :disabled="running" @change="onFileSelected" />
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" /></svg>
            </label>
            <n-input
              v-model:value="request"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 6 }"
              placeholder="输入你的 GIS 需求…（Enter 发送，Shift+Enter 换行）"
              :disabled="running"
              @keydown.enter.exact.prevent="onSubmit"
            />
            <button class="gis-send-btn" :disabled="!canSubmit" title="发送" @click="onSubmit">
              <span v-if="!running">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
              </span>
              <span v-else class="gis-spinner" />
            </button>
          </div>

          <div class="mt-2 flex items-center justify-between text-[11px] text-muted">
            <span>📎 可上传数据 · 未上传时自动使用演示数据</span>
            <span class="hidden sm:inline">{{ sessionId ? "多轮对话中 · 图层与产物已保留" : "新会话" }}</span>
          </div>
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
/* ---- 页面骨架：sidebar + main ---- */
.gis-page {
  position: relative;
  height: 100vh;
  height: 100dvh;
  display: flex;
  overflow: hidden;
  background-color: var(--bg);
  color: var(--text);
}
.gis-main {
  position: relative;
  z-index: 1;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

/* ---- 氛围背景 ---- */
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

/* ---- 左侧会话栏 ---- */
.gis-sidebar {
  position: relative;
  z-index: 10;
  width: 248px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg-sidebar) 88%, transparent);
  backdrop-filter: blur(10px);
  transition: margin-left 0.25s ease;
}
.gis-sidebar-closed {
  margin-left: -248px;
}
.gis-sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 14px 10px;
}
.gis-sidebar-new {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  transition: all 0.2s ease;
}
.gis-sidebar-new:hover:not(:disabled) {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--bg-hover);
}
.gis-sidebar-new:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.gis-sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.gis-session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 9px 10px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  transition: all 0.18s ease;
}
.gis-session-item:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text);
}
.gis-session-active {
  background: var(--accent-dim);
  border-color: color-mix(in srgb, var(--accent) 30%, transparent);
  color: var(--text);
}
.gis-session-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.gis-session-title {
  font-size: 12.5px;
  font-weight: 500;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gis-session-meta {
  font-size: 10.5px;
  color: var(--text-muted);
  margin-top: 2px;
}
.gis-session-del {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  color: var(--text-muted);
  opacity: 0;
  flex-shrink: 0;
  transition: all 0.18s ease;
}
.gis-session-item:hover .gis-session-del {
  opacity: 1;
}
.gis-session-del:hover {
  color: var(--danger);
  background: var(--danger-dim);
}
.gis-sidebar-empty {
  padding: 18px 10px;
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
}
.gis-sidebar-toggle {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.gis-sidebar-toggle:hover {
  color: var(--accent);
  background: var(--bg-hover);
}

/* ---- 头部 ---- */
.gis-header {
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg) 82%, transparent);
  backdrop-filter: blur(10px);
}
.gis-seal {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 5px;
  background: linear-gradient(145deg, #d0484e, var(--seal-red));
  color: #faf3ea;
  font-family: var(--font-display);
  font-weight: 900;
  font-size: 1.15rem;
  box-shadow:
    inset 0 0 0 2px rgba(250, 243, 234, 0.28),
    0 4px 14px rgba(196, 52, 58, 0.35);
  transform: rotate(-2deg);
  user-select: none;
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
.gis-new-btn {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.06em;
  color: var(--text-dim);
  background: transparent;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.2s ease;
}
.gis-new-btn:hover:not(:disabled) {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--bg-hover);
}
.gis-new-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ---- 主对话区 ---- */
.gis-chat {
  flex: 1;
  overflow-y: auto;
  overscroll-behavior: contain;
}
.gis-chat::-webkit-scrollbar {
  width: 6px;
}

/* ---- 消息行 ---- */
.gis-msg-row {
  display: flex;
}
.gis-msg-user {
  justify-content: flex-end;
}
.gis-msg-assistant {
  justify-content: flex-start;
  width: 100%;
}
.gis-user-text {
  max-width: 82%;
  padding: 9px 14px;
  border-radius: 14px 14px 4px 14px;
  background: var(--accent-dim);
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  color: var(--text);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
.gis-answer {
  padding: 2px 2px 0;
}
.gis-thinking {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 2px;
}

/* ---- 轨迹折叠 ---- */
.gis-trajectory-wrap {
  margin-top: 14px;
}
.gis-trajectory-toggle {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg-input);
  color: var(--text-dim);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}
.gis-trajectory-toggle:hover {
  color: var(--accent);
  border-color: color-mix(in srgb, var(--accent) 40%, transparent);
  background: var(--bg-hover);
}
.gis-chevron {
  transition: transform 0.2s ease;
}
.gis-chevron-open {
  transform: rotate(90deg);
}
.gis-trajectory-body {
  margin-top: 10px;
  padding-left: 2px;
}

/* ---- 时间线 ---- */
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
  padding-bottom: 12px;
}
.gis-timeline-item:last-child {
  padding-bottom: 2px;
}

/* ---- 流式工具调用（内联时间线） ---- */
.gis-tool-inline::before {
  content: "";
  position: absolute;
  left: 7px;
  top: 32px;
  bottom: -10px;
  width: 2px;
  border-radius: 1px;
  background: linear-gradient(to bottom, var(--accent) 0%, var(--border) 90%);
}
.gis-tool-inline:last-child::before {
  display: none;
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
  padding: 8px 12px;
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
.gis-chip {
  display: inline-flex;
  align-items: center;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.gis-chip-accent {
  color: var(--accent);
  background: var(--accent-dim);
}

/* ---- 空状态 ---- */
.gis-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 56px 24px;
}
.gis-empty-compass {
  width: 60px;
  height: 60px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-size: 24px;
  color: var(--accent);
  background: var(--accent-dim);
  border: 1px dashed color-mix(in srgb, var(--accent) 45%, transparent);
  box-shadow: var(--accent-glow);
  margin-bottom: 16px;
}
.gis-example-chip {
  display: block;
  width: 100%;
  text-align: left;
  padding: 9px 14px;
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-light);
  background: transparent;
  color: var(--text-dim);
  font-size: 12.5px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.gis-example-chip:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--bg-hover);
}

/* ---- 底部输入区 ---- */
.gis-composer {
  border-top: 1px solid var(--border);
  background: color-mix(in srgb, var(--bg) 86%, transparent);
  backdrop-filter: blur(12px);
}
.gis-file-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  color: var(--success);
  background: var(--success-dim);
  border: 1px solid color-mix(in srgb, var(--success) 35%, transparent);
}
.gis-file-chip-x {
  border: none;
  background: transparent;
  color: var(--success);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  padding: 0 2px;
}
.gis-file-chip-x:hover {
  color: var(--text);
}
.gis-input-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 16px;
  border: 1.5px solid var(--border);
  background: var(--bg-input);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.gis-input-row:focus-within {
  border-color: var(--accent);
  box-shadow: var(--accent-glow);
}
.gis-attach-btn {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  color: var(--text-dim);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}
.gis-attach-btn:hover {
  color: var(--accent);
  background: var(--bg-hover);
}
.gis-send-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: none;
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent-hover), var(--accent) 60%);
  color: var(--text-on-accent);
  cursor: pointer;
  box-shadow: var(--accent-glow);
  transition: filter 0.2s ease, transform 0.15s ease;
}
.gis-send-btn:hover:not(:disabled) {
  filter: brightness(1.08);
  transform: translateY(-1px);
}
.gis-send-btn:active:not(:disabled) {
  transform: scale(0.94);
}
.gis-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ---- 错误 / 加载 ---- */
.gis-error {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: var(--danger-dim);
  border: 1px solid color-mix(in srgb, var(--danger) 35%, transparent);
  color: var(--danger);
  font-size: 12px;
  line-height: 1.6;
}
.gis-spinner {
  width: 15px;
  height: 15px;
  border-radius: 50%;
  border: 2px solid color-mix(in srgb, var(--text-on-accent) 35%, transparent);
  border-top-color: var(--text-on-accent);
  animation: gisSpin 0.8s linear infinite;
}
.gis-spinner-lg {
  width: 22px;
  height: 22px;
  border-width: 3px;
  border-color: var(--border-light);
  border-top-color: var(--accent);
}
@keyframes gisSpin {
  to { transform: rotate(360deg); }
}
</style>
