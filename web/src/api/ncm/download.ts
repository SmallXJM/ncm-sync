import { http, type ApiEnvelope, type ApiResult } from '../request'
import { NCM_API } from '../config'

const DOWNLOAD = NCM_API.DOWNLOAD

export interface CreateJobParams {
  job_name: string
  job_type: string
  source_type: string
  source_id: string
  storage_path: string
  source_name?: string
  source_owner_id?: string
  target_quality?: string
  download_cover?: boolean
  download_lyrics?: boolean
  embed_metadata?: boolean
  filename_template?: string
}

export const createJob = async (params: CreateJobParams): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(DOWNLOAD.CREATE_JOB, params)
}
