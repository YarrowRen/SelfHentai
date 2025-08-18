<template>
  <div class="theme-toggle">
    <Button
      @click="toggleTheme"
      class="theme-btn"
      :class="{ 'dark': isDark }"
      v-tooltip="`当前: ${getThemeLabel()}, 点击切换`"
      severity="secondary"
      outlined
    >
      <span class="theme-icon">{{ getThemeIcon() }}</span>
      <span class="theme-label">{{ getThemeLabel() }}</span>
    </Button>
  </div>
</template>

<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'

const { isDark, toggleTheme, getThemeIcon, getThemeLabel } = useTheme()
</script>

<style scoped>
.theme-toggle {
  display: inline-block;
}

.theme-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  min-width: 120px;
  /* 主题切换按钮专用背景色 */
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: white !important;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.25);
}

.theme-icon {
  font-size: 16px;
}

.theme-label {
  font-weight: 500;
}

.theme-btn:hover {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.theme-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

/* 深色模式时的特殊样式 */
.theme-btn.dark {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%) !important;
  box-shadow: 0 2px 6px rgba(74, 85, 104, 0.25);
}

.theme-btn.dark:hover {
  background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%) !important;
  box-shadow: 0 4px 12px rgba(74, 85, 104, 0.4);
}

/* 添加脉动动画效果 */
.theme-btn {
  position: relative;
  overflow: hidden;
}

.theme-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s;
}

.theme-btn:hover::before {
  left: 100%;
}

/* 响应式设计 - 小屏幕只显示图标 */
@media (max-width: 768px) {
  .theme-label {
    display: none;
  }
  
  .theme-btn {
    min-width: auto;
    padding: 8px;
  }
}
</style>