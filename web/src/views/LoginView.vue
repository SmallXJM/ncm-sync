
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { sha256, setToken } from '@/utils/auth'
import AppToast from '@/components/AppToast.vue'
import { toast } from '@/utils/toast'

const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    toast.error('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    const hashedPassword = await sha256(password.value, username.value)
    const res = await api.auth.login({
      username: username.value,
      password: hashedPassword
    })

    if (res.success && res.data.code === 200 && res.data.data) {
      setToken(res.data.data.token)
      toast.success('登录成功') 
      router.push('/')
    } else {
      toast.error(res.success ? res.data.message || '登录失败' : res.error)
    }
  } catch (e) {
    toast.error(`登录出错: ${e}`)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page login-page">
    <div class="glass-card login-card">
      <div class="login-header">
        <div class="brand-container">
          <span class="brand-icon">
            <img alt="logo" width="48" height="48" />
          </span>
          <h1 class="brand-title">NCM Sync</h1>
        </div>
        <p class="login-subtitle">登录以继续</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label>用户名</label>
          <input 
            v-model="username" 
            type="text" 
            class="input"
            placeholder="请输入用户名"
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label>密码</label>
          <input 
            v-model="password" 
            type="password" 
            class="input"
            placeholder="请输入密码"
            :disabled="loading"
          />
        </div>
        
        <button type="submit" :disabled="loading" class="btn btn-primary login-btn">
          <div v-if="loading" class="loading-spinner"></div>
          <span>{{ loading ? '登录中...' : '登录' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  background-color: var(--bg-body);
  color: var(--text-primary);
  padding: var(--spacing-lg);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.login-header {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  
  .brand-container {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xs);
  }

  .brand-icon {
    flex-shrink: 0;
    /* 防止被压缩 */
    display: inline-flex;
    /* 让 img 或 svg 可以居中对齐 */
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}

  .brand-icon img {
    content: var(--img-favicon);
    width: 48px;
    height: 48px;
    object-fit: contain;
  }
  
  .brand-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }
  
  .login-subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
    margin: 0;
  }
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  
  label {
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-primary);
  }
}

.login-btn {
  width: 100%;
  margin-top: 1rem;
  justify-content: center;
}



</style>
