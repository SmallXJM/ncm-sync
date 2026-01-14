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
                    <nav class="breadcrumb" aria-label="Breadcrumb">
                        <template v-for="(item, idx) in breadcrumbs" :key="`${idx}-${item.title}`">
                            <button v-if="item.to && idx < breadcrumbs.length - 1" type="button"
                                class="breadcrumb-item breadcrumb-link" @click="goBreadcrumb(item.to)">
                                {{ item.title }}
                            </button>
                            <span v-else class="breadcrumb-item breadcrumb-current">{{ item.title }}</span>
                            <span v-if="idx < breadcrumbs.length - 1" class="breadcrumb-sep">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                    stroke-linecap="round" stroke-linejoin="round">
                                    <polyline points="9 18 15 12 9 6"></polyline>
                                </svg>
                            </span>
                        </template>
                    </nav>
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
import { useRoute, useRouter, type RouteLocationRaw } from 'vue-router'
import { useSidebar } from '@/composables/useSidebar'
import { getStoredMusicQuery } from '@/composables/useMusicQuery'

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
                    const { query, ...rest } = parentTo
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

.breadcrumb {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
}

.breadcrumb-item {
    font-size: 1.1rem;
    font-weight: 600;
    color: $text-strong;
    transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 40vw;
}

.breadcrumb-link {
    background: transparent;
    border: 1px solid transparent;
    border-radius: $radius-sm;
    padding: 4px 8px;
    cursor: pointer;
    color: var(--text-secondary);

    &:hover {
        background: var(--bg-surface-hover);
        color: var(--text-primary);
        border-color: var(--border-hover);
    }
}

.breadcrumb-current {
    // 对齐 breadcrumb-link
    padding: 4px 8px;
    margin-top: -2px;
    margin-left: 1px;
    // padding: 4px 0;
    color: var(--text-primary);
}

.breadcrumb-sep {
    // 调整位置到最底下 
    line-height: 1;
    color: var(--text-tertiary);

    // font-weight: 500;
    user-select: none;
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
    transition: all $ts-quick, border-color 0.3s ease;

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
