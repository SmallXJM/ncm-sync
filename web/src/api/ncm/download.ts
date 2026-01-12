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
  embed_cover?: boolean
  embed_lyrics?: boolean
  embed_metadata?: boolean
  filename_template?: string
}

export interface DownloadJobItem {
  id: number
  job_type: 'playlist' | 'album' | 'artist' | string
  source_id: string
  source_name: string
  source_type: string
  job_name: string
  storage_path: string
  filename_template: string
  target_quality: string
  embed_cover: boolean
  embed_lyrics: boolean
  embed_metadata: boolean
  enabled: boolean
  status: string
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  created_at: string
  updated_at: string
}

export type UpdateJobParams = Partial<CreateJobParams> & { job_id: number; enabled?: boolean }

export const createJob = async (params: CreateJobParams): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(DOWNLOAD.CREATE_JOB, params)
}

export const updateJob = async (params: UpdateJobParams): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(DOWNLOAD.UPDATE_JOB, params)
}

export const getJobList = async (): Promise<ApiResult<ApiEnvelope<{ jobs: DownloadJobItem[]; count: number }>>> => {
  return http.get<ApiEnvelope<{ jobs: DownloadJobItem[]; count: number }>>(DOWNLOAD.GET_JOB_LIST)
}