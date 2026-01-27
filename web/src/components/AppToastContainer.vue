<template>
  <div
    ref="containerRef"
    class="toast-container"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @click="handleClick"
    :style="{ '--container-padding-bottom': isHovered ? '20px' : '40px' }"
  >
    <TransitionGroup name="toast-list">

        <Toast
                v-for="(item, index) in displayToasts"
        :key="item.id"
        class="toast-layer"
        :ref="(el) => setItemRef(el, item.id)"
        :style="getLayerStyle(index)"
        :title="item.title"
          :message="item.message"
          :type="item.type"
          :icon="item.icon"
          @close="remove(item.id)"
        />
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onBeforeUnmount, onMounted, watch, type CSSProperties, type ComponentPublicInstance, type Component } from 'vue';
import Toast from './AppToast.vue';

interface ToastItem {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  icon?: Component;
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
  const htmlEl = el ? ((el instanceof HTMLElement) ? el : (el as ComponentPublicInstance).$el) : null;

  const existingEl = itemRefs.get(id);

  if (htmlEl instanceof HTMLElement) {
    if (existingEl !== htmlEl) {
      if (existingEl) {
        resizeObserver.unobserve(existingEl);
      }
      htmlEl.setAttribute('data-toast-id', id.toString());
      itemRefs.set(id, htmlEl);
      resizeObserver.observe(htmlEl);
    }
  } else {
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

const handleClick = () => {
  if (!isHovered.value) {
    handleMouseEnter();
  }
};

const containerRef = ref<HTMLElement | null>(null);

// 监听展开状态，动态绑定全局点击事件
const handleOutsideAction = (e: Event) => {
  // 判断点击或触摸的目标是否在容器外
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    isHovered.value = false;
  }
};

watch(isHovered, (newVal) => {
  if (newVal) {
    // 同时也监听 touchstart 和 scroll，确保拖动别处也能收回
    setTimeout(() => {
      document.addEventListener('click', handleOutsideAction);
      document.addEventListener('touchstart', handleOutsideAction);
      window.addEventListener('scroll', () => (isHovered.value = false), { once: true });
    }, 0);
  } else {
    document.removeEventListener('click', handleOutsideAction);
    document.removeEventListener('touchstart', handleOutsideAction);
    // 注意：scroll 使用 once: true 会自动移除
  }
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideAction);
  resizeObserver.disconnect();
});


const handleMouseEnter = () => {
  // 如果是触摸事件，防止触发浏览器的默认长按行为（可选）
  // if (e?.type === 'touchstart') { ... }
  if (toasts.value.length > 1) {
    isHovered.value = true;
  }
};

const handleMouseLeave = () => {
// 增加一点延迟，防止手指快速点击造成的频繁闪烁
  setTimeout(() => {
    isHovered.value = false;
  }, 100);
};

const DURATION_MS = 400;
const EASING = 'cubic-bezier(0.4, 0, 0.2, 1)';
const GAP = 6;
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
      transition: `all 0.3s ease, transform ${DURATION_MS}ms ${EASING}, opacity ${DURATION_MS}ms ${EASING}`,
      pointerEvents: 'auto',
    };
  }

  if (index < 3) {
    const scale = COLLAPSED_SCALES[index] ?? 1;
    const gap = 8;
    const topItem = displayToasts.value[0];
    const currentItem = displayToasts.value[index];
    
    // 默认高度 60，避免未获取高度时计算错误
    const h0 = topItem ? (itemHeights[topItem.id] ?? 60) : 60;
    const hi = currentItem ? (itemHeights[currentItem.id] ?? 60) : 60;
    
    // 动态计算偏移量：保证底部堆叠间距一致
    // Offset_i = H_0 - H_i * S_i + i * gap
    const offsetY = h0 - hi * scale + index * gap;

    return {
      position: 'absolute',
      left: '50%',
      zIndex,
      // opacity: 1,
      transform: `${topAlign} translateY(${offsetY}px) scale(${scale})`,
      transition: `all 0.3s ease, transform ${DURATION_MS}ms ${EASING}, opacity ${DURATION_MS}ms ${EASING}`,
      pointerEvents: index === 0 ? 'auto' : 'none',
    };
  }

  // 计算第3个位置（index=2）的偏移量作为隐藏元素的基准
  const scale2 = COLLAPSED_SCALES[2] ?? 0.89;
  const gap = 8;
  const topItem = displayToasts.value[0];
  const item2 = displayToasts.value[2];
  const h0 = topItem ? (itemHeights[topItem.id] ?? 60) : 60;
  const h2 = item2 ? (itemHeights[item2.id] ?? 60) : 60;
  const offset2 = h0 - h2 * scale2 + 2 * gap;

  const hiddenOffset = offset2 + 2;
  return {
    position: 'absolute',
    left: '50%',
    zIndex,
    opacity: 0,
    transform: `${topAlign} translateY(${hiddenOffset}px) scale(0.9)`,
    transition: `all 0.3s ease, transform ${DURATION_MS}ms ${EASING}, opacity ${DURATION_MS}ms ${EASING}`,
    pointerEvents: 'none',
  };
};

const add = (title: string, message = '', type: ToastItem['type'] = 'info', duration = 3000, icon?: Component) => {
  const id = count++;
  toasts.value.push({ id, title, message, type, icon });

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
  //左对齐
  
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
