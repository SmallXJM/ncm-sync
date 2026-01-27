import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/auth'
import { useAuthStore } from '@/stores/auth'
// const DashboardView = () => import('../views/Dashboard.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: {
        title: '登录',
        layout: false,
      },
    },
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

// Navigation Guard
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  if (!authStore.isInitialized.value) {
    await authStore.fetchAuthConfig()
  }

  const token = getToken()
  const requireAuth = authStore.isAuthEnabled.value

  if (!requireAuth) {
    if (to.path === '/login') {
      next('/')
    } else {
      next()
    }
    return
  }

  if (to.path === '/login') {
    if (token) {
      // 如果已登录，跳转到 redirect 参数指定的页面，或者首页
      const redirect = to.query.redirect as string
      next(redirect || '/')
    } else {
      next()
    }
  } else {
    if (!token) {
      // 未登录，跳转到登录页，并携带当前页面路径作为 redirect 参数
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    } else {
      next()
    }
  }
})

// 设置浏览器标签页标题
router.afterEach((to) => {
  const title = to.meta.title ?? 'NCM Sync'
  document.title = `${title} - NCM Sync`
})

export default router
