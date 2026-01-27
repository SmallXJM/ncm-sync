<template>
  <div
    class="toast-container"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    :style="{ '--container-padding-bottom': isHovered ? '20px' : '40px' }"
  >
    <TransitionGroup name="toast-list">

        <Toast
                v-for="(item, index) in displayToasts"
        :key="item.id"
        class="toast-layer"
        :ref="(el) => setItemRef(el, item.id)"
        :style="getLayerStyle(index)"
          :message="item.message"
          :type="item.type"
          @close="remove(item.id)"
        />
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onBeforeUnmount, type CSSProperties, type ComponentPublicInstance } from 'vue';
import Toast from './AppToast.vue';

interface ToastItem {
  id: number;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

const toasts = ref<ToastItem[]>([]);
let count = 0;
const isHovered = ref(false);
const itemHeights = reactive<Record<number, number>>({});
const itemRefs = new Map<number, HTMLElement>();

const resizeObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    const id = Number(entry.target.getAttribute('data-toast-id'));
    if (!isNaN(id)) {
      itemHeights[id] = entry.borderBoxSize?.[0]?.blockSize ?? entry.contentRect.height;
    }
  }
});

const setItemRef = (el: Element | ComponentPublicInstance | null, id: number) => {
  if (el instanceof HTMLElement) {
    el.setAttribute('data-toast-id', id.toString());
    itemRefs.set(id, el);
    resizeObserver.observe(el);
  } else {
    const existingEl = itemRefs.get(id);
    if (existingEl) {
      resizeObserver.unobserve(existingEl);
      itemRefs.delete(id);
      delete itemHeights[id];
    }
  }
};

onBeforeUnmount(() => {
  resizeObserver.disconnect();
});

const displayToasts = computed(() => {
  return [...toasts.value].reverse();
});

const handleMouseEnter = () => {
  if (toasts.value.length > 1) {
    isHovered.value = true;
  }
};

const handleMouseLeave = () => {
  isHovered.value = false;
};

const DURATION_MS = 400;
const EASING = 'cubic-bezier(0.4, 0, 0.2, 1)';
const GAP = 3;
const COLLAPSED_OFFSETS = [0, 8, 16];
const COLLAPSED_SCALES = [1, 0.94, 0.89];

const getExpandedOffset = (idx: number) => {
  let y = 0;
  for (let i = 0; i < idx; i++) {
    const pid = displayToasts.value[i]?.id;
    if (pid === undefined) continue;
    y += (itemHeights[pid] ?? 60) + GAP;
  }
  return y;
};

const getLayerStyle = (index: number): CSSProperties => {
  const zIndex = 100 - index;
  const topAlign = 'translateX(-50%)';

  if (isHovered.value) {
    const offsetY = getExpandedOffset(index);
    return {
      position: 'absolute',
      left: '50%',
      zIndex,
      // opacity: 1,
      transform: `${topAlign} translateY(${offsetY}px) scale(1)`,
      transition: `transform ${DURATION_MS}ms ${EASING}, opacity ${DURATION_MS}ms ${EASING}`,
      pointerEvents: 'auto',
    };
  }

  if (index < 3) {
    const offsetY = COLLAPSED_OFFSETS[index];
    const scale = COLLAPSED_SCALES[index];
    return {
      position: 'absolute',
      left: '50%',
      zIndex,
      // opacity: 1,
      transform: `${topAlign} translateY(${offsetY}px) scale(${scale})`,
      transition: `transform ${DURATION_MS}ms ${EASING}, opacity ${DURATION_MS}ms ${EASING}`,
      pointerEvents: index === 0 ? 'auto' : 'none',
    };
  }

  const hiddenOffset = (COLLAPSED_OFFSETS[2] ?? 24) + 2;
  return {
    position: 'absolute',
    left: '50%',
    zIndex,
    opacity: 0,
    transform: `${topAlign} translateY(${hiddenOffset}px) scale(0.9)`,
    transition: `transform ${DURATION_MS}ms ${EASING}, opacity ${DURATION_MS}ms ${EASING}`,
    pointerEvents: 'none',
  };
};

const add = (message: string, type: ToastItem['type'] = 'info', duration = 300000) => {
  const id = count++;
  toasts.value.push({ id, message, type });

  if (duration > 0) {
    setTimeout(() => remove(id), duration);
  }
};

const remove = (id: number) => {
  toasts.value = toasts.value.filter(t => t.id !== id);
};

defineExpose({ add });
</script>

<style scoped lang="scss">
.toast-container {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  width: max-content;
  pointer-events: auto;
  padding-bottom: var(--container-padding-bottom);
  transition: padding-bottom 0.3s ease;
}

.toast-layer {
  position: absolute;
  left: 50%;
  /* 移除 width: max-content，改为由 Toast 内部定义的 min-width 撑开 */
  transform-origin: top center;
  backface-visibility: hidden;
  will-change: transform, opacity;
  
  /* 确保圆角和滤镜不被父级裁剪 */
  overflow: visible; 

  // 关键：通过 margin 和 padding 的组合，让感应区连成一片
  // 假设 GAP 是 10px，我们给上下各加 5px 的透明边框或内边距
  &::before {
    content: '';
    position: absolute;
    inset: -10px 0; // 向上向下各延伸 5px，填满 10px 的 GAP
    z-index: -1;
  }
}

.toast-list-enter-active,
.toast-list-leave-active {
  transition: transform 400ms cubic-bezier(0.4, 0, 0.2, 1), opacity 400ms cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-list-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-80px) scale(0.9) !important;
}

.toast-list-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px) scale(0.9) !important;
  pointer-events: none;
}

.toast-list-leave-active {
  position: absolute;
  left: 50%;
  transform-origin: top center;
}
</style>
