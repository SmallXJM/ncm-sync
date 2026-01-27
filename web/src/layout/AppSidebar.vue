<template>
    <aside id="app-sidebar" class="sidebar"
        :class="{ 'sidebar--narrow': isNarrow && !isMobile, 'sidebar--open': isMobileOpen }" role="navigation"
        :aria-hidden="isMobile && !isMobileOpen" :aria-modal="isMobile ? 'true' : 'false'" tabindex="-1">
        <div class="sidebar__brand">
            <router-link to="/" class="brand-link" :title="isNarrow ? 'ncm-sync' : ''" @click="handleMenuItemClick">
                <span class="brand-icon">
                    <img alt="logo" width="32" height="32" />
                </span>
                <div class="brand-info">
                    <span class="brand-title">NCM Sync</span>
                    <span class="brand-subtitle">音乐同步工具</span>
                </div>
            </router-link>
        </div>

        <nav class="sidebar__menu">
            <div v-for="(group, index) in menuGroups" :key="index" class="menu-group">
                <div v-if="group.title" class="menu-group-title">{{ group.title }}</div>
                <router-link v-for="item in group.items" :key="item.path" :to="item.path" class="menu-item"
                    :title="item.title" @click="handleMenuItemClick">
                    <component :is="item.icon" class="menu-icon" />
                    <span class="menu-text">{{ item.title }}</span>
                </router-link>
            </div>
        </nav>


        <div class="sidebar__footer">

            <button class="theme-toggle menu-item" @click="cycleTheme"
                :title="'当前模式: ' + (themeMode === 'light' ? '浅色' : themeMode === 'dark' ? '深色' : '设备')">
                <div class="menu-icon-wrapper">
                    <!-- Sun Icon -->
                    <svg v-if="themeMode === 'light'" xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                        viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round">
                        <circle cx="12" cy="12" r="5"></circle>
                        <line x1="12" y1="1" x2="12" y2="3"></line>
                        <line x1="12" y1="21" x2="12" y2="23"></line>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                        <line x1="1" y1="12" x2="3" y2="12"></line>
                        <line x1="21" y1="12" x2="23" y2="12"></line>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                    </svg>
                    <!-- Moon Icon -->
                    <svg v-else-if="themeMode === 'dark'" xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                        viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                    </svg>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                        fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                        <line x1="8" y1="21" x2="16" y2="21"></line>
                        <line x1="12" y1="17" x2="12" y2="21"></line>
                        <text x="7" y="13" font-size="8" font-weight="bold" fill="currentColor"
                            stroke-width="0">A</text>
                    </svg>
                </div>
                <span class="menu-text">
                    {{ themeMode === 'light' ? '浅色' : themeMode === 'dark' ? '深色' : '设备' }}
                </span>
            </button>

            <div class="sidebar__setting">
                <router-link to="/config" class="menu-item" title="设置" @click="handleMenuItemClick">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                        <g fill="none" fill-rule="evenodd">
                            <path
                                d="m12.594 23.258l-.012.002l-.071.035l-.02.004l-.014-.004l-.071-.036q-.016-.004-.024.006l-.004.01l-.017.428l.005.02l.01.013l.104.074l.015.004l.012-.004l.104-.074l.012-.016l.004-.017l-.017-.427q-.004-.016-.016-.018m.264-.113l-.014.002l-.184.093l-.01.01l-.003.011l.018.43l.005.012l.008.008l.201.092q.019.005.029-.008l.004-.014l-.034-.614q-.005-.019-.02-.022m-.715.002a.02.02 0 0 0-.027.006l-.006.014l-.034.614q.001.018.017.024l.015-.002l.201-.093l.01-.008l.003-.011l.018-.43l-.003-.012l-.01-.01z" />
                            <path fill="currentColor"
                                d="M16 15c1.306 0 2.418.835 2.83 2H20a1 1 0 1 1 0 2h-1.17a3.001 3.001 0 0 1-5.66 0H4a1 1 0 1 1 0-2h9.17A3 3 0 0 1 16 15m0 2a1 1 0 1 0 0 2a1 1 0 0 0 0-2M8 9a3 3 0 0 1 2.762 1.828l.067.172H20a1 1 0 0 1 .117 1.993L20 13h-9.17a3.001 3.001 0 0 1-5.592.172L5.17 13H4a1 1 0 0 1-.117-1.993L4 11h1.17A3 3 0 0 1 8 9m0 2a1 1 0 1 0 0 2a1 1 0 0 0 0-2m8-8c1.306 0 2.418.835 2.83 2H20a1 1 0 1 1 0 2h-1.17a3.001 3.001 0 0 1-5.66 0H4a1 1 0 0 1 0-2h9.17A3 3 0 0 1 16 3m0 2a1 1 0 1 0 0 2a1 1 0 0 0 0-2" />
                        </g>
                    </svg>
                    <span class="menu-text">设置</span>
                </router-link>
            </div>
        </div>
    </aside>
    <div v-show="isMobile" class="sidebar-overlay" :class="{ visible: isMobileOpen }" @click="closeMobileSidebar"
        aria-hidden="true" />
