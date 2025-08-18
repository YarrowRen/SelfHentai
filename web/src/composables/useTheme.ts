import { ref, watch } from 'vue'

export type Theme = 'light' | 'dark'

const isDark = ref<boolean>(false)
const theme = ref<Theme>('dark')

// 立即同步应用主题，防止闪烁
const applyThemeImmediate = (themeValue: Theme) => {
  const html = document.documentElement
  const body = document.body
  const isDarkMode = themeValue === 'dark'
  
  if (isDarkMode) {
    html.classList.add('my-app-dark')
    html.classList.remove('my-app-light')
    // 同步更新 body 背景色
    if (body) {
      body.style.backgroundColor = '#0f172a'
      body.style.color = '#f1f5f9'
    }
  } else {
    html.classList.add('my-app-light')
    html.classList.remove('my-app-dark')
    // 同步更新 body 背景色
    if (body) {
      body.style.backgroundColor = '#faf8f5'
      body.style.color = '#2d3748'
    }
  }
  
  return isDarkMode
}

// 从 localStorage 获取保存的主题设置并立即应用
const savedTheme = localStorage.getItem('theme') as Theme
if (savedTheme && ['light', 'dark'].includes(savedTheme)) {
  theme.value = savedTheme
  isDark.value = applyThemeImmediate(savedTheme)
} else {
  // 默认深色模式
  theme.value = 'dark'
  isDark.value = applyThemeImmediate('dark')
}

// 更新主题状态
const updateTheme = () => {
  isDark.value = applyThemeImmediate(theme.value)
}

// 监听主题变化
watch(theme, () => {
  localStorage.setItem('theme', theme.value)
  updateTheme()
}, { immediate: true })

export const useTheme = () => {
  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
  }

  const toggleTheme = () => {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  const getThemeIcon = () => {
    return theme.value === 'light' ? '☀️' : '🌙'
  }

  const getThemeLabel = () => {
    return theme.value === 'light' ? '浅色模式' : '深色模式'
  }

  return {
    isDark,
    theme,
    setTheme,
    toggleTheme,
    getThemeIcon,
    getThemeLabel
  }
}