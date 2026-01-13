<template>
  <div class="toast" :class="type">
    <div class="toast-content">
      <span class="message">{{ message }}</span>
      <button class="toast-close" @click="$emit('close')">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}>();

defineEmits(['close']);
</script>

<style scoped lang="scss">
.toast {
  pointer-events: auto; // 恢复点击
  position: relative; // 移除之前的 fixed 定位
  top: auto;
  right: auto;
  z-index: 2000;
  max-width: 400px;
  padding: var(--spacing-md);
  border-radius: 0.75rem;
  background: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 0;
}

.toast.info {
    // 信息 toast 背景与边框颜色一致
  border-left: 4px solid var(--border-color);
}

.toast.success {
  border-left: 4px solid var(--color-success);
}

.toast.error {
  border-left: 4px solid var(--color-error);
}

.toast.warning {
  border-left: 4px solid var(--color-warning);
}

.toast-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-md);
  font-weight: 500;
}

.toast-close {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: var(--text-secondary);
  opacity: 0.7;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: 0.2s ease;
}

.toast-close:hover {
  opacity: 1;
  color: var(--text-primary);
}

.message { font-weight: 500; font-size: 0.9rem; }


</style>