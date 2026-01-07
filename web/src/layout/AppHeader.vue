<template>
    <header class="app-header">
        <div class="app-header__inner">
            <div class="app-header__left">
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
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const title = computed(() => {
    return route.meta.title ?? 'ncm-sync'
})
</script>


<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.app-header {
    position: relative;
    /* Changed from sticky to relative since outer container is fixed */
    /* top: 0; */
    z-index: 850;
    height: 60px;
    background: var(--bg-base);
    /* Use base color */
    /* border-bottom: 1px solid $border; */
    backdrop-filter: blur(20px);
    transition: background-color 0.3s ease, border-color 0.3s ease;
}

.app-header__inner {
    max-width: 1200px;
    height: 100%;
    margin: 0 auto;
    padding: 0 $space-xl;
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
</style>
