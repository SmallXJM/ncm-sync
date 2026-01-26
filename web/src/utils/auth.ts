
const TOKEN_KEY = 'ncm_auth_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export async function sha256(message: string) {
  // 检查原生支持
  if (window.crypto && window.crypto.subtle) {
    const msgBuffer = new TextEncoder().encode(message)
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer)
    return Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')
  }
  
  // 降级方案：动态导入或直接使用 js-sha256
  const { sha256: fallbackSha256 } = await import('js-sha256')
  return fallbackSha256(message)
}


