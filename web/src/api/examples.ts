import api from '@/api'

export async function loginExample() {
  try {
    const qrResult = await api.auth.startQRLogin()

    if (qrResult.success && qrResult.data.code === 200 && qrResult.data.data) {
      const qrKey = qrResult.data.data.qr_key

      const checkLogin = async () => {
        const checkResult = await api.auth.checkQRLogin(qrKey)
        return (
          checkResult.success &&
          checkResult.data.code === 200 &&
          checkResult.data.data?.status === 'success'
        )
      }

      for (let i = 0; i < 15; i++) {
        await new Promise((resolve) => setTimeout(resolve, 2000))
        if (await checkLogin()) break
      }
    }
  } catch {
    return
  }
}

