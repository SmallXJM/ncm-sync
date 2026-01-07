<template>
  <div id="app">
    <nav class="main-nav" v-if="showNavigation">
      <div class="nav-container">
        <div class="nav-brand">
          <router-link to="/" class="brand-link">
            <span class="brand-icon">🎵</span>
            <span class="brand-text">ncm-sync</span>
          </router-link>
        </div>
        
        <div class="nav-links">
          <router-link to="/" class="nav-link">首页</router-link>
          <router-link to="/account" class="nav-link">账号管理</router-link>
          <router-link to="/music" class="nav-link">音乐搜索</router-link>
          <router-link to="/api" class="nav-link">API 测试</router-link>
        </div>
      </div>
    </nav>
    
    <main class="main-content" :class="{ 'with-nav': showNavigation }">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// 在某些页面隐藏导航栏
const showNavigation = computed(() => {
  return !['login'].includes(route.name)
})
</script>

<style>
/* 重置和基础样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f5f7;
  line-height: 1.6;
  overflow-x: hidden;
}

/* App 容器 */
#app {
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
}

/* 导航栏样式 */
.main-nav {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  flex-shrink: 0;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: #1d1d1f;
  font-weight: 600;
  font-size: 1.1rem;
}

.brand-icon {
  font-size: 1.5rem;
}

.nav-links {
  display: flex;
  gap: 1rem;
}

.nav-link {
  text-decoration: none;
  color: #1d1d1f;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
  font-size: 0.95rem;
}

.nav-link:hover {
  background: rgba(0, 122, 255, 0.1);
  color: #007aff;
}

.nav-link.router-link-active {
  background: #007aff;
  color: white;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  width: 100%;
  min-height: 100vh;
}

.main-content.with-nav {
  min-height: calc(100vh - 60px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-container {
    padding: 0 1rem;
  }
  
  .nav-links {
    gap: 0.5rem;
  }
  
  .nav-link {
    padding: 0.4rem 0.8rem;
    font-size: 0.9rem;
  }
  
  .brand-text {
    display: none;
  }
}

@media (max-width: 480px) {
  .nav-links {
    gap: 0.25rem;
  }
  
  .nav-link {
    padding: 0.3rem 0.6rem;
    font-size: 0.85rem;
  }
}
</style>
