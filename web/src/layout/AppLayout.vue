<template>
    <div class="layout">
        <AppSidebar />

        <div class="layout__main">
            <AppHeader />
            <div class="layout__content-wrapper">
                <main class="layout__content">
                    <slot />
                </main>
            </div>
        </div>
    </div>
</template>



<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables.scss' as *;

.layout {
    min-height: 100vh;
    width: 100%;
    background: var(--bg-base);
    transition: background-color 0.3s ease, border-color 0.3s ease;

}

.layout__main {
    margin-left: $nav-width-desktop;
    height: 100vh;
    /* Changed from min-height to fixed height */
    display: flex;
    flex-direction: column;
    /* overflow: hidden; Removed to allow shadow to cast outside */
}

.layout__content-wrapper {
    flex: 1;
    overflow: hidden;
    position: relative;
    z-index: 850;
    /* Higher than Sidebar (800), Lower than Header (900) */
    /* This shadow is now fixed and won't move with scroll */
    // box-shadow: -8px -8px 56px rgba(0, 0, 0, 0.6);
    // background: var(--bg-base);
    // border-top-left-radius: 56px;
    /* White content area */
    /* 12px or use 8px as requested */
    box-shadow: var(--shadow-ly);

    border-top-left-radius: $radius-md;
    border-bottom-left-radius: $radius-md;
    /* 让阴影圆角生效 */
}

.layout__content {
    height: 100%;
    overflow-y: auto;
    /* Internal scroll */
    background: var(--bg-base);
    transition: background-color 0.3s ease;

    /* 可选，让内容内部圆角跟随父元素 */
    // box-shadow: -8px -8px 56px rgba(0, 0, 0, 0.6);

    /* 滚动条样式适配 */
    &::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    &::-webkit-scrollbar-track {
        background: transparent;
        border-radius: $radius-full;
    }

    &::-webkit-scrollbar-thumb {
        background-color: var(--text-secondary);
        border-radius: $radius-full;
        border: 2px solid transparent;
        background-clip: content-box;
        transition: background-color 0.3s ease;
    }

    &::-webkit-scrollbar-thumb:hover {
        background-color: var(--text-primary);
    }
}

</style>
