import { defineConfig, presetUno, presetIcons, transformerDirectives } from "unocss"

export default defineConfig({
  presets: [
    presetUno({ dark: "class" }),
    presetIcons({ scale: 1.2 }),
  ],
  transformers: [transformerDirectives()],
  shortcuts: {
    "page-container": "h-full flex flex-col bg-[var(--bg)] text-[var(--text)]",
    "card": "bg-[var(--bg-card)] rounded-xl border border-[var(--border)] p-6",
    "btn-primary": "bg-[var(--accent)] text-white px-4 py-2 rounded-lg font-medium hover:opacity-85 transition cursor-pointer",
    "btn-secondary": "bg-[var(--bg-input)] text-[var(--text)] px-4 py-2 rounded-lg font-medium hover:opacity-85 transition cursor-pointer border border-[var(--border)]",
    "section-title": "text-lg font-semibold mb-4",
    "text-dim": "text-[var(--text-dim)]",
  },
  theme: {
    colors: {
      accent: "#38BDF8",
      "accent-hover": "#7DD3FC",
      green: "#4ADE80",
      yellow: "#FACC15",
      red: "#F87171",
      purple: "#A78BFA",
    },
  },
})
