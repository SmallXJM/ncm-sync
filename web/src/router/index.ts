import { createRouter, createWebHistory } from 'vue-router'
// const DashboardView = () => import('../views/Dashboard.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: {
        title: '仪表盘',
      },
    },
    {
      path: '/account',
      name: 'account',
      component: () => import('../views/AccountView.vue'),
      meta: {
        title: '登录态',
      },
    },
    {
      path: '/config',
      name: 'config',
      component: () => import('../views/ConfigView.vue'),
      meta: {
        title: '设置',
      },
    },
    {
      path: '/my/playlist',
      name: 'my-playlist',
      component: () => import('../views/MyPlaylistView.vue'),
      meta: {
        title: '我的歌单',
      },
    },
    {
      path: '/music',
      name: 'music',
      component: () => import('../views/MusicView.vue'),
      meta: {
        title: '音乐',
      },
    },
    {
      path: '/music/:taskId',
      name: 'music-detail',
      component: () => import('../views/MusicDetailView.vue'),
      meta: {
        title: '音乐详情',
        parent: { title: '音乐', to: '/music' },
      },
    },
    {
      path: '/subscription',
      name: 'subscription',
      component: () => import('../views/SubscriptionView.vue'),
      meta: {
        title: '订阅',
      },
    },
  ],
})

// 设置浏览器标签页标题
router.afterEach((to) => {
  const title = to.meta.title ?? 'ncm-sync'
  document.title = `${title} - ncm sync`
})

export default router
