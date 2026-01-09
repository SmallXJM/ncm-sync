<template>
    <aside class="sidebar" :class="{ 'sidebar--narrow': isNarrow }">
        <div class="sidebar__brand">
            <router-link to="/" class="brand-link" :title="isNarrow ? 'ncm-sync' : ''">
                <span class="brand-icon">🎵</span>
                <span class="brand-text">ncm-sync</span>
            </router-link>
        </div>

        <nav class="sidebar__menu">
            <router-link v-for="item in menus" :key="item.path" :to="item.path" class="menu-item" :title="item.title">
                <component :is="item.icon" class="menu-icon" />
                <span class="menu-text">{{ item.title }}</span>
            </router-link>
        </nav>

        <div class="sidebar__setting">
            <router-link to="/config" class="menu-item" title="设置">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" fill-rule="evenodd"><path d="m12.594 23.258l-.012.002l-.071.035l-.02.004l-.014-.004l-.071-.036q-.016-.004-.024.006l-.004.01l-.017.428l.005.02l.01.013l.104.074l.015.004l.012-.004l.104-.074l.012-.016l.004-.017l-.017-.427q-.004-.016-.016-.018m.264-.113l-.014.002l-.184.093l-.01.01l-.003.011l.018.43l.005.012l.008.008l.201.092q.019.005.029-.008l.004-.014l-.034-.614q-.005-.019-.02-.022m-.715.002a.02.02 0 0 0-.027.006l-.006.014l-.034.614q.001.018.017.024l.015-.002l.201-.093l.01-.008l.003-.011l.018-.43l-.003-.012l-.01-.01z"/><path fill="currentColor" d="M16 15c1.306 0 2.418.835 2.83 2H20a1 1 0 1 1 0 2h-1.17a3.001 3.001 0 0 1-5.66 0H4a1 1 0 1 1 0-2h9.17A3 3 0 0 1 16 15m0 2a1 1 0 1 0 0 2a1 1 0 0 0 0-2M8 9a3 3 0 0 1 2.762 1.828l.067.172H20a1 1 0 0 1 .117 1.993L20 13h-9.17a3.001 3.001 0 0 1-5.592.172L5.17 13H4a1 1 0 0 1-.117-1.993L4 11h1.17A3 3 0 0 1 8 9m0 2a1 1 0 1 0 0 2a1 1 0 0 0 0-2m8-8c1.306 0 2.418.835 2.83 2H20a1 1 0 1 1 0 2h-1.17a3.001 3.001 0 0 1-5.66 0H4a1 1 0 0 1 0-2h9.17A3 3 0 0 1 16 3m0 2a1 1 0 1 0 0 2a1 1 0 0 0 0-2"/></g></svg>
                <span class="menu-text">设置</span>
            </router-link>
        </div>

        <div class="sidebar__footer">
            <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '切换到浅色模式' : '切换到深色模式'">
                <!-- Sun Icon -->
                <svg v-if="!isDark" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
            </button>
        </div>
    </aside>
</template>

<script setup lang="ts">
import { ref, onMounted, h, type Component } from 'vue'
import { useSidebar } from '@/composables/useSidebar'

const { isNarrow } = useSidebar()

// 定义图标组件
const HomeIcon = h('svg', {
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
    h('path', { d: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z' }),
    h('polyline', { points: '9 22 9 12 15 12 15 22' })
])

const UserIcon = h('svg', {
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

const SettingsIcon = h('svg', {
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
    h('circle', { cx: '12', cy: '12', r: '3' }),
    h('path', {
        d: 'M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83' +
            ' 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33' +
            ' 1.65 1.65 0 0 0-1 1.51V22a2 2 0 0 1-2 2' +
            ' 2 2 0 0 1-2-2v-.09a1.65 1.65 0 0 0-1-1.51' +
            ' 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0' +
            ' 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15' +
            ' 1.65 1.65 0 0 0 3.09 14H3a2 2 0 0 1-2-2' +
            ' 2 2 0 0 1 2-2h.09a1.65 1.65 0 0 0 1.51-1' +
            ' 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83' +
            ' 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.6' +
            ' 1.65 1.65 0 0 0 10 3.09V3a2 2 0 0 1 2-2' +
            ' 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51' +
            ' 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0' +
            ' 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82' +
            ' 1.65 1.65 0 0 0 1.51 1H22a2 2 0 0 1 2 2' +
            ' 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'
    })
])

interface MenuItem {
    title: string
    path: string
    icon: Component
}

const menus: MenuItem[] = [
    { title: '首页', path: '/', icon: HomeIcon },
    { title: '账号管理', path: '/account', icon: UserIcon },
    // { title: '设置', path: '/config', icon: SettingsIcon }
]

const isDark = ref(false)

const toggleTheme = () => {
    isDark.value = !isDark.value
    const html = document.documentElement

    if (isDark.value) {
        html.classList.add('dark')
        html.classList.remove('light')
        localStorage.setItem('theme', 'dark')
    } else {
        html.classList.add('light')
        html.classList.remove('dark')
        localStorage.setItem('theme', 'light')
    }
}

onMounted(() => {
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        isDark.value = true
        document.documentElement.classList.add('dark')
    } else {
        isDark.value = false
        document.documentElement.classList.add('light')
    }
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: $nav-width-sidebar-widen;
    height: 100vh;
    background: var(--bg-base);
    /* Use base color */
    /* border-right: 1px solid var(--border-color); */
    padding: $space-md;
    display: flex;
    flex-direction: column;
    gap: $space-md;
    z-index: 800;
    /* Lowered from 1000 to allow Content shadow to be visible */
    transition: width 0.3s ease, padding 0.3s ease, background-color 0.3s ease;

    &.sidebar--narrow {
        width: $nav-width-sidebar-narrow;
        // padding: $space-md $space-xs;
        // 保持右侧 padding 为 space-md (12px)，左侧为 space-xs (4px)
        // 这样配合 flex-end，按钮(40px)在64px宽度下：左(4+8)px，右12px -> 视觉居中
        padding: $space-md $space-md $space-md $space-md;

        .brand-text,
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
}

.brand-icon {
    font-size: 1.4rem;
    flex-shrink: 0;
    /* 防止图标被压缩 */
}

.brand-text {
    transition: opacity 0.2s ease, max-width 0.2s ease;
    white-space: nowrap;
    // 添加 max-width 以支持过渡
    max-width: 200px;
    overflow: hidden;
}

.sidebar__menu {
    display: flex;
    flex-direction: column;
    gap: $space-xs;
    flex: 1;
    width: 100%;
    /* 占据剩余空间，将 footer 推到底部 */
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
        background: var(--bg-surface-hover);
        color: var(--text-primary);
    }


}

.menu-icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
}

.menu-text {
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
    display: flex;
    // justify-content: flex-end;
    transition: border-color 0.3s ease, gap 0.3s ease, padding 0.3s ease;
    width: 100%;

}

.theme-toggle {
    width: 100%;
    height: 40px;
    border-radius: $radius-lg;
    border: 1px solid var(--border-color);
    background: var(--bg-surface);
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all $ts-quick, background-color 0.3s ease;
    ;

    &:hover {
        background: var(--bg-surface-hover);
        color: var(--text-primary);
        border-color: var(--text-secondary);
    }
}
</style>