</template>

<script lang="ts">
import { h, type Component } from 'vue'

const DashboardIcon: Component = () => h(
    'svg',
    {
        xmlns: 'http://www.w3.org/2000/svg',
        width: 20,
        height: 20,
        viewBox: '0 0 24 24',
    },
    [
        h(
            'g',
            {
                fill: 'none',
                stroke: 'currentColor',
                'stroke-linecap': 'round',
                'stroke-linejoin': 'round',
                'stroke-width': 2,
            },
            [
                h('path', {
                    d: 'M10 3.2A9 9 0 1 0 20.8 14a1 1 0 0 0-1-1H13a2 2 0 0 1-2-2V4a.9.9 0 0 0-1-.8',
                }),
                h('path', {
                    d: 'M15 3.5A9 9 0 0 1 20.5 9H16a1 1 0 0 1-1-1z',
                }),
            ]
        ),
    ]
)

const UserIcon: Component = () => h('svg', {
    xmlns: 'http://www.w3.org/2000/svg',
    width: '20',
    height: '20',
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    'stroke-width': '2',
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round'
}, [
    h('path', { d: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2' }),
    h('circle', { cx: '12', cy: '7', r: '4' })
])

const PlaylistIcon: Component = () => h(
    'svg',
    {
        xmlns: 'http://www.w3.org/2000/svg',
        width: '20',
        height: '20',
        viewBox: '0 0 24 24',
    },
    [
        h('path', {
            fill: 'none',
            stroke: 'currentColor',
            'stroke-width': '2',
            'stroke-linecap': 'round',
            'stroke-linejoin': 'round',
            d: 'M11 17a3 3 0 1 0 6 0a3 3 0 1 0-6 0m6 0V4h4m-8 1H3m0 4h10m-4 4H3',
        }),
    ]
)

const FileMusicIcon: Component = () => h(
    'svg',
    {
        xmlns: 'http://www.w3.org/2000/svg',
        width: '20',
        height: '20',
        viewBox: '0 0 24 24',
    },
    [
        h(
            'g',
            {
                fill: 'none',
                stroke: 'currentColor',
                'stroke-width': '2',
                'stroke-linecap': 'round',
                'stroke-linejoin': 'round',
            },
            [
                h('path', {
                    d: 'M14 3v4a1 1 0 0 0 1 1h4',
                }),
                h('path', {
                    d: 'M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2',
                }),
                h('path', {
                    d: 'M10 16a1 1 0 1 0 2 0a1 1 0 0 0-2 0m2 0v-5l2 1',
                }),
            ]
        ),
    ]
)

const BellIcon: Component = () => h(
    'svg',
    {
        xmlns: 'http://www.w3.org/2000/svg',
        width: '20',
        height: '20',
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': '2',
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
    },
    [
        h('path', {
            d: 'M10 5a2 2 0 0 1 4 0a7 7 0 0 1 4 6v3a4 4 0 0 0 2 3H4a4 4 0 0 0 2-3v-3a7 7 0 0 1 4-6',
        }),
        h('path', {
            d: 'M9 17v1a3 3 0 0 0 6 0v-1',
        }),
        h('path', {
            d: 'M21 6.727A11.05 11.05 0 0 0 18.206 3',
        }),
        h('path', {
            d: 'M3 6.727A11.05 11.05 0 0 1 5.792 3',
        }),
    ]
)

export const sidebarIcons = {
    dashboard: DashboardIcon,
    account: UserIcon,
    music: FileMusicIcon,
    subscription: BellIcon,
    playlist: PlaylistIcon,
} as const
</script>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useSidebar } from '@/composables/useSidebar'
import { useTheme } from '@/composables/useTheme'

const { isNarrow, isMobileOpen } = useSidebar()
const { themeMode, cycleTheme } = useTheme()

const mq = window.matchMedia('(max-width: 768px)')
const isMobile = ref(mq.matches)

function handleMqChange(e: MediaQueryListEvent) {
    isMobile.value = e.matches
    if (!e.matches) {
        isMobileOpen.value = false
    }
}

function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && isMobile.value && isMobileOpen.value) {
        isMobileOpen.value = false
    }
}

