<template>
  <div class="page" style="display: flex; align-items: center; justify-content: center; padding: 2rem;">
    <div class="hero-section">
      <h1 class="hero-title">NCM 操作台</h1>
      <p class="hero-subtitle">网易云音乐 API 管理控制台</p>
      
      <div class="quick-actions">
        <router-link to="/account" class="action-card">
          <div class="action-icon">👤</div>
          <h3>账号管理</h3>
          <p>管理登录账号和会话</p>
        </router-link>
        
        <router-link to="/music" class="action-card">
          <div class="action-icon">🎵</div>
          <h3>音乐搜索</h3>
          <p>搜索和管理音乐资源</p>
        </router-link>
        
        <router-link to="/api" class="action-card">
          <div class="action-icon">🔧</div>
          <h3>API 测试</h3>
          <p>测试和调试 API 接口</p>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
// Home page - NCM Control Panel
</script>


