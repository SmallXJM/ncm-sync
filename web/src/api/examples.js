// API 使用示例
import { AuthService, UserService, MusicService } from '@/api'

// 示例1：用户登录流程
export async function loginExample() {
  try {
    // 开始二维码登录
    const qrResult = await AuthService.startQRLogin()
    
    if (qrResult.success) {
      console.log('二维码生成成功:', qrResult.data.data.qr_img)
      
      // 轮询检查登录状态
      const checkLogin = async () => {
        const checkResult = await AuthService.checkQRLogin(qrResult.data.data.qr_key)
        
        if (checkResult.success && checkResult.data.data.status === 'success') {
          console.log('登录成功！')
          return true
        }
        return false
      }
      
      // 每2秒检查一次，最多检查15次（30秒）
      for (let i = 0; i < 15; i++) {
        await new Promise(resolve => setTimeout(resolve, 2000))
        if (await checkLogin()) {
          break
        }
      }
    }
  } catch (error) {
    console.error('登录失败:', error)
  }
}

// 示例2：获取用户信息
export async function getUserInfoExample() {
  try {
    const result = await UserService.getCurrentUser()
    
    if (result.success && result.data.code === 200) {
      const userInfo = result.data.data.account
      console.log('用户信息:', userInfo)
      return userInfo
    } else {
      console.log('未登录或获取用户信息失败')
      return null
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    return null
  }
}

// 示例3：音乐搜索
export async function searchMusicExample(keywords) {
  try {
    const result = await MusicService.enhancedSearch({
      keywords,
      search_type: 'song',
      limit: 10,
      include_details: false
    })
    
    if (result.success && result.data.code === 200) {
      const songs = result.data.data.results?.result?.songs || []
      console.log(`找到 ${songs.length} 首歌曲:`)
      songs.forEach((song, index) => {
        console.log(`${index + 1}. ${song.name} - ${song.ar?.map(a => a.name).join(', ')}`)
      })
      return songs
    } else {
      console.log('搜索失败:', result.data?.message)
      return []
    }
  } catch (error) {
    console.error('搜索失败:', error)
    return []
  }
}

// 示例4：会话管理
export async function sessionManagementExample() {
  try {
    // 获取所有会话
    const sessionsResult = await UserService.getSessionsList()
    
    if (sessionsResult.success && sessionsResult.data.code === 200) {
      const sessions = sessionsResult.data.data.sessions
      console.log('会话列表:')
      sessions.forEach((session, index) => {
        console.log(`${index + 1}. ${session.nickname} (${session.is_valid ? '有效' : '无效'})`)
      })
      
      // 如果有多个有效会话，可以切换
      const validSessions = sessions.filter(s => s.is_valid && !s.is_current)
      if (validSessions.length > 0) {
        console.log('切换到第一个有效会话...')
        const switchResult = await UserService.switchSession(validSessions[0].session_id)
        
        if (switchResult.success) {
          console.log('切换成功！')
        } else {
          console.log('切换失败:', switchResult.data?.message)
        }
      }
    }
  } catch (error) {
    console.error('会话管理失败:', error)
  }
}

// 示例5：错误处理
export async function errorHandlingExample() {
  try {
    // 故意调用一个可能失败的 API
    const result = await UserService.getCurrentUser()
    
    if (result.success) {
      if (result.data.code === 200) {
        console.log('API 调用成功:', result.data.data)
      } else {
        console.log('业务错误:', result.data.message)
      }
    } else {
      // 网络错误或其他异常
      console.log('请求失败:', result.error)
      
      // 根据状态码处理不同类型的错误
      switch (result.status) {
        case 0:
          console.log('网络连接失败')
          break
        case 408:
          console.log('请求超时')
          break
        case 401:
          console.log('未授权，需要重新登录')
          break
        case 500:
          console.log('服务器内部错误')
          break
        default:
          console.log('未知错误')
      }
    }
  } catch (error) {
    console.error('异常错误:', error)
  }
}