function closeMobileSidebar() {
    isMobileOpen.value = false
}

function handleMenuItemClick() {
    if (isMobile.value) {
        isMobileOpen.value = false
    }
}

onMounted(() => {
    mq.addEventListener('change', handleMqChange)
    window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
    mq.removeEventListener('change', handleMqChange)
    window.removeEventListener('keydown', handleKeydown)
})

// const TaskIcon = h(
//     'svg',
//     {
//         xmlns: 'http://www.w3.org/2000/svg',
//         width: '24',
//         height: '24',
//         viewBox: '0 0 24 24',
//         fill: 'none',
//         stroke: 'currentColor',
//         'stroke-width': '2',
//         'stroke-linecap': 'round',
//         'stroke-linejoin': 'round',
//     },
//     [
//         h('path', { d: 'M9 11l3 3L22 4' }),
//         h('path', { d: 'M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11' }),
//     ]
// )

type SidebarIcon = (typeof sidebarIcons)[keyof typeof sidebarIcons]

interface MenuItem {
    title: string
    path: string
    icon: SidebarIcon
}

interface MenuGroup {
    title: string
    items: MenuItem[]
}

const menuGroups: MenuGroup[] = [
    {
        title: '总览',
        items: [
            { title: '仪表盘', path: '/', icon: sidebarIcons.dashboard },
            { title: '登录态', path: '/account', icon: sidebarIcons.account },
        ]
    },
    {
        title: '内容管理',
        items: [
            { title: '音乐', path: '/music', icon: sidebarIcons.music },
            { title: '订阅', path: '/subscription', icon: sidebarIcons.subscription },
        ]
    },
    {
        title: '快捷订阅',
        items: [
            { title: '我的歌单', path: '/my/playlist', icon: sidebarIcons.playlist },
        ]
    }
]

onMounted(() => {
    mq.addEventListener('change', handleMqChange)
    window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
    mq.removeEventListener('change', handleMqChange)
    window.removeEventListener('keydown', handleKeydown)
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: $nav-width-sidebar-widen;
    height: 100dvh;
    background: var(--bg-base);
    /* Use base color */
    /* border-right: 1px solid var(--border-color); */
    padding: $space-sm;
    display: flex;
    flex-direction: column;
    gap: $space-md;
    z-index: 100; // 默认较低
    // z-index: 140;
    /* Lowered from 1000 to allow Content shadow to be visible */
    transform: translateX(0);
    transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1), z-index 0s 0.3s, width 0.3s cubic-bezier(0.25, 1, 0.5, 1), background-color 0.3s ease;

    &.sidebar--narrow {
        width: $nav-width-sidebar-narrow;
        // padding: $space-md $space-xs;
        // 保持右侧 padding 为 space-md (12px)，左侧为 space-xs (4px)
        // 这样配合 flex-end，按钮(40px)在64px宽度下：左(4+8)px，右12px -> 视觉居中
        padding: $space-sm;

        .menu-group-title {
            display: none;
        }

        .brand-info,
        .menu-text {
            opacity: 0;
            width: 0;
            // display: none; // 移除 display: none 以支持过渡
            max-width: 0; // 使用 max-width 进行过渡
            overflow: hidden;

        }

        .brand-link {
            // justify-content: center;
            padding-left: 0; // Reset padding if needed
            padding-inline: calc(50% - 14px); // 动态居中，图标宽约 22px
            gap: 0;
        }

        .menu-item {
            // justify-content: center; // 移除跳变的对齐方式
            padding: $space-sm 0;
            padding-inline: calc(50% - 10px); // 使用 padding 动态居中 (10px 是图标一半宽度)
            gap: 0; // 消除间距

            .menu-icon {
                margin: 0;
            }
        }
    }
}

/* 移动端抽屉样式 */
@media (max-width: 768px) {
    .sidebar {
        width: $nav-width-sidebar-widen;
        // max-width: $nav-width-sidebar-widen;
        transform: translateX(-100%);
        z-index: 100; // 默认较低
        box-shadow: var(--shadow-lg);
        // border-right: 1px solid var(--border-color);
        background: var(--bg-modal);
        // transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1), z-index 0s 0.3s, width 0.3s cubic-bezier(0.25, 1, 0.5, 1), background-color 0.3s ease;

    }

    .sidebar.sidebar--open {
        transform: translateX(0);
        z-index: 600; // 弹窗600
        transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1), z-index 0s, background-color 0.3s ease; // 进入时立即调高
    }
}

