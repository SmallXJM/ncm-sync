# API 管理系统使用指南

## 概述

这个 API 管理系统提供了统一的接口调用方式，解决了以下问题：

- ✅ **集中管理** - 所有 API 调用集中在一个地方
- ✅ **类型安全** - 提供清晰的参数和返回值结构
- ✅ **错误处理** - 统一的错误处理和超时控制
- ✅ **环境配置** - 支持开发/生产环境配置
- ✅ **代码复用** - 避免重复的 fetch 代码

## 目录结构

```
src/api/
├── index.js              # 统一入口文件
├── config.js             # API 配置和端点定义
├── request.js            # HTTP 请求工具
├── services/             # 具体服务实现
│   ├── authService.js    # 认证相关 API
│   ├── userService.js    # 用户相关 API
│   └── musicService.js   # 音乐相关 API
└── README.md            # 使用指南
```

## 基础使用

### 1. 导入 API

```javascript
// 方式1：导入统一 API 对象
import api from '@/api'

// 方式2：导入具体服务
import { authService, userService, musicService } from '@/api'

// 方式3：导入 HTTP 工具
import { http, get, post } from '@/api'
```

### 2. 调用 API

```javascript
// 使用统一 API 对象
const result = await api.auth.startQRLogin()
const userInfo = await api.user.getCurrentUser()
const searchResults = await api.music.enhancedSearch({
  keywords: '周杰伦',
  search_type: 'song'
})

// 使用具体服务
const result = await authService.startQRLogin()
const userInfo = await userService.getCurrentUser()
```

### 3. 处理响应

```javascript
async function loadUserData() {
  const result = await api.user.getCurrentUser()
  
  if (result.success) {
    // 请求成功
    const userData = result.data
    console.log('用户数据:', userData)
  } else {
    // 请求失败
    console.error('请求失败:', result.error)
    showToast('加载用户数据失败', 'error')
  }
}
```

## 响应格式

所有 API 调用都返回统一的响应格式：

```javascript
{
  success: boolean,     // 请求是否成功
  data: any,           // 响应数据（成功时）
  error: string,       // 错误信息（失败时）
  status: number,      // HTTP 状态码
  headers: Headers     // 响应头
}
```

## 在 Vue 组件中使用

### 完整示例

```vue
<template>
  <div>
    <button @click="login" :disabled="isLoading">
      {{ isLoading ? '登录中...' : '登录' }}
    </button>
    
    <div v-if="user">
      欢迎，{{ user.nickname }}！
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api'

const isLoading = ref(false)
const user = ref(null)

async function login() {
  isLoading.value = true
  
  try {
    // 开始二维码登录
    const qrResult = await api.auth.startQRLogin()
    
    if (qrResult.success) {
      console.log('二维码:', qrResult.data.data.qr_img)
      
      // 轮询检查登录状态
      const checkLogin = async () => {
        const checkResult = await api.auth.checkQRLogin(qrResult.data.data.qr_key)
        
        if (checkResult.success && checkResult.data.data.status === 'success') {
          // 登录成功，获取用户信息
          const userResult = await api.user.getCurrentUser()
          if (userResult.success) {
            user.value = userResult.data.data.account
          }
        }
      }
      
      // 每2秒检查一次
      const timer = setInterval(checkLogin, 2000)
      
      // 30秒后停止检查
      setTimeout(() => clearInterval(timer), 30000)
    }
  } catch (error) {
    console.error('登录失败:', error)
  } finally {
    isLoading.value = false
  }
}
</script>
```

## 环境配置

### 开发环境 (.env.development)
```
VITE_API_BASE_URL=http://localhost:8000
```

### 生产环境 (.env.production)
```
VITE_API_BASE_URL=https://your-api-domain.com
```

## 扩展 API

### 1. 添加新的端点

在 `config.js` 中添加新的端点：

```javascript
export const API_ENDPOINTS = {
  // 现有端点...
  
  // 新增端点
  DOWNLOAD: {
    START: '/ncm/download/start',
    STATUS: '/ncm/download/status',
    CANCEL: '/ncm/download/cancel'
  }
}
```

### 2. 创建新的服务

创建 `services/downloadService.js`：

```javascript
import { http } from '../request.js'
import { API_ENDPOINTS } from '../config.js'

export class DownloadService {
  static async startDownload(songIds) {
    return http.post(API_ENDPOINTS.DOWNLOAD.START, { song_ids: songIds })
  }
  
  static async getDownloadStatus(taskId) {
    return http.get(API_ENDPOINTS.DOWNLOAD.STATUS, { task_id: taskId })
  }
  
  static async cancelDownload(taskId) {
    return http.post(API_ENDPOINTS.DOWNLOAD.CANCEL, { task_id: taskId })
  }
}
```

