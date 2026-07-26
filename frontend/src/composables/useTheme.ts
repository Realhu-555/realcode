import { useLocalStorage } from "@vueuse/core"
import { watch } from "vue"

// 模块级单例 Ref，所有组件共享同一个主题状态
const isDark = useLocalStorage("theme-dark", true)

// 同步 CSS 变量
watch(isDark, (dark) => {
  document.documentElement.classList.toggle("light", !dark)
}, { immediate: true })

export function useTheme() {
  return isDark
}
