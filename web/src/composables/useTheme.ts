import { ref } from 'vue'
import { updateThemeColor } from "@/utils/theme"

export type ThemeMode = 'light' | 'dark' | 'system'

// 全局单例状态，保证多组件共享
const themeMode = ref<ThemeMode>('system')
const colorSchemeMq = window.matchMedia('(prefers-color-scheme: dark)')

export function useTheme() {
    
    // 核心渲染函数：根据计算结果修改 HTML 类名
    const applyTheme = () => {
        const html = document.documentElement;
        let targetIsDark: boolean;

        if (themeMode.value === 'system') {
            // 1. 移除显式类名，让 CSS 的 @media (prefers-color-scheme) 生效
            html.classList.remove('dark', 'light');
            // 2. 判定系统当前真实状态
            targetIsDark = colorSchemeMq.matches;
        } else {
            targetIsDark = themeMode.value === 'dark';
            // 3. 显式添加类名
            html.classList.toggle('dark', targetIsDark);
            html.classList.toggle('light', !targetIsDark);
        }

        // 4. 同步更新 iOS 状态栏颜色
        // 这里的颜色值应与你 CSS 变量 --bg-base 的值保持绝对一致
        // 注意：这里可能需要根据实际 CSS 变量值进行微调，或者从 CSS 变量读取
        // 目前先保持原有的硬编码值，后续优化可改为 getComputedStyle
        const color = targetIsDark ? '#05070c' : '#f3f4f6';
        updateThemeColor(color);
    };

    // 监听器回调：当浏览器/系统主题改变时自动执行
    const handleSystemThemeChange = () => {
        if (themeMode.value === 'system') {
            applyTheme()
        }
    }

    // 初始化函数（应在 App.vue 中调用一次）
    const initTheme = () => {
        const saved = localStorage.getItem('theme-preference') as ThemeMode
        if (saved) themeMode.value = saved

        applyTheme()

        // 注册监听器
        colorSchemeMq.addEventListener('change', handleSystemThemeChange)
        
        // 返回清理函数
        return () => {
            colorSchemeMq.removeEventListener('change', handleSystemThemeChange)
        }
    }

    // 三态切换逻辑
    const cycleTheme = () => {
        if (themeMode.value === 'light') themeMode.value = 'dark'
        else if (themeMode.value === 'dark') themeMode.value = 'system'
        else themeMode.value = 'light'

        localStorage.setItem('theme-preference', themeMode.value)
        applyTheme() // 切换模式后立即生效
    }

    return {
        themeMode,
        initTheme,
        cycleTheme,
        applyTheme
    }
}