### 3. 更新统一入口

在 `index.js` 中导出新服务：

```javascript
export { DownloadService } from './services/downloadService.js'

export const api = {
  // 现有服务...
  
  download: {
    start: (songIds) => DownloadService.startDownload(songIds),
    getStatus: (taskId) => DownloadService.getDownloadStatus(taskId),
    cancel: (taskId) => DownloadService.cancelDownload(taskId)
  }
}
```

## 最佳实践

### 1. 错误处理

```javascript
async function handleApiCall() {
  try {
    const result = await api.user.getCurrentUser()
    
    if (result.success) {
      // 处理成功响应
      return result.data
    } else {
      // 处理业务错误
      throw new Error(result.error)
    }
  } catch (error) {
    // 处理网络错误或其他异常
    console.error('API 调用失败:', error)
    showErrorMessage('操作失败，请稍后重试')
  }
}
```

### 2. 加载状态管理

```javascript
const { isLoading, execute } = useAsyncOperation()

async function loadData() {
  await execute(async () => {
    const result = await api.user.getCurrentUser()
    if (result.success) {
      userData.value = result.data
    }
  })
}
```

### 3. 缓存策略

```javascript
// 简单的内存缓存
const cache = new Map()

async function getCachedUserInfo(userId) {
  const cacheKey = `user_${userId}`
  
  if (cache.has(cacheKey)) {
    return cache.get(cacheKey)
  }
  
  const result = await api.user.getUserInfo(userId)
  if (result.success) {
    cache.set(cacheKey, result.data)
    return result.data
  }
}
```

## 调试和监控

### 1. 请求日志

HTTP 客户端会自动记录请求错误，你可以在浏览器控制台查看。

### 2. 网络面板

在浏览器开发者工具的 Network 面板中可以查看所有 API 请求的详细信息。

### 3. 自定义拦截器

如需添加请求/响应拦截器，可以修改 `request.js` 文件：

```javascript
// 在 request 方法中添加拦截逻辑
async request(url, options = {}) {
  // 请求前拦截
  console.log('发送请求:', url, options)
  
  const result = await fetch(fullUrl, config)
  
  // 响应后拦截
  console.log('收到响应:', result)
  
  return result
}
```

## 故障排除

### 常见问题

#### 1. "UserService is not defined" 错误

**问题**: 在组件中使用 API 时出现 `ReferenceError: UserService is not defined`

**解决方案**:
```javascript
// ❌ 错误的导入方式
import { api } from '@/api'

// ✅ 正确的导入方式
import { AuthService, UserService, MusicService } from '@/api'

// 或者使用默认导出
import api from '@/api'
```

#### 2. 模块循环依赖问题

**问题**: 模块加载时出现循环依赖错误

**解决方案**: 确保导入顺序正确，避免在模块顶层直接引用其他模块的导出

```javascript
// ❌ 可能导致循环依赖
export const api = {
  user: {
    getCurrentUser: () => UserService.getCurrentUser() // 直接引用
  }
}

// ✅ 正确的方式
import { UserService } from './services/userService.js'

export const api = {
  user: {
    getCurrentUser: () => UserService.getCurrentUser() // 在函数内引用
  }
}
```

#### 3. 环境变量未生效

**问题**: API 请求发送到错误的地址

**解决方案**: 检查环境变量配置
```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000

# .env.production  
VITE_API_BASE_URL=https://your-production-api.com
```

#### 4. 请求超时

**问题**: API 请求经常超时

**解决方案**: 调整超时配置
```javascript
// 在 config.js 中修改
export const API_CONFIG = {
  TIMEOUT: 30000, // 增加到30秒
  // ...
}
```

### 调试技巧

#### 1. 启用详细日志

在 `request.js` 中添加调试日志：

```javascript
async request(url, options = {}) {
  console.log('🚀 发送请求:', url, options)
  
  const result = await fetch(fullUrl, config)
  
  console.log('📥 收到响应:', result.status, result.data)
  
  return result
}
```

#### 2. 检查网络请求

在浏览器开发者工具的 Network 面板中查看：
- 请求 URL 是否正确
- 请求头是否包含正确的 Content-Type
- 响应状态码和内容

#### 3. 验证 API 端点

使用 Postman 或 curl 直接测试后端 API：

```bash
# 测试用户信息接口
curl -X GET http://localhost:8000/service/user/current

# 测试二维码登录
curl -X POST http://localhost:8000/service/auth/qr/start
```

这个 API 管理系统提供了完整的解决方案，让你的前端代码更加清晰、可维护和可扩展。