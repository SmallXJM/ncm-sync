<template>
  <div class="toast" :class="type">
    <div class="toast-icon">
      <component v-if="icon" :is="icon" />
      <template v-else>
        <svg v-if="type === 'success'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
        <svg v-else-if="type === 'error'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
        <svg v-else-if="type === 'warning'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
      </template>
    </div>

    <div class="toast-content">
      <span class="title">{{ title }}</span>
      <span class="message">{{ message }}</span>
    </div>

    <button class="toast-close" @click="$emit('close')">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
defineProps<{
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  icon?: Component;
}>();

defineEmits(['close']);
</script>

<style scoped lang="scss">
.toast {
  box-sizing: border-box;
  pointer-events: auto;
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  
  width: max-content; /* 避免在绝对定位父容器下 100% 造成计算异常 */
  min-width: 300px;
  max-width: 450px;
  padding: 12px;
  
  border-radius: 12px;
  background: var(--bg-surface);
  box-shadow: 
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
    
  color: var(--text-primary);
  margin-bottom: 0;
  
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);

  /* 避免 border 被背景覆盖 */
  background-clip: padding-box;
  
  transition: all 0.3s ease;
}

.toast-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  svg {
    width: 24px;
    height: 24px;
  }
}

.toast-content {
  flex: 1;
  display: flex;
  align-items: flex-start;
  flex-direction: column;
}

.title {
  font-weight: 700;
  font-size: 0.95rem;
  line-height: 1.2;
}

.message {
  font-weight: 500;
  font-size: 0.95rem;
  line-height: 1.2;
}

.toast-close {
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: var(--text-secondary);
  border-radius: 50%;
  transition: all 0.2s ease;
  flex-shrink: 0;
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.05);
    color: var(--text-primary);
  }
}

// Variants with Gradients
// border会造成左边一条竖白线，原因不明
.toast.success {
  background: linear-gradient(to right, rgba(16, 185, 129, 0.1), var(--bg-surface) 50%);
  // border: 1px solid rgba(16, 185, 129, 0.1);
  .toast-icon { color: #10b981; }
}

.toast.error {
  background: linear-gradient(to right, rgba(239, 68, 68, 0.1), var(--bg-surface) 50%);
  // border: 1px solid rgba(239, 68, 68, 0.1);
  .toast-icon { color: #ef4444; }
}

.toast.warning {
  background: linear-gradient(to right, rgba(245, 158, 11, 0.1), var(--bg-surface) 50%);
  // border: 1px solid rgba(245, 158, 11, 0.1);
  .toast-icon { color: #f59e0b; }
}

.toast.info {
  background: linear-gradient(to right, rgba(59, 130, 246, 0.1), var(--bg-surface) 50%);
  // border: 1px solid rgba(59, 130, 246, 0.1);
  .toast-icon { color: #3b82f6; }
}
</style>
