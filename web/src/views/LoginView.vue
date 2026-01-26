
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { sha256, setToken } from '@/utils/auth'
import AppToast from '@/components/AppToast.vue'
import { toast } from '@/utils/toast'

const router = useRouter()

const username = ref('admin')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    toast.error('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    const hashedPassword = await sha256(password.value)
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
    toast.error('登录出错')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>NCM Sync</h1>
        <p>登录以继续</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label>用户名</label>
          <input 
            v-model="username" 
            type="text" 
            placeholder="请输入用户名"
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label>密码</label>
          <input 
            v-model="password" 
            type="password" 
            placeholder="请输入密码"
            :disabled="loading"
          />
        </div>
        
        <button type="submit" :disabled="loading" class="login-btn">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped lang="scss">
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--color-background);
  color: var(--color-text);
}

.login-box {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
  background-color: var(--color-surface);
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
  
  h1 {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
    color: var(--color-primary);
  }
  
  p {
    color: var(--color-text-secondary);
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
    color: var(--color-text-secondary);
  }
  
  input {
    padding: 0.75rem;
    border-radius: 4px;
    border: 1px solid var(--color-border);
    background-color: var(--color-background);
    color: var(--color-text);
    transition: border-color 0.2s;
    
    &:focus {
      outline: none;
      border-color: var(--color-primary);
    }
    
    &:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }
  }
}

.login-btn {
  padding: 0.75rem;
  background-color: var(--color-primary);
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
  transition: opacity 0.2s;
  margin-top: 1rem;
  
  &:hover:not(:disabled) {
    opacity: 0.9;
  }
  
  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
}
</style>
