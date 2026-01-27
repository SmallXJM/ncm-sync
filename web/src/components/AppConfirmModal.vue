<template>
  <Transition name="modal">
    <div v-if="isOpen" class="modal-overlay" @click.self="handleClose">
      <div class="modal-content" :style="{ maxWidth: maxWidth }">
        <div class="modal-body">
          <div class="modal-header">
            <div class="header-content">
              <h3>{{ title }}</h3>
            </div>
            <button class="close-btn" @click="handleClose">×</button>
          </div>

          <div class="modal-content-text">
            <slot>
              <p class="message" v-html="message"></p>
            </slot>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="handleClose" :disabled="loading">
            {{ cancelText }}
          </button>
          <button 
            class="btn" 
            :class="confirmButtonClass" 
            @click="handleConfirm" 
            :disabled="loading"
          >
            {{ loading ? loadingText : confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  title: {
    type: String,
    default: '提示'
  },
  message: {
    type: String,
    default: ''
  },
  confirmText: {
    type: String,
    default: '确定'
  },
  cancelText: {
    type: String,
    default: '取消'
  },
  loading: {
    type: Boolean,
    default: false
  },
  loadingText: {
    type: String,
    default: '处理中...'
  },
  variant: {
    type: String as () => 'primary' | 'danger',
    default: 'primary'
  },
  maxWidth: {
    type: String,
    default: '500px'
  }
})

const emit = defineEmits(['update:isOpen', 'close', 'confirm'])

const confirmButtonClass = computed(() => {
  return props.variant === 'danger' ? 'btn-danger' : 'btn-primary'
})

function handleClose() {
  if (props.loading) return
  emit('update:isOpen', false)
  emit('close')
}

function handleConfirm() {
  emit('confirm')
}
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md);
}

.modal-content {
  width: 90dvw; // Default mobile width
  max-height: 90vh;
  background: var(--bg-modal);
  border-radius: 12px;
  box-shadow: var(--shadow-2xl);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.5s cubic-bezier(0.25, 1, 0.5, 1);

  @media (min-width: 769px) {
    width: 100%; // Will be constrained by maxWidth style binding
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;

  .header-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  h3 {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
    line-height: 1.2;
  }
}

.close-btn {
  font-size: 1.5rem;
  line-height: 1;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 4px;
  margin-top: -4px;
  transition: color 0.2s;

  &:hover {
    color: var(--text-primary);
  }
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem; // Match SubscriptionView padding
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.modal-content-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  white-space: pre-wrap;
  line-height: 1.5;
}

.modal-footer {
  padding: var(--spacing-lg);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
}

/* Transition Animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;

  .modal-content {
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .modal-content {
    transform: scale(0.95) translateY(10px);
  }
}
</style>