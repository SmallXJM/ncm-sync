import { http, type ApiEnvelope, type ApiResult } from '../request'
import { NCM_API } from '../config'

export interface RecentAddedMusicDay {
  date: string
  count: number
}

export interface DashboardAggregate {
  recent_added_music: {
    days: RecentAddedMusicDay[]
  }
}

export const getAggregate = async (): Promise<ApiResult<ApiEnvelope<DashboardAggregate>>> => {
  return http.get<ApiEnvelope<DashboardAggregate>>(NCM_API.DASHBOARD.AGGREGATE)
}
