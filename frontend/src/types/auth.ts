export type UserRole = 'CANDIDATE' | 'EMPLOYER' | 'ADMIN'
export type CompanyStatus = 'PENDING' | 'APPROVED' | 'REJECTED'
export type VerificationTier = 'UNVERIFIED' | 'VERIFIED'

export type CompanySize = '1-9' | '10-24' | '25-99' | '100-499' | '500-1000' | '1000+'

export const COMPANY_SIZE_LABELS: Record<CompanySize, string> = {
  '1-9': '1 - 9 nhân viên',
  '10-24': '10 - 24 nhân viên',
  '25-99': '25 - 99 nhân viên',
  '100-499': '100 - 499 nhân viên',
  '500-1000': '500 - 1000 nhân viên',
  '1000+': 'Trên 1000 nhân viên',
}

export interface User {
  id: string
  email: string
  role: UserRole
  full_name: string
  phone_number: string | null
  avatar_url: string | null
}

export interface CompanyBrief {
  id: string
  company_name: string
  short_name: string | null
  slug: string
  logo_url: string | null
  status: CompanyStatus
  verification_tier: VerificationTier
  rejected_reason: string | null
}

/** Refresh token không có ở đây — nó nằm trong httpOnly cookie. */
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
  company: CompanyBrief | null
}

export interface MeResponse {
  user: User
  company: CompanyBrief | null
}
