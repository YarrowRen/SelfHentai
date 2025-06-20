<script setup lang="ts">
</script>

<template>

  <!-- Navigation Bar -->
  <div class="navigation-bar">
    <ul class="nav-menu">
      <li><a href="/">Front Page</a></li>
      <li><a href="/data">Data Analys</a></li>
      <li><a href="/sync">Sync Data</a></li>
      <li><a href="/favorites">Favorites</a></li>
      <li><a href="#settings">Settings</a></li>
      <li><a href="https://exhentai.org/">ExHentai</a></li>
    </ul>
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
    background-color: #34353a;
    padding: 10px 0;
  }
  
  .nav-menu {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    justify-content: center;
  }
  
  .nav-menu li {
    margin: 0 15px;
  }
  
  .nav-menu a {
    color: white;
    text-decoration: none;
    font-weight: bold;
    font-size: 14px;
  }
  
  .nav-menu a:hover {
    color: #ddd;
    text-decoration: underline;
  }


</style>