.sidebar__brand {
    padding-bottom: $space-sm;
    // border-bottom: 1px solid var(--border-color);
    transition: border-color 0.3s ease;
    width: 100%;
    display: flex;
}

.brand-link {
    display: flex;
    align-items: center;
    gap: $space-sm;
    font-weight: 600;
    color: var(--text-primary);
    text-decoration: none;
    overflow: hidden;
    /* 防止文字溢出 */
    transition: gap 0.3s ease, padding 0.3s ease;
    padding: var(--spacing-sm);
}

.brand-icon {
    flex-shrink: 0;
    /* 防止被压缩 */
    display: inline-flex;
    /* 让 img 或 svg 可以居中对齐 */
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}

.brand-icon img {
    content: var(--img-favicon);
    width: 32px;
    height: 32px;
    object-fit: contain;
}

.brand-info {
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: opacity 0.2s ease, max-width 0.2s ease;
    white-space: nowrap;
    max-width: 200px;
    overflow: hidden;
    gap: 2px;
}

.brand-title {
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.2;
    color: var(--text-primary);
    transition: color 0.3s ease;
}

.brand-subtitle {
    font-size: 0.75rem;
    font-weight: 500;
    line-height: 1.2;
    color: var(--text-secondary);
    transition: color 0.3s ease;
}

.sidebar__menu {
    display: flex;
    flex-direction: column;
    gap: $space-md;
    flex: 1;
    width: 100%;
    /* 占据剩余空间，将 footer 推到底部 */
}

.menu-group {
    display: flex;
    flex-direction: column;
    gap: $space-xs;
}

.menu-group-title {
    padding: 0 $space-md;
    font-size: 0.75rem;
    color: var(--text-tertiary);
    font-weight: 500;
    margin-bottom: 2px;
}

.sidebar__setting {
    width: 100%;

    // 这样它就会完全继承 .menu-item 的所有样式（高度、悬浮效果、圆角等）
}

.menu-item {
    padding: $space-sm $space-md;
    border-radius: $radius-sm;
    color: var(--text-primary);
    text-decoration: none;
    font-size: 0.95rem;
    transition: all $ts-quick;
    display: flex;
    align-items: center;
    gap: $space-md;
    /* 图标和文字间距 */

    &:hover {
        background: var(--sidebar-hover);
        color: var(--text-primary);
    }


}

.menu-icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
}

.menu-text {
    font-size: 0.80rem;

    white-space: nowrap;
    overflow: hidden;
    max-width: 200px; // 初始最大宽度，确保能完全显示文本
    transition:
        opacity 0.15s ease,
        max-width 0.2s ease;

}


.menu-item.router-link-active {
    background: var(--sidebar-active-bg);
    color: var(--sidebar-active-text);
}

.sidebar__footer {
    padding-top: $space-sm;
    border-top: 1px solid var(--border-color);
    gap: $space-xs;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    transition: border-color 0.3s ease, gap 0.3s ease, padding 0.3s ease;
    width: 100%;

}

.theme-toggle {
    /* 彻底重置按钮默认样式 */
    width: 100%;
    background: transparent;
    border: none;
    /* 移除之前那个明显的边框 */
    cursor: pointer;
    margin: 0;
    font-family: inherit;
    /* 防止字体不一致导致宽度微差 */

    /* 核心：强制对齐方式 */
    display: flex;
    align-items: center;
    justify-content: flex-start;
    /* 确保靠左对齐，与菜单项一致 */

    /* 间距修正 */
    padding: $space-sm $space-md;
    /* 必须与 .menu-item 的 padding 完全一致 */
    gap: $space-lg;
    /* 必须与 .menu-item 的 gap 完全一致 */

    // 针对收起状态的修正
    .sidebar--narrow & {
        padding-inline: calc(50% - 10px);
        /* 10px 是图标半径，确保图标居中 */
        gap: 0;
    }
}

/* 确保 menu-icon-wrapper 内部的 svg 大小一致 */
/* 统一图标占位 */
.menu-icon-wrapper,
.menu-icon {
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

/* 移动端遮罩层 */
.sidebar-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(2px);
    z-index: 500; //页面遮罩 500
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
}

.sidebar-overlay.visible {
    opacity: 1;
    pointer-events: auto;
}
</style>
