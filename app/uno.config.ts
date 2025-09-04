import { defineConfig, presetWind4, presetAttributify, presetIcons } from 'unocss'

export default defineConfig({
  presets: [presetWind4(), presetAttributify(), presetIcons()],
  content: {
    pipeline: { include: ['src/**/*.{vue,js,ts,jsx,tsx}'] }
  },
  theme: {
    colors: {
      primary: '#ff6b6b',
      panel: '#0b1220',
      bg1: '#0f172a',
      bg2: '#071126',
      muted: '#94a3b8',
      text: '#e6f0ff',
    },
  },
})
