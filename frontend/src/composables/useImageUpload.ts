import { ref } from "vue"

export function useImageUpload(maxCount = 5) {
  const images = ref<string[]>([])       // base64 data URLs
  const uploading = ref(false)
  const error = ref<string | null>(null)

  /** 将 File 转为 base64 data URL */
  function fileToDataUrl(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = () => reject(new Error(`读取失败: ${file.name}`))
      reader.readAsDataURL(file)
    })
  }

  /** 添加图片 */
  async function addImages(files: FileList | File[]) {
    uploading.value = true
    error.value = null

    const remaining = maxCount - images.value.length
    if (remaining <= 0) {
      error.value = `最多上传 ${maxCount} 张图片`
      uploading.value = false
      return
    }

    const toProcess = Array.from(files).slice(0, remaining)

    // 检查文件类型
    for (const f of toProcess) {
      if (!f.type.startsWith("image/")) {
        error.value = `不支持的文件类型: ${f.name}`
        uploading.value = false
        return
      }
      if (f.size > 10 * 1024 * 1024) {
        error.value = `图片过大（>10MB）: ${f.name}`
        uploading.value = false
        return
      }
    }

    try {
      const urls = await Promise.all(toProcess.map(fileToDataUrl))
      images.value.push(...urls)
    } catch (e: any) {
      error.value = e.message || "图片处理失败"
    } finally {
      uploading.value = false
    }
  }

  /** 删除图片 */
  function removeImage(index: number) {
    images.value.splice(index, 1)
  }

  /** 清空 */
  function clear() {
    images.value = []
    error.value = null
  }

  return { images, uploading, error, addImages, removeImage, clear, maxCount }
}
