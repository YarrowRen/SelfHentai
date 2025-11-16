import { createRouter, createWebHistory } from 'vue-router';
import Home from '@/components/Home.vue';
import SyncData from '@/components/SyncData.vue'
import DataAnalys from '@/components/DataAnalys.vue';
import GalleryDetail from '@/components/GalleryDetail.vue';
import Settings from '@/components/Settings.vue';
import Reader from '@/components/Reader.vue';
import AutoTranslate from '@/components/AutoTranslate.vue'; 

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
    path: '/settings',
    name: 'Settings',
    component: Settings,
  },
  {
    path: '/gallery/:gid',  // ExHentai 动态路由
    name: 'GalleryDetail',
    component: GalleryDetail,
    props: true,  // 将参数作为props传递给组件
  },
  {
    path: '/reader/:gid/:token',  // ExHentai 阅读器路由
    name: 'Reader',
    component: Reader,
    props: true,  // 将参数作为props传递给组件
  },
  {
    path: '/auto-translate/:gid/:token',  // ExHentai 自动翻译路由
    name: 'AutoTranslate',
    component: AutoTranslate,
    props: true,  // 将参数作为props传递给组件
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
