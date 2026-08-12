import { apiDelete, apiGet, apiPatch, apiPost, buildQuery } from '@/lib/apiClient'
import type { Page } from '@/types/company'
import type { Job, JobInput, JobListItem, JobStatus } from '@/types/job'

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
