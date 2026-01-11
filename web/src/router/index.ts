import { createRouter, createWebHistory } from 'vue-router'
const HomeView = () => import('../views/HomeView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        title: '首页',
      },
    },
    {
      path: '/account',
      name: 'account',
      component: () => import('../views/AccountView.vue'),
      meta: {
        title: '账号管理',
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
  ],
})

// 设置浏览器标签页标题
router.afterEach((to) => {
  const title = to.meta.title ?? 'ncm-sync'
  document.title = `${title} - ncm sync`
})

export default router
