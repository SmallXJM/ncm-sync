<template>
  <div class="app-loading" role="status" aria-live="polite" :class="customClass">
    <div class="dots-container">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>
    <p v-if="message" class="loading-message">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
/**
 * AppLoading Component
 * 
 * A reusable loading indicator with three animated dots.
 * Displays a loading animation and an optional message.
 * 
 * Usage:
 * <AppLoading message="Loading data..." />
 */
withDefaults(defineProps<{
  /** The message to display below the spinner. Default: '正在加载' */
  message?: string
  /** Custom CSS class for the container */
  customClass?: string
}>(), {
  message: '正在加载'
})
</script>

<style scoped>
.app-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  width: 100%;
  min-height: 200px;
  height: 100%;
}

.dots-container {
  display: flex;
  gap: 8px;
  margin-bottom: 1rem;
}

.dot {
  width: 16px;
  height: 16px;
  background-color: var(--control-active-bg);
  border-radius: 50%;
  animation: wave 2s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

.dot:nth-child(3) {
  animation-delay: 0s;
}

@keyframes wave {
  0%, 60%, 100% {
    opacity: 0.2;
    transform: scale(0.92);
  }
  30% {
    opacity: 1;
    transform: scale(1);
  }
}

.loading-message {
  color: var(--text-secondary);
  font-size: 1.5rem;
  margin: 0;
  animation: wave-message 2s infinite ease-in-out both;

}

@keyframes wave-message {
  0%, 50%, 100% {
    opacity: 0.2;
  }
  30% {
    opacity: 1;
  }
}


</style>
