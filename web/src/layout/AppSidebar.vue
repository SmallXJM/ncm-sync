<template>
    <aside class="sidebar">
        <div class="sidebar__brand">
            <router-link to="/" class="brand-link">
                <span class="brand-icon">🎵</span>
                <span class="brand-text">ncm-sync</span>
            </router-link>
        </div>

        <nav class="sidebar__menu">
            <router-link v-for="item in menus" :key="item.path" :to="item.path" class="menu-item">
                {{ item.title }}
            </router-link>
        </nav>

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
import { ref, onMounted } from 'vue'

interface MenuItem {
    title: string
    path: string
}

const menus: MenuItem[] = [
    { title: '首页', path: '/' },
    { title: '账号管理', path: '/account' }
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
    width: $nav-width-desktop;
    height: 100vh;
    background: var(--bg-base); /* Use base color */
    /* border-right: 1px solid var(--border-color); */
    padding: $space-md;
    display: flex;
    flex-direction: column;
    gap: $space-md;
    z-index: 800;
    /* Lowered from 1000 to allow Content shadow to be visible */
    transition: background-color 0.3s ease, border-color 0.3s ease;
}

.sidebar__brand {
    padding-bottom: $space-sm;
    // border-bottom: 1px solid var(--border-color);
    transition: border-color 0.3s ease;
}

.brand-link {
    display: flex;
    align-items: center;
    gap: $space-sm;
    font-weight: 600;
    color: var(--text-primary);
    text-decoration: none;
}

.brand-icon {
    font-size: 1.4rem;
}

.sidebar__menu {
    display: flex;
    flex-direction: column;
    gap: $space-xs;
    flex: 1;
    /* 占据剩余空间，将 footer 推到底部 */
}

.menu-item {
    padding: $space-sm $space-md;
    border-radius: $radius-sm;
    color: var(--text-primary);
    text-decoration: none;
    font-size: 0.95rem;
    transition: all $ts-quick;

    &:hover {
        background: var(--bg-surface-hover);
        color: var(--text-primary);
    }
}

.menu-item.router-link-active {
    background: var(--sidebar-active-bg);
    color: var(--sidebar-active-text);
}

.sidebar__footer {
    padding-top: $space-sm;
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: right;
    transition: border-color 0.3s ease;
}

.theme-toggle {
    width: 40px;
    height: 40px;
    border-radius: $radius-sm;
    border: 1px solid var(--border-color);
    background: var(--bg-surface);
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all $ts-quick;

    &:hover {
        background: var(--bg-surface-hover);
        color: var(--text-primary);
        border-color: var(--text-secondary);
    }
}
</style>
