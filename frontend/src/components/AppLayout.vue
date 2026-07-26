<script setup lang="ts">
import { useLocalStorage } from "@vueuse/core"
import { useProjectStore } from "../stores/project"

const isDark = useLocalStorage("theme-dark", true)
const projectStore = useProjectStore()
</script>

<template>
  <div class="h-full flex">
    <!-- 左侧边栏 -->
    <aside class="w-260px bg-[var(--bg-card)] border-r border-[var(--border)] flex flex-col shrink-0">
      <div class="p-5 border-b border-[var(--border)] flex items-center gap-3">
        <span class="text-2xl">📝</span>
        <div>
          <h1 class="text-15px font-semibold">营销内容平台</h1>
          <p class="text-11px text-dim">AI Dev Platform</p>
        </div>
      </div>

      <!-- 新建按钮 -->
      <div class="p-4">
        <router-link to="/create">
          <n-button type="primary" block secondary>
            <template #icon>
              <span class="text-lg">+</span>
            </template>
            新建营销项目
          </n-button>
        </router-link>
      </div>

      <!-- 项目列表（TODO: 从后端获取历史项目） -->
      <div class="flex-1 overflow-y-auto px-2">
        <div class="px-3 py-2 text-11px text-dim font-medium uppercase tracking-wider">最近项目</div>
        <div class="px-3 py-4 text-13px text-dim text-center">
          暂无历史项目
        </div>
      </div>

      <!-- 底部主题切换 -->
      <div class="p-4 border-t border-[var(--border)]">
        <n-button text @click="isDark = !isDark" class="w-full justify-start">
          <span class="mr-2">{{ isDark ? '☀️' : '🌙' }}</span>
          {{ isDark ? '亮色模式' : '暗色模式' }}
        </n-button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 overflow-hidden">
      <slot />
    </main>
  </div>
</template>
