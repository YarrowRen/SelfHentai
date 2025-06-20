import { createRouter, createWebHistory } from 'vue-router';
import Home from '../components/Home.vue';
import SyncData from '../components/SyncData.vue'
import DataAnalys from '../components/DataAnalys.vue';
import GalleryDetail from '../components/GalleryDetail.vue'; // 导入新的组件
import Favorites from '../components/Favorites.vue'; // 导入新的组件

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/data',
    name: 'DataAnalys',
    component: DataAnalys,
  },
  {
    path: '/sync',
    name: 'SyncData',
    component: SyncData,
  },
  {
    path: '/gallery/:gid',  // 添加动态路由
    name: 'GalleryDetail',
    component: GalleryDetail,
    props: true,  // 将参数作为props传递给组件
  },
  {
    path: '/favorites',  // 添加动态路由
    name: 'Favorites',
    component: Favorites
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
