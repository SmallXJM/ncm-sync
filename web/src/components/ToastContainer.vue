<template>
  <div class="toast-container">
    <TransitionGroup name="toast-list">
      <Toast
        v-for="item in toasts"
        :key="item.id"
        :message="item.message"
        :type="item.type"
        @close="remove(item.id)"
      />
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Toast from './Toast.vue'; // 确保路径正确

interface ToastItem {
  id: number;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

const toasts = ref<ToastItem[]>([]);
let count = 0;

// 增加一条消息
const add = (message: string, type: ToastItem['type'] = 'info', duration = 3000) => {
  const id = count++;
  toasts.value.push({ id, message, type });
  
  if (duration > 0) {
    setTimeout(() => remove(id), duration);
  }
};

// 移除一条消息
const remove = (id: number) => {
  toasts.value = toasts.value.filter(t => t.id !== id);
};

// 关键：必须暴露给外部，utils/toast.ts 才能调用到 add 方法
defineExpose({ add });
</script>

<style scoped lang="scss">
.toast-container {
  position: fixed;
  top: var(--spacing-xl);
  right: var(--spacing-xl);
  z-index: 2000;
  display: flex;
  flex-direction: column; // 垂直堆叠
  gap: var(--spacing-sm); // 消息之间的间距
  pointer-events: none; // 防止容器遮挡点击，内部元素再开启
}

/* TransitionGroup 动画 */
.toast-list-enter-active,
.toast-list-leave-active {
  transition: all 0.3s ease;
}

.toast-list-enter-from {
  opacity: 0;
  transform: translateX(30px); // 从右侧滑入
}

.toast-list-leave-to {
  opacity: 0;
  transform: scale(0.9); // 消失时轻微缩小
}

/* 确保列表中其他元素平滑移动 */
.toast-list-move {
  transition: transform 0.3s ease;
}
</style>