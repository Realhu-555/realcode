<script setup lang="ts">
import { computed } from "vue"
import { darkTheme, lightTheme, zhCN } from "naive-ui"
import AppLayout from "./components/AppLayout.vue"
import { useTheme } from "./composables/useTheme"

const isDark = useTheme()

const naiveTheme = computed(() => isDark.value ? darkTheme : lightTheme)
</script>

<template>
  <n-config-provider :theme="naiveTheme" :locale="zhCN">
    <n-notification-provider>
      <n-message-provider>
        <AppLayout>
          <router-view />
        </AppLayout>
      </n-message-provider>
    </n-notification-provider>
  </n-config-provider>
</template>
