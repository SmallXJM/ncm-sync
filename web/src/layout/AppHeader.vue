<template>
    <header class="app-header">
        <div class="app-header__inner">
            <div class="app-header__left">
                <button class="sidebar-toggle" @click="toggleSidebar" :title="isNarrow ? '展开侧边栏' : '收起侧边栏'"
                    :aria-label="isNarrow ? '展开侧边栏' : '收起侧边栏'" aria-controls="app-sidebar" :aria-expanded="!isNarrow">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="9" y1="3" x2="9" y2="21"></line>
                    </svg>
                </button>
                <slot name="left">
                    <nav class="breadcrumb" aria-label="Breadcrumb">
                        <template v-for="(item, idx) in breadcrumbs" :key="`${idx}-${item.title}`">
                            <button v-if="item.to && idx < breadcrumbs.length - 1" type="button"
                                class="breadcrumb-item breadcrumb-link" @click="goBreadcrumb(item.to)">
                                {{ item.title }}
                            </button>
                            <button v-else class="breadcrumb-item breadcrumb-current">{{ item.title }}</button>
                            <span v-if="idx < breadcrumbs.length - 1" class="breadcrumb-sep">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                    stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <polyline points="9 18 15 12 9 6"></polyline>
                                </svg>
                            </span>
                        </template>
                    </nav>
                </slot>
            </div>

            <div class="app-header__right">
                <Transition name="header-status" mode="out-in">
                    <div v-if="showStatusBadge" :key="statusText" class="status-badge connection-status-badge"
                        :class="{ 'status-action': canManualReconnect }" @click="handleBadgeClick">
                        <span class="status-dot" :class="{
                            'status-offline': isWsDisconnected && !canManualReconnect,
                            'status-warning': canManualReconnect,
                            'status-online': !isWsDisconnected
                        }"></span>
                        <span class="status-text">{{ statusText }}</span>
                    </div>
                </Transition>
            </div>
        </div>
    </header>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter, type RouteLocationRaw } from 'vue-router'
import { useSidebar } from '@/composables/useSidebar'
import { getStoredMusicQuery } from '@/composables/useMusicQuery'
import { wsClient } from '@/stores/wsClient'

const route = useRoute()
const router = useRouter()

const title = computed<string>(() => String(route.meta.title ?? 'ncm-sync'))

type BreadcrumbItem = { title: string; to?: RouteLocationRaw }

const breadcrumbs = computed<BreadcrumbItem[]>(() => {
    const currentTitle = String(title.value ?? 'ncm-sync')
    const parent = route.meta.parent as BreadcrumbItem | undefined

    if (parent && parent.title) {
        let parentTo: RouteLocationRaw = parent.to ?? { path: route.matched[0]?.path || '/' }

        if (route.name === 'music-detail') {
            const storedQuery = getStoredMusicQuery()
            if (storedQuery) {
                if (typeof parentTo === 'string') {
                    parentTo = { path: parentTo, query: storedQuery }
                } else {
                    const { ...rest } = parentTo
                    parentTo = { ...rest, query: storedQuery }
                }
            }
        }

        return [
            { title: parent.title, to: parentTo },
            { title: currentTitle },
        ]
    }
    return [{ title: currentTitle }]
})

const goBreadcrumb = (to?: RouteLocationRaw) => {
    if (to) {
        router.push(to)
        return
    }
    router.back()
}

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

const { connectionState, userMessage, canManualReconnect } = wsClient.reactiveState

const isWsDisconnected = computed(() => connectionState.value !== 'open')
const showStatusBadge = ref(isWsDisconnected.value);

const statusText = computed(() => {
    if (userMessage.value) {
        return userMessage.value
    }
    return isWsDisconnected.value ? '连接已断开' : '已连接'
})

const handleBadgeClick = () => {
    if (canManualReconnect.value) {
        wsClient.retryConnect()
    }
}

// 新增：专门控制 UI 显示的变量
// 1. 显式定义 timer 的类型
// ReturnType<typeof setTimeout> 会自动根据当前环境获取正确的定时器类型
let timer: ReturnType<typeof setTimeout> | null = null;

