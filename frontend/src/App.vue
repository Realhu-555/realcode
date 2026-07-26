<script setup lang="ts">
import { darkTheme, zhCN } from "naive-ui"
import { useLocalStorage } from "@vueuse/core"
import AppLayout from "./components/AppLayout.vue"

const isDark = useLocalStorage("theme-dark", true)
</script>

<template>
  <n-config-provider :theme="isDark ? darkTheme : null" :locale="zhCN">
    <n-notification-provider>
      <n-message-provider>
        <AppLayout>
          <router-view />
        </AppLayout>
      </n-message-provider>
    </n-notification-provider>
  </n-config-provider>
</template>
