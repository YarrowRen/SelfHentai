import { createRouter, createWebHistory } from 'vue-router';
import Home from '@/components/Home.vue';
import SyncData from '@/components/SyncData.vue'
import DataAnalys from '@/components/DataAnalys.vue';
import GalleryDetail from '@/components/GalleryDetail.vue';
import ImageViewer from '@/components/ImageViewer.vue';
import Settings from '@/components/Settings.vue'; 

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
    path: '/gallery/:gid',  // EX 动态路由
    name: 'GalleryDetail',
    component: GalleryDetail,
    props: true,  // 将参数作为props传递给组件
  },
  {
    path: '/jm/:id',  // JM 动态路由
    name: 'JMGalleryDetail',
    component: GalleryDetail,
    props: true,  // 将参数作为props传递给组件
  },
  {
    path: '/gallery/:gid/:token/page/:page',  // 图片查看器路由
    name: 'ImageViewer',
    component: ImageViewer,
    props: true,  // 将参数作为props传递给组件
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