watch(isWsDisconnected, (newVal) => {
    if (newVal) {
        if (timer) clearTimeout(timer);
        showStatusBadge.value = true;
    } else {
        showStatusBadge.value = true;

        if (timer) clearTimeout(timer);

        // 2. 这里的赋值现在是类型安全的
        timer = setTimeout(() => {
            showStatusBadge.value = false;
        }, 1000);
    }
}, { immediate: true });
</script>


<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.app-header {
    /* 1. 核心修复：增加顶部安全区域内边距 */
    padding-top: env(safe-area-inset-top);

    /* 2. 修改高度计算：原本高度 + 安全区高度 */
    /* 不要写死 height: 50px，改用 min-height 或 content-box */
    height: calc(50px + env(safe-area-inset-top));

    position: sticky; // 建议用 sticky 或保持 relative，取决于父容器
    top: 0;
    z-index: 100;

    background: var(--bg-base);
    backdrop-filter: blur(20px);

    /* 3. 防止点击时出现系统默认的灰色高亮方块 */
    -webkit-tap-highlight-color: transparent;

    transition: background-color 0.3s ease, border-color 0.3s ease;

}

.app-header__inner {
    /* 保持内容在 50px 的正中间，不受安全区 padding 影响 */
    height: 50px;
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

.breadcrumb {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
}

/* 基础面包屑项样式提取 */
.breadcrumb-item {
    font-size: 1.2rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 40dvw;

    /* 核心对齐属性 */
    display: inline-flex;
    align-items: center;
    height: 32px;
    /* 固定高度确保基准线一致 */
    padding: 0 8px;
    /* 左右间距保持一致 */
    line-height: 1;
    /* 消除行高带来的动态边距 */
    border: 1px solid transparent;
    /* 关键：current 也要有透明边框占用空间 */
    background: transparent;
    box-sizing: border-box;
    /* 确保边框不撑大盒子 */
}

.breadcrumb-link {
    border-radius: $radius-sm;
    cursor: pointer;
    color: var(--text-secondary);
    transition: all 0.3s ease;
    // border: 0px;

    &:hover {
        background: var(--bg-surface);
        color: var(--text-primary);
        border-color: var(--border-hover);
    }
}

.breadcrumb-current {
    /* 移除之前的 margin-top 和 margin-left */
    color: var(--text-primary);
    cursor: default;
    transition: all 0.3s ease;

}

.breadcrumb-sep {
    display: inline-flex;
    align-items: center;
    color: var(--text-tertiary);
    user-select: none;
    /* 确保分隔符也居中 */
    height: 32px;
}

.app-header__left {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm); // 控制 sidebar-toggle 和 title 的间距
}

.app-header__right {
    display: flex;
    align-items: center;
    justify-content: flex-end;
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
    width: 32px;
    height: 32px;
    border-radius: $radius-full;
    border: 0px solid var(--border-color);
    background: transparent;
    color: var(--text-secondary);
    // background: var(--bg-surface);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all $ts-quick, border-color 0.3s ease;

    touch-action: manipulation;

    &:hover {
        background: var(--bg-surface);
        color: var(--text-primary);
        // border-color: var(--border-hover);
    }

    &:active {
        background: var(--bg-surface-active); // 增加按下时的视觉反馈
        transform: scale(0.92);
    }
}

.connection-status-badge {
    position: sticky;
    bottom: 0px;
    right: 0px;
    font-size: auto;
    font-weight: auto;
    margin-left: $space-md;
}

.status-action {
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
        background-color: var(--bg-surface-hover);
        transform: translateY(-1px);
    }

    &:active {
        transform: translateY(0);
    }
}

.status-warning {
    background-color: #faad14;
    box-shadow: 0 0 0 2px rgba(250, 173, 20, 0.2);
}

.status-text {
    white-space: nowrap;
}

/* 1. 定义过渡的时间和曲线，只针对 opacity */
.header-status-enter-active,
.header-status-leave-active {
    transition: opacity 0.25s ease;
}

/* 2. 定义隐藏状态：透明度为 0 */
.header-status-enter-from,
.header-status-leave-to {
    opacity: 0;
}

/* 3. 定义显示状态：透明度为 1 */
.header-status-enter-to,
.header-status-leave-from {
    opacity: 1;
}
</style>
