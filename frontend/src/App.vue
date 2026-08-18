<script setup lang="ts">
import { computed } from "vue"
import { useRoute } from "vue-router"
import { darkTheme, lightTheme, zhCN } from "naive-ui"
import AppLayout from "./components/AppLayout.vue"
import { useTheme } from "./composables/useTheme"

const isDark = useTheme()
const route = useRoute()
const isStandalone = computed(() => Boolean(route.meta.standalone))

const naiveTheme = computed(() => isDark.value ? darkTheme : lightTheme)
</script>

<template>
  <n-config-provider :theme="naiveTheme" :locale="zhCN">
    <n-notification-provider>
      <n-message-provider>
        <AppLayout v-if="!isStandalone">
          <router-view />
        </AppLayout>
        <router-view v-else />
      </n-message-provider>
    </n-notification-provider>
  </n-config-provider>
</template>
