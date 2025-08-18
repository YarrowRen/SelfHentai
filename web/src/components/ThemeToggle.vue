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
}

.theme-icon {
  font-size: 16px;
}

.theme-label {
  font-weight: 500;
}

.theme-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
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