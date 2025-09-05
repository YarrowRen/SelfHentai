// composables/useMomMode.ts
import { ref, computed } from 'vue'

const isMomModeEnabled = ref(false)

export function useMomMode() {
  // 从 localStorage 初始化状态
  const initMomMode = () => {
    const savedMode = localStorage.getItem('mom-mode')
    isMomModeEnabled.value = savedMode === 'true'
    updateBodyClass()
  }

  // 切换妈妈模式
  const toggleMomMode = () => {
    isMomModeEnabled.value = !isMomModeEnabled.value
    localStorage.setItem('mom-mode', isMomModeEnabled.value.toString())
    updateBodyClass()
  }

  // 更新 body 的 class
  const updateBodyClass = () => {
    if (isMomModeEnabled.value) {
      document.body.classList.add('mom-mode')
    } else {
      document.body.classList.remove('mom-mode')
    }
  }

  // 获取图标
  const getMomModeIcon = () => {
    return isMomModeEnabled.value ? '👩‍👧‍👦' : '🔒'
  }

  // 获取标签文本
  const getMomModeLabel = () => {
    return isMomModeEnabled.value ? '妈妈模式' : '隐私模式'
  }

  // 计算属性
  const isMomMode = computed(() => isMomModeEnabled.value)

  return {
    isMomMode,
    toggleMomMode,
    getMomModeIcon,
    getMomModeLabel,
    initMomMode
  }
}