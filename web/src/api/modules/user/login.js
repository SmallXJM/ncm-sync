import { http } from '../../request.js'

/**
 * Login 相关 API 服务
 */

export const getLoginStatus = async () => 
    http.post('/api/login/status', {})

export const getLoginQrKey = async () => 
    http.post('/api/login/qr/key', {})

export const getLoginQrCheck = async (key) => 
    http.post('/api/login/qr/check', {key})

export const getLoginQrCreate = async ({key,qrimg,platform}) => 
    http.post('/api/login/qr/create', {key,qrimg,platform})