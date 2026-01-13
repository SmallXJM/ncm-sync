<template>
    <header class="app-header">
        <div class="app-header__inner">
            <div class="app-header__left">
                <button class="sidebar-toggle" @click="toggleSidebar" :title="isNarrow ? '展开侧边栏' : '收起侧边栏'"
                    :aria-label="isNarrow ? '展开侧边栏' : '收起侧边栏'" aria-controls="app-sidebar" :aria-expanded="!isNarrow">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="9" y1="3" x2="9" y2="21"></line>
                    </svg>
                </button>
                <slot name="left">
                    <span class="app-header__title">{{ title }}</span>
                </slot>
            </div>

            <div class="app-header__right">
                <!-- <slot name="right">
                    <button class="header-btn">设置</button>
                    <button class="header-btn">退出</button>
                </slot> -->
            </div>
        </div>
    </header>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useSidebar } from '@/composables/useSidebar'

const route = useRoute()

const title = computed(() => {
    return route.meta.title ?? 'ncm-sync'
})

const { isNarrow, isMobileOpen } = useSidebar()

const mq = window.matchMedia('(max-width: 768px)')
const isMobile = ref(mq.matches)

function handleMqChange(e: MediaQueryListEvent) {
    isMobile.value = e.matches
}

onMounted(() => {
    mq.addEventListener('change', handleMqChange)
})

onUnmounted(() => {
    mq.removeEventListener('change', handleMqChange)
})

const toggleSidebar = () => {
    if (isMobile.value) {
        isMobileOpen.value = !isMobileOpen.value
    } else {
        isNarrow.value = !isNarrow.value
    }
}
</script>


<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.app-header {
    position: relative;
    /* Changed from sticky to relative since outer container is fixed */
    /* top: 0; */
    // z-index: 144;
    height: 50px;
    background: var(--bg-base);
    /* Use base color */
    /* border-bottom: 1px solid $border; */
    backdrop-filter: blur(20px);
    transition: background-color 0.3s ease, border-color 0.3s ease;
}

.app-header__inner {
    // max-width: 1200px;
    height: 100%;
    margin: 0 auto;
    padding: 0 $space-md;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.app-header__title {
    font-size: 1.1rem;
    font-weight: 600;
    color: $text-strong;
    transition: color 0.3s ease;
}

.app-header__left {
    display: flex;
    align-items: center;
    gap: 12px; // 控制 sidebar-toggle 和 title 的间距
}

.header-btn {
    background: transparent;
    border: none;
    font-size: 0.9rem;
    padding: $space-xs $space-sm;
    cursor: pointer;
    color: $text-strong;
    border-radius: $radius-sm;
    transition: all 0.2s ease;

    &:hover {
        background: rgba($primary, 0.08);
        color: $primary;
    }
}

.sidebar-toggle {
    width: 36px;
    height: 36px;
    border-radius: $radius-lg;
    border: 1px solid var(--border-color);
    background: transparent;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all $ts-quick,  border-color 0.3s ease;

    &:hover {
        background: var(--bg-surface-hover);
        color: var(--text-primary);
        border-color: var(--text-secondary);
    }

    &:active {
        transform: scale(0.95);
    }
}
</style>
