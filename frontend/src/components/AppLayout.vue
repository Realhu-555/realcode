<script setup lang="ts">
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useProjectStore } from "../stores/project"
import { useTheme } from "../composables/useTheme"

const route = useRoute()
const router = useRouter()
const isDark = useTheme()
const projectStore = useProjectStore()

// ---- 路由感知 ----
const currentPage = computed(() => {
  const map: Record<string, string> = {
    create: "新建项目",
    strategy: "策略确认",
    preview: "内容预览",
  }
  return map[route.name as string] ?? ""
})

const isOnPage = (name: string) => route.name === name

// 导航项
const navItems = [
  { name: "create", label: "新建项目", icon: "✚", route: "/create" },
]

// 如果有项目在运行中，显示项目导航
const activeProjectNav = computed(() => {
  if (!projectStore.currentProjectId) return []
  const id = projectStore.currentProjectId
  return [
    { name: "strategy", label: "策略确认", icon: "⚙", route: `/strategy/${id}` },
    { name: "preview", label: "内容预览", icon: "▤", route: `/preview/${id}` },
  ]
})
</script>

<template>
  <div class="h-screen flex">
    <!-- ===== 侧边栏 ===== -->
    <aside class="h-screen w-240px bg-[var(--bg-sidebar)] border-r border-[var(--border)] flex flex-col shrink-0 relative overflow-hidden sticky top-0">
      <!-- 装饰：右侧微光 -->
      <div class="absolute inset-y-0 right-0 w-px bg-gradient-to-b from-transparent via-[var(--accent)]/10 to-transparent" />

      <!-- Logo -->
      <div class="relative px-5 pt-7 pb-5">
        <router-link to="/create" class="no-underline block group">
          <h1 class="font-display text-[1.65rem] font-black text-[var(--text)] tracking-tight leading-none">
            素<span class="text-[var(--accent)]">宣</span>
          </h1>
          <p class="text-[10px] text-muted mt-1 tracking-[0.2em] uppercase">Suxuan</p>
        </router-link>
      </div>

      <!-- 分隔 -->
      <div class="px-5 mb-3">
        <div class="h-px bg-gradient-to-r from-[var(--border)] to-transparent" />
      </div>

      <!-- 导航区 -->
      <nav class="px-3 space-y-0.5">
        <!-- 固定导航 -->
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="item.route"
          class="no-underline"
        >
          <div
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 cursor-pointer group"
            :class="isOnPage(item.name)
              ? 'bg-[var(--accent-dim)] text-[var(--accent)]'
              : 'text-dim hover:text-[var(--text)] hover:bg-[var(--bg-hover)]'"
          >
            <span class="text-base w-6 text-center shrink-0">{{ item.icon }}</span>
            <span class="font-medium">{{ item.label }}</span>
            <span
              v-if="isOnPage(item.name)"
              class="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--accent)]"
            />
          </div>
        </router-link>

        <!-- 分隔（有活跃项目时显示） -->
        <div
          v-if="activeProjectNav.length"
          class="px-5 py-2"
        >
          <div class="h-px bg-gradient-to-r from-[var(--border)] to-transparent" />
        </div>

        <!-- 当前项目导航 -->
        <router-link
          v-for="item in activeProjectNav"
          :key="item.name"
          :to="item.route"
          class="no-underline"
        >
          <div
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 cursor-pointer"
            :class="isOnPage(item.name)
              ? 'bg-[var(--accent-dim)] text-[var(--accent)]'
              : 'text-dim hover:text-[var(--text)] hover:bg-[var(--bg-hover)]'"
          >
            <span class="text-base w-6 text-center shrink-0">{{ item.icon }}</span>
            <span class="font-medium">{{ item.label }}</span>
            <span
              v-if="isOnPage(item.name)"
              class="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--accent)]"
            />
          </div>
        </router-link>
      </nav>

      <!-- 弹性空白 -->
      <div class="flex-1" />

      <!-- 空状态灵感区 -->
      <div v-if="!projectStore.currentProjectId" class="px-3 pb-3">
        <div class="mx-2 px-4 py-3 rounded-lg bg-[var(--bg-hover)] border border-[var(--border)]/50">
          <p class="text-[10px] text-muted tracking-wide leading-relaxed">
            <span class="text-[var(--accent)]">✦</span>&nbsp; 好内容是从一壶茶和一颗安静的心开始的
          </p>
        </div>
      </div>

      <!-- 底部分隔 -->
      <div class="px-5 py-2">
        <div class="h-px bg-gradient-to-r from-transparent via-[var(--border)]/50 to-transparent" />
      </div>

      <!-- 主题切换 -->
      <div class="px-3 pb-5">
        <button
          class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-dim transition-all duration-200 hover:text-[var(--text)] hover:bg-[var(--bg-hover)]"
          @click="isDark = !isDark"
        >
          <span class="text-sm w-6 text-center">{{ isDark ? '☀' : '☾' }}</span>
          <span>{{ isDark ? '切至亮色' : '切至暗色' }}</span>
        </button>
      </div>
    </aside>

    <!-- ===== 主内容区 ===== -->
    <div class="flex-1 flex flex-col overflow-hidden relative">
      <!-- 🔆 背景微光 -->
      <div class="absolute inset-0 pointer-events-none opacity-30"
        style="background: radial-gradient(ellipse 80% 60% at 70% 15%, rgba(212,168,83,0.03) 0%, transparent 60%);" />

      <!-- 顶栏 -->
      <header class="shrink-0 h-14 border-b border-[var(--border)] bg-[var(--bg-card)]/80 backdrop-blur-sm flex items-center px-6 gap-4 z-10">
        <!-- 当前位置 -->
        <div class="flex items-center gap-2 text-sm">
          <span class="text-muted">/</span>
          <span class="font-medium text-[var(--text)]">{{ currentPage || "素宣" }}</span>
        </div>

        <div class="flex-1" />

        <!-- 项目名称（有活跃项目时显示） -->
        <div
          v-if="projectStore.currentProjectId"
          class="flex items-center gap-2 text-xs text-muted"
        >
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
          <span class="font-mono text-[11px]">{{ projectStore.currentProjectId.slice(0, 8) }}</span>
        </div>
      </header>

      <!-- 页面内容 -->
      <div class="flex-1 overflow-hidden relative">
        <slot />
      </div>
    </div>
  </div>
</template>
