// utils/theme.ts
export function updateThemeColor(color: string) {
  let meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', 'theme-color');
    document.head.appendChild(meta);
  }
  meta.setAttribute('content', color);
}

// 在你切换主题的逻辑中调用
// 例如：updateThemeColor(isDark.value ? '#121212' : '#ffffff');