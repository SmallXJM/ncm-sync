<template>
    <div class="layout">
        <AppSidebar />

        <div class="layout__main" :class="{ 'layout__main--narrow': isNarrow }">
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
import { useSidebar } from '@/composables/useSidebar'

const { isNarrow } = useSidebar()
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
    margin-left: $nav-width-sidebar-widen;
    height: 100vh;
    /* Changed from min-height to fixed height */
    display: flex;
    flex-direction: column;
    /* overflow: hidden; Removed to allow shadow to cast outside */
    transition: margin-left 0.3s ease;

    &.layout__main--narrow {
        margin-left: $nav-width-sidebar-narrow;
    }
}

@media (max-width: 768px) {
    .layout__main {
        margin-left: 0 !important;
    }
}

.layout__content-wrapper {
    flex: 1;
    /* 占满剩余高度 */
    position: relative;
    // z-index: 150;
    min-height: 0;
    // --- 核心修改开始 ---

    // 2. 制造悬浮感：通过 margin 设置左、右、底部的间距
    // 这里的 16px 是间距大小，你可以根据需要调整
    // margin-top: 0 意味着紧贴 Header
    margin: 0 8px 8px 8px;

    // 3. 模块化外观：必须给 Wrapper 一个背景色，否则它是透明的
    background: var(--bg-surface, #ffffff); // 假设你有一个亮色的背景变量，否则默认白色

    // 4. 圆角与阴影
    border-radius: $radius-lg; // 设置四周圆角
    box-shadow: var(--shadow-ly);

    // 5. 溢出处理：确保圆角不被内部内容遮挡，且限制滚动区域在卡片内
    overflow: hidden;
    display: flex; // 让内部的 content 能够继承高度
    flex-direction: column;

    transition: box-shadow 0.3s ease, background-color 0.3s ease;

}

.layout__content {
    flex: 1;
    overflow-y: auto;
    /* Internal scroll */
    background: var(--bg-body);
    transition: background-color 0.3s ease;

    /* 可选，让内容内部圆角跟随父元素 */
    // box-shadow: -8px -8px 56px rgba(0, 0, 0, 0.6);

    /* 滚动条样式适配 */
    scrollbar-color: var(--text-secondary) transparent;

    &::-webkit-scrollbar {
        width: 12px;
        height: 12px;
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
