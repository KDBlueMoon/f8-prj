import { apiGet, apiPatch, buildQuery } from '@/lib/apiClient'
import type { CompanyStatus, VerificationTier } from '@/types/auth'
import type { AdminUser, Company, CompanyListItem, Page } from '@/types/company'

export interface CompanyListParams {
  status?: CompanyStatus
  q?: string
  page?: number
}

export const listCompanies = (params: CompanyListParams): Promise<Page<CompanyListItem>> =>
  apiGet<Page<CompanyListItem>>(`/admin/companies${buildQuery({ ...params })}`)

export const countCompanies = (): Promise<Record<CompanyStatus, number>> =>
  apiGet<Record<CompanyStatus, number>>('/admin/companies/counts')

export const getCompany = (companyId: string): Promise<Company> =>
  apiGet<Company>(`/admin/companies/${companyId}`)

export const decideCompany = (
  companyId: string,
  payload: { status: 'APPROVED' | 'REJECTED'; rejected_reason?: string },
): Promise<Company> => apiPatch<Company>(`/admin/companies/${companyId}/status`, payload)

export const setVerification = (
  companyId: string,
  verificationTier: VerificationTier,
): Promise<Company> =>
  apiPatch<Company>(`/admin/companies/${companyId}/verification`, {
    verification_tier: verificationTier,
  })

export const listUsers = (params: { q?: string; page?: number }): Promise<Page<AdminUser>> =>
  apiGet<Page<AdminUser>>(`/admin/users${buildQuery({ ...params })}`)

export const setUserActive = (userId: string, isActive: boolean): Promise<AdminUser> =>
  apiPatch<AdminUser>(`/admin/users/${userId}/status`, { is_active: isActive })
