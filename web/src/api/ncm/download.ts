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

export const updateJob = async (params: UpdateJobParams): Promise<ApiResult<ApiEnvelope<DownloadJobItem>>> => {
  return http.post<ApiEnvelope<DownloadJobItem>>(DOWNLOAD.UPDATE_JOB, params)
}

export const deleteJob = async (job_id: number): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(DOWNLOAD.DELETE_JOB, { job_id })
}



export const getJobList = async (): Promise<ApiResult<ApiEnvelope<{ jobs: DownloadJobItem[]; count: number }>>> => {
  return http.get<ApiEnvelope<{ jobs: DownloadJobItem[]; count: number }>>(DOWNLOAD.GET_JOB_LIST)
}

export interface DownloadTaskItem {
  id: number
  music_id: string
  music_title?: string
  music_artist?: string
  music_album?: string
  job_id: number
  quality?: string
  progress_flags: number
  file_path?: string
  file_name?: string
  file_format?: string
  file_size?: number
  status: string
  error_message?: string
  created_at?: string
  updated_at?: string
  started_at?: string
  completed_at?: string
}

export interface ListTasksParams {
  page?: number
  limit?: number
  job_id?: number
  status?: string
  keyword?: string
}

interface TaskStatusPayload {
  is_running?: boolean
  next_run_time?: string
}

export const getTaskList = async (params: ListTasksParams): Promise<ApiResult<ApiEnvelope<{ tasks: DownloadTaskItem[]; total: number; limit: number; offset: number }>>> => {
  return http.post<ApiEnvelope<{ tasks: DownloadTaskItem[]; total: number; limit: number; offset: number }>>(DOWNLOAD.TASK_LIST, params)
}

export const resetTask = async (task_id: number): Promise<ApiResult<ApiEnvelope<unknown>>> => {
  return http.post<ApiEnvelope<unknown>>(DOWNLOAD.TASK_RESET, { task_id })
}

export const daemonControl = async (
  action: 'start' | 'stop' | 'trigger_now',
): Promise<ApiResult<ApiEnvelope<TaskStatusPayload>>> => {
  return http.post<ApiEnvelope<TaskStatusPayload>>(DOWNLOAD.DAEMON_CONTROL, { action })
}
