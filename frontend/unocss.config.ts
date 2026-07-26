import { defineConfig, presetUno, presetIcons, transformerDirectives } from "unocss"

export default defineConfig({
  presets: [
    presetUno({ dark: "class" }),
    presetIcons({ scale: 1.2 }),
  ],
  transformers: [transformerDirectives()],
  rules: [
    ["font-display", { "font-family": "var(--font-display)" }],
  ],
  shortcuts: {
    "page-container": "h-full flex flex-col bg-[var(--bg)] text-[var(--text)]",
    "card": "bg-[var(--bg-card)] rounded-xl border border-[var(--border)] p-6 transition-shadow duration-300 hover:shadow-[var(--shadow-md)]",
    "card-accent": "bg-[var(--bg-card)] rounded-xl border border-[var(--border)] p-6 border-l-3 border-l-[var(--accent)]",
    "btn-primary": "bg-[var(--accent)] text-[var(--text-on-accent)] px-5 py-2.5 rounded-lg font-medium tracking-wide transition-all duration-200 cursor-pointer hover:brightness-110 hover:shadow-[var(--accent-glow)] active:scale-97",
    "btn-ghost": "text-[var(--text-dim)] px-4 py-2 rounded-lg font-medium transition cursor-pointer hover:text-[var(--text)] hover:bg-[var(--bg-hover)]",
    "heading-display": "font-display font-bold tracking-tight",
    "heading-section": "font-display font-semibold text-lg",
    "text-dim": "text-[var(--text-dim)]",
    "text-muted": "text-[var(--text-muted)]",
    "divider": "h-px bg-[var(--border)] my-4",
    "accent-line": "w-8 h-0.5 bg-[var(--accent)] rounded-full",
    "tag": "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
    "tag-accent": "tag bg-[var(--accent-dim)] text-[var(--accent)]",
    "tag-success": "tag bg-[var(--success-dim)] text-[var(--success)]",
    "tag-warning": "tag bg-[var(--warning-dim)] text-[var(--warning)]",
  },
  theme: {
    colors: {
      accent: "#D4A853",
      "accent-hover": "#E0BC6B",
      "accent-dim": "#2A2418",
      success: "#4ADE80",
      "success-dim": "#142618",
      warning: "#F59E0B",
      "warning-dim": "#2A2010",
      danger: "#EF4444",
      "danger-dim": "#2A1414",
      channel: {
        gongzhonghao: "#5B9A7C",
        zhihu: "#5B8FBF",
        xiaohongshu: "#C45B6C",
      },
    },
  },
})
