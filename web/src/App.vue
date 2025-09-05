<script setup lang="ts">
import { onMounted } from 'vue'
import { useTheme } from '@/composables/useTheme'
import { useMomMode } from '@/composables/useMomMode'
import ThemeToggle from '@/components/ThemeToggle.vue'
import MomModeToggle from '@/components/MomModeToggle.vue'

// 初始化主题和妈妈模式
const { isDark } = useTheme()
const { initMomMode } = useMomMode()

onMounted(() => {
  initMomMode()
})
</script>

<template>

  <!-- Navigation Bar -->
  <div class="navigation-bar">
    <ul class="nav-menu">
      <li><a href="/">Front Page</a></li>
      <li><a href="/data">Data Analys</a></li>
      <li><a href="/sync">Sync Data</a></li>
      <li><a href="/settings">Settings</a></li>
      <li><a href="https://exhentai.org/">ExHentai</a></li>
    </ul>
    <div class="theme-toggle-nav">
      <MomModeToggle />
      <ThemeToggle />
    </div>
  </div>
  <router-view></router-view> <!-- 路由出口 -->
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}


  /* Navigation Bar Styles */
  .navigation-bar {
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .nav-menu {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    justify-content: center;
    flex: 1;
  }
  
  .theme-toggle-nav {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .nav-menu li {
    margin: 0 15px;
  }
  
  .nav-menu a {
    color: var(--text-color);
    text-decoration: none;
    font-weight: bold;
    font-size: 14px;
    transition: color 0.3s ease;
  }
  
  .nav-menu a:hover {
    color: var(--primary-color);
    text-decoration: underline;
  }


</style>
