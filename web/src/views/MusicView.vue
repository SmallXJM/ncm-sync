<template>
  <div class="page">
    <div class="page-header">
      <div class="container">
        <h1 class="page-title">音乐搜索</h1>
        <p class="page-subtitle">搜索和管理网易云音乐资源</p>
      </div>
    </div>
    
    <div class="container">
      <!-- Search Section -->
      <section class="mb-xl">
        <div class="glass-card">
          <div class="search-form">
            <input 
              v-model="searchQuery" 
              type="text" 
              class="search-input"
              placeholder="输入歌曲、歌手或专辑名称..."
              @keyup.enter="performSearch"
            />
            <button 
              class="btn btn-primary"
              @click="performSearch" 
              :disabled="isSearching || !searchQuery.trim()"
            >
              <div v-if="isSearching" class="loading-spinner"></div>
              <span v-else>🔍 搜索</span>
            </button>
          </div>
          
          <div class="search-options">
            <label class="option-label">
              <input type="radio" v-model="searchType" value="song" />
              <span>歌曲</span>
            </label>
            <label class="option-label">
              <input type="radio" v-model="searchType" value="album" />
              <span>专辑</span>
            </label>
            <label class="option-label">
              <input type="radio" v-model="searchType" value="artist" />
              <span>歌手</span>
            </label>
            <label class="option-label">
              <input type="radio" v-model="searchType" value="playlist" />
              <span>歌单</span>
            </label>
          </div>
        </div>
      </section>
      
      <!-- Results Section -->
      <section v-if="searchResults.length > 0" class="mb-xl">
        <div class="glass-card">
          <div class="section-header">
            <h2 class="section-title">搜索结果</h2>
            <span class="result-count">共 {{ searchResults.length }} 条结果</span>
          </div>
          
          <div class="results-list">
            <div 
              v-for="item in searchResults" 
              :key="item.id" 
              class="result-item"
            >
              <div class="item-cover" v-if="getItemCover(item)">
                <img :src="getItemCover(item)" :alt="item.name" @error="handleImageError" />
              </div>
              
              <div class="item-info">
                <h3 class="item-name">{{ item.name }}</h3>
                <p class="item-meta">{{ getItemMeta(item) }}</p>
                <p class="item-extra" v-if="getItemExtra(item)">{{ getItemExtra(item) }}</p>
              </div>
              
              <div class="item-actions">
                <button class="btn btn-sm btn-secondary" @click="viewDetails(item)">
                  详情
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <!-- Empty State -->
      <section v-else-if="hasSearched" class="mb-xl">
        <div class="glass-card">
          <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <h3>未找到结果</h3>
            <p class="text-secondary">请尝试其他关键词</p>
          </div>
        </div>
      </section>
      
      <!-- Initial State -->
      <section v-else class="mb-xl">
        <div class="glass-card">
          <div class="empty-state">
            <div class="empty-icon">🎵</div>
            <h3>开始搜索</h3>
            <p class="text-secondary">输入关键词搜索音乐资源</p>
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
import { ref, reactive } from 'vue'
import api from '@/api'

const searchQuery = ref('')
const searchType = ref('song')
const searchResults = ref([])
const isSearching = ref(false)
const hasSearched = ref(false)

// Toast notification
const toast = reactive({
  show: false,
  message: '',
  type: 'info'
})

async function performSearch() {
  if (!searchQuery.value.trim()) {
    showToast('请输入搜索关键词', 'warning')
    return
  }
  
  isSearching.value = true
  hasSearched.value = true
  
  try {
    const result = await api.music.enhancedSearch({
      keywords: searchQuery.value,
      search_type: searchType.value,
      limit: 30,
      include_details: false
    })
    
    if (result.success && result.data.code === 200) {
      const results = result.data.data.results?.result || {}
      
      switch (searchType.value) {
        case 'song':
          searchResults.value = results.songs || []
          break
        case 'album':
          searchResults.value = results.albums || []
          break
        case 'artist':
          searchResults.value = results.artists || []
          break
        case 'playlist':
          searchResults.value = results.playlists || []
          break
        default:
          searchResults.value = []
      }
      
      if (searchResults.value.length === 0) {
        showToast('未找到相关结果', 'info')
      } else {
        showToast(`找到 ${searchResults.value.length} 条结果`, 'success')
      }
    } else {
      showToast(result.data?.message || '搜索失败', 'error')
      searchResults.value = []
    }
  } catch (error) {
    console.error('Search failed:', error)
    showToast('搜索失败，请检查网络连接', 'error')
    searchResults.value = []
  } finally {
    isSearching.value = false
  }
}

function getItemCover(item) {
  if (searchType.value === 'song') {
    return item.al?.picUrl || item.album?.picUrl
  } else if (searchType.value === 'album') {
    return item.picUrl || item.blurPicUrl
  } else if (searchType.value === 'artist') {
    return item.picUrl || item.img1v1Url
  } else if (searchType.value === 'playlist') {
    return item.coverImgUrl
  }
  return null
}

function getItemMeta(item) {
  if (searchType.value === 'song') {
    const artists = item.ar || item.artists || []
    return artists.map(a => a.name).join(', ')
  } else if (searchType.value === 'album') {
    const artist = item.artist || {}
    return artist.name || '未知艺术家'
  } else if (searchType.value === 'artist') {
    return `${item.albumSize || 0} 张专辑`
  } else if (searchType.value === 'playlist') {
    return `by ${item.creator?.nickname || '未知用户'}`
  }
  return ''
}

function getItemExtra(item) {
  if (searchType.value === 'song') {
    const album = item.al || item.album || {}
    return album.name || ''
  } else if (searchType.value === 'album') {
    return `${item.size || 0} 首歌曲`
  } else if (searchType.value === 'playlist') {
    return `${item.trackCount || 0} 首歌曲 · ${item.playCount || 0} 次播放`
  }
  return ''
}

function viewDetails(item) {
  showToast('详情功能开发中...', 'info')
  console.log('View details:', item)
}

function handleImageError(event) {
  event.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3E🎵%3C/text%3E%3C/svg%3E'
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

