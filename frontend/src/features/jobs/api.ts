import { apiDelete, apiGet, apiPatch, apiPost, buildQuery } from '@/lib/apiClient'
import type { Page } from '@/types/company'
import type {
  Job,
  JobInput,
  JobListItem,
  JobSort,
  JobStatus,
  PublicJobDetail,
  PublicJobListItem,
} from '@/types/job'

/** Bộ lọc của `GET /jobs`, khớp đúng tên tham số backend nhận. */
export interface PublicJobFilters {
  q?: string
  category_id?: string
  group_id?: string
  city_id?: number
  job_type?: string
  experience_level?: string
  salary_min?: number
  salary_max?: number
  is_hot?: boolean
  sort?: JobSort
  page?: number
  page_size?: number
}

export const listPublicJobs = (filters: PublicJobFilters): Promise<Page<PublicJobListItem>> =>
  apiGet<Page<PublicJobListItem>>(
    `/jobs${buildQuery({ ...filters, is_hot: filters.is_hot ? 'true' : undefined })}`,
  )

export const getPublicJob = (slug: string): Promise<PublicJobDetail> =>
  apiGet<PublicJobDetail>(`/jobs/${encodeURIComponent(slug)}`)

export interface EmployerJobListParams {
  status?: JobStatus
  q?: string
  page?: number
}

export const listMyJobs = (params: EmployerJobListParams): Promise<Page<JobListItem>> =>
  apiGet<Page<JobListItem>>(`/employer/jobs${buildQuery({ ...params })}`)

export const countMyJobs = (): Promise<Record<JobStatus, number>> =>
  apiGet<Record<JobStatus, number>>('/employer/jobs/counts')

export const getMyJob = (jobId: string): Promise<Job> => apiGet<Job>(`/employer/jobs/${jobId}`)

export const createJob = (payload: JobInput): Promise<Job> =>
  apiPost<Job>('/employer/jobs', payload)

export const updateJob = (jobId: string, payload: Partial<JobInput>): Promise<Job> =>
  apiPatch<Job>(`/employer/jobs/${jobId}`, payload)

/** Chỉ PUBLISHED và CLOSED — hai trạng thái còn lại thuộc quyền admin/hệ thống. */
export const changeJobStatus = (
  jobId: string,
  status: Extract<JobStatus, 'PUBLISHED' | 'CLOSED'>,
): Promise<Job> => apiPatch<Job>(`/employer/jobs/${jobId}/status`, { status })

export const deleteJob = (jobId: string): Promise<void> =>
  apiDelete<void>(`/employer/jobs/${jobId}`)
