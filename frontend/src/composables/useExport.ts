import { useClipboard, useDownload } from "@vueuse/core"
import { ref } from "vue"

export function useExport() {
  const { copy, copied } = useClipboard()
  const downloading = ref(false)

  async function copyContent(text: string) {
    await copy(text)
    setTimeout(() => copied.value = false, 2000)
  }

  function downloadMarkdown(content: string, filename: string) {
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${filename}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return { copyContent, downloadMarkdown, copied, downloading }
}
