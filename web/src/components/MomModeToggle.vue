<template>
  <div class="mom-mode-toggle">
    <Button
      @click="toggleMomMode"
      class="mom-mode-btn"
      :class="{ 'active': isMomMode }"
      v-tooltip="`${getMomModeLabel()}: ${isMomMode ? '已开启' : '已关闭'}`"
      severity="secondary"
      outlined
    >
      <span class="mom-mode-icon">{{ getMomModeIcon() }}</span>
      <span class="mom-mode-label">{{ getMomModeLabel() }}</span>
    </Button>
  </div>
</template>

<script setup lang="ts">
import { useMomMode } from '@/composables/useMomMode'

const { isMomMode, toggleMomMode, getMomModeIcon, getMomModeLabel } = useMomMode()
</script>

<style scoped>
.mom-mode-toggle {
  display: inline-block;
}

.mom-mode-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  min-width: 120px;
  /* 妈妈模式按钮背景色 */
  background: linear-gradient(135deg, #ff9a8b 0%, #fecfef 50%, #fecfef 100%) !important;
  border: none !important;
  color: #333 !important;
  box-shadow: 0 2px 6px rgba(255, 154, 139, 0.25);
}

.mom-mode-icon {
  font-size: 16px;
}

.mom-mode-label {
  font-weight: 500;
}

.mom-mode-btn:hover {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #ff8a80 0%, #f8bbd9 50%, #f8bbd9 100%) !important;
  box-shadow: 0 4px 12px rgba(255, 154, 139, 0.4);
}

.mom-mode-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(255, 154, 139, 0.3);
}

/* 激活状态时的特殊样式 */
.mom-mode-btn.active {
  background: linear-gradient(135deg, #81c784 0%, #a5d6a7 100%) !important;
  box-shadow: 0 2px 6px rgba(129, 199, 132, 0.25);
  color: white !important;
}

.mom-mode-btn.active:hover {
  background: linear-gradient(135deg, #66bb6a 0%, #81c784 100%) !important;
  box-shadow: 0 4px 12px rgba(129, 199, 132, 0.4);
}

/* 添加脉动动画效果 */
.mom-mode-btn {
  position: relative;
  overflow: hidden;
}

.mom-mode-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s;
}

.mom-mode-btn:hover::before {
  left: 100%;
}

/* 响应式设计 - 小屏幕只显示图标 */
@media (max-width: 768px) {
  .mom-mode-label {
    display: none;
  }
  
  .mom-mode-btn {
    min-width: auto;
    padding: 8px;
  }
}
</style>