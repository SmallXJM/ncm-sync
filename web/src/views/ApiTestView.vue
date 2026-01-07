<template>
  <div class="page">
    <div class="page-header">
      <div class="container">
        <h1 class="page-title">API 测试</h1>
        <p class="page-subtitle">测试和调试 NCM API 接口</p>
      </div>
    </div>

    <div class="container">
      <!-- API Categories -->
      <section class="mb-xl">
        <div class="glass-card">
          <h2 class="section-title">API 分类</h2>
          <div class="categories-grid">
            <div
              v-for="category in apiCategories"
              :key="category.id"
              class="category-card"
              :class="{ active: selectedCategory === category.id }"
              @click="selectCategory(category.id)"
            >
              <div class="category-icon">{{ category.icon }}</div>
              <h3>{{ category.name }}</h3>
              <p>{{ category.description }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- API List -->
      <section class="mb-xl" v-if="selectedCategory">
        <div class="glass-card">
          <h2 class="section-title">{{ getCurrentCategory()?.name }} API</h2>
          <div class="api-list">
            <div
              v-for="api in getCurrentApis()"
              :key="api.path"
              class="api-item"
              @click="selectApi(api)"
            >
              <div class="api-method" :class="api.method.toLowerCase()">
                {{ api.method }}
              </div>
              <div class="api-info">
                <h4>{{ api.name }}</h4>
                <p class="api-path">{{ api.path }}</p>
                <p class="api-desc">{{ api.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- API Test Panel -->
      <section class="mb-xl" v-if="selectedApi">
        <div class="glass-card">
          <div class="panel-header">
            <h2 class="section-title">测试 {{ selectedApi.name }}</h2>
            <button class="btn btn-primary" @click="executeApi" :disabled="isExecuting">
              <div v-if="isExecuting" class="loading-spinner"></div>
              <span v-else>🚀 执行</span>
            </button>
          </div>

          <!-- Parameters -->
          <div class="parameters-section" v-if="selectedApi.parameters?.length">
            <h3>参数</h3>
            <div class="parameters-grid">
              <div
                v-for="param in selectedApi.parameters"
                :key="param.name"
                class="parameter-item"
              >
                <label class="param-label">
                  {{ param.name }}
                  <span v-if="param.required" class="required">*</span>
                </label>
                <input
                  v-model="paramValues[param.name]"
                  :type="param.type === 'number' ? 'number' : 'text'"
                  :placeholder="param.placeholder || param.description"
                  class="param-input"
                />
                <p class="param-desc">{{ param.description }}</p>
              </div>
            </div>
          </div>

          <!-- Request Body -->
          <div class="request-section">
            <h3>请求体 (JSON)</h3>
            <textarea
              v-model="requestBody"
              class="request-textarea"
              placeholder="输入 JSON 格式的请求体..."
              rows="6"
            ></textarea>
          </div>

          <!-- Response -->
          <div class="response-section" v-if="apiResponse">
            <h3>响应结果</h3>
            <div class="response-header">
              <span class="status-code" :class="getStatusClass(apiResponse.status)">
                {{ apiResponse.status }}
              </span>
              <span class="response-time">{{ responseTime }}ms</span>
            </div>
            <pre class="response-body">{{ formatJson(apiResponse.data) }}</pre>
          </div>
        </div>
      </section>
    </div>

    <!-- Toast Notifications -->
    <div v-if="toast.show" class="toast" :class="toast.type">
      <div class="toast-content">
        <span>{{ toast.message }}</span>
        <button class="toast-close" @click="hideToast">×</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const selectedCategory = ref('')
const selectedApi = ref(null)
const paramValues = reactive({})
const requestBody = ref('')
const apiResponse = ref(null)
const responseTime = ref(0)
const isExecuting = ref(false)

// Toast notification
const toast = reactive({
  show: false,
  message: '',
  type: 'info'
})

// API Categories
const apiCategories = [
  {
    id: 'auth',
    name: '认证相关',
    icon: '🔐',
    description: '登录、注册、会话管理'
  },
  {
    id: 'user',
    name: '用户管理',
    icon: '👤',
    description: '用户信息、账号管理'
  },
  {
    id: 'music',
    name: '音乐搜索',
    icon: '🎵',
    description: '搜索、歌单、下载'
  },
  {
    id: 'modules',
    name: '基础模块',
    icon: '🔧',
    description: '原始 API 模块'
  }
]

// API Definitions
const apiDefinitions = {
  auth: [
    {
      name: '二维码登录 - 生成',
      path: '/ncm/auth/qr/start',
      method: 'POST',
      description: '生成登录二维码',
      parameters: []
    },
    {
      name: '二维码登录 - 检查',
      path: '/ncm/auth/qr/check',
      method: 'POST',
      description: '检查二维码登录状态',
      parameters: [
        { name: 'qr_key', type: 'string', required: true, description: '二维码密钥' }
      ]
    },
    {
      name: 'Cookie 登录',
      path: '/ncm/auth/cookie/login',
      method: 'POST',
      description: '使用 Cookie 登录',
      parameters: [
        { name: 'cookie', type: 'string', required: true, description: 'Cookie 字符串' }
      ]
    },
    {
      name: '登录状态检查',
      path: '/ncm/auth/status',
      method: 'POST',
      description: '检查当前登录状态',
      parameters: []
    }
  ],
  user: [
    {
      name: '获取当前用户',
      path: '/ncm/user/current',
      method: 'GET',
      description: '获取当前登录用户信息',
      parameters: []
    },
    {
      name: '用户列表',
      path: '/ncm/user/list',
      method: 'GET',
      description: '获取所有用户列表',
      parameters: [
        { name: 'limit', type: 'number', required: false, description: '限制数量', placeholder: '100' },
        { name: 'offset', type: 'number', required: false, description: '偏移量', placeholder: '0' }
      ]
    },
    {
      name: '切换会话',
      path: '/ncm/user/switch',
      method: 'POST',
      description: '切换到指定会话',
      parameters: [
        { name: 'session_id', type: 'string', required: true, description: '会话 ID' }
      ]
    },
    {
      name: '会话列表',
      path: '/ncm/user/sessions/list',
      method: 'GET',
      description: '获取所有会话列表',
      parameters: []
    }
  ],
  music: [
    {
      name: '增强搜索',
      path: '/ncm/music/search/enhanced',
      method: 'POST',
      description: '增强音乐搜索功能',
      parameters: [
        { name: 'keywords', type: 'string', required: true, description: '搜索关键词' },
        { name: 'search_type', type: 'string', required: false, description: '搜索类型', placeholder: 'song' },
        { name: 'limit', type: 'number', required: false, description: '结果数量', placeholder: '30' },
        { name: 'include_details', type: 'boolean', required: false, description: '包含详细信息' }
      ]
    },
    {
      name: '歌单分析',
      path: '/ncm/music/playlist/analyze',
      method: 'POST',
      description: '分析歌单信息',
      parameters: [
        { name: 'playlist_id', type: 'string', required: true, description: '歌单 ID' },
        { name: 'include_song_details', type: 'boolean', required: false, description: '包含歌曲详情' }
      ]
    },
    {
      name: '准备下载',
      path: '/ncm/music/download/prepare',
      method: 'POST',
      description: '准备批量下载',
      parameters: [
        { name: 'song_ids', type: 'array', required: true, description: '歌曲 ID 列表' },
        { name: 'quality', type: 'string', required: false, description: '音质', placeholder: 'standard' }
      ]
    }
  ],
  modules: [
    {
      name: '匿名注册',
      path: '/anonimous/register_anonimous',
      method: 'POST',
      description: '匿名用户注册',
      parameters: []
    },
    {
      name: '热门搜索',
      path: '/search/search_hot',
      method: 'GET',
      description: '获取热门搜索词',
      parameters: []
    },
    {
      name: '搜索',
      path: '/search/search',
      method: 'GET',
      description: '基础搜索功能',
      parameters: [
        { name: 'keywords', type: 'string', required: true, description: '搜索关键词' },
        { name: 'type', type: 'string', required: false, description: '搜索类型', placeholder: '1' },
        { name: 'limit', type: 'number', required: false, description: '结果数量', placeholder: '30' }
      ]
    }
  ]
}

const getCurrentCategory = () => {
  return apiCategories.find(cat => cat.id === selectedCategory.value)
}

const getCurrentApis = () => {
  return apiDefinitions[selectedCategory.value] || []
}

function selectCategory(categoryId) {
  selectedCategory.value = categoryId
  selectedApi.value = null
  apiResponse.value = null
}

function selectApi(api) {
  selectedApi.value = api
  apiResponse.value = null

  // Reset parameters
  Object.keys(paramValues).forEach(key => {
    delete paramValues[key]
  })

  // Initialize parameters with default values
  if (api.parameters) {
    api.parameters.forEach(param => {
      paramValues[param.name] = ''
    })
  }

  // Set default request body for POST requests
  if (api.method === 'POST') {
    const bodyObj = {}
    if (api.parameters) {
      api.parameters.forEach(param => {
        if (param.type === 'array') {
          bodyObj[param.name] = []
        } else if (param.type === 'boolean') {
          bodyObj[param.name] = false
        } else if (param.type === 'number') {
          bodyObj[param.name] = 0
        } else {
          bodyObj[param.name] = ''
        }
      })
    }
    requestBody.value = JSON.stringify(bodyObj, null, 2)
  } else {
    requestBody.value = ''
  }
}

async function executeApi() {
  if (!selectedApi.value) return

  isExecuting.value = true
  const startTime = Date.now()

  try {
    let url = `/api${selectedApi.value.path}`
    let options = {
      method: selectedApi.value.method,
      headers: {
        'Content-Type': 'application/json'
      }
    }

    // Handle parameters
    if (selectedApi.value.method === 'GET') {
      // Add query parameters for GET requests
      const params = new URLSearchParams()
      Object.entries(paramValues).forEach(([key, value]) => {
        if (value !== '' && value !== null && value !== undefined) {
          params.append(key, value)
        }
      })
      if (params.toString()) {
        url += '?' + params.toString()
      }
    } else {
      // Use request body for POST requests
      if (requestBody.value.trim()) {
        try {
          const body = JSON.parse(requestBody.value)
          options.body = JSON.stringify(body)
        } catch (e) {
          showToast('请求体 JSON 格式错误', 'error')
          return
        }
      }
    }

    const response = await fetch(url, options)
    const data = await response.json()

    responseTime.value = Date.now() - startTime
    apiResponse.value = {
      status: response.status,
      data: data
    }

    if (response.ok) {
      showToast('API 调用成功', 'success')
    } else {
      showToast('API 调用失败', 'error')
    }

  } catch (error) {
    responseTime.value = Date.now() - startTime
    apiResponse.value = {
      status: 0,
      data: { error: error.message }
    }
    showToast('请求失败: ' + error.message, 'error')
  } finally {
    isExecuting.value = false
  }
}

function getStatusClass(status) {
  if (status >= 200 && status < 300) return 'success'
  if (status >= 400 && status < 500) return 'warning'
  if (status >= 500) return 'error'
  return 'info'
}

function formatJson(obj) {
  return JSON.stringify(obj, null, 2)
}

function showToast(message, type = 'info') {
  toast.message = message
  toast.type = type
  toast.show = true

  setTimeout(() => {
    hideToast()
  }, 3000)
}

function hideToast() {
  toast.show = false
}
</script>

