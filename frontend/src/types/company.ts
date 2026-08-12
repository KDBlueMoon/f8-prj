import type { CompanySize, CompanyStatus, UserRole, VerificationTier } from '@/types/auth'

/** Chỉ 4 trường này VietQR trả về — phần còn lại nhà tuyển dụng nhập tay. */
export interface TaxCodeLookup {
  tax_code: string
  company_name: string
  international_name: string | null
  short_name: string | null
  headquarters_address: string | null
}

export interface CompanyAddress {
  id: string
  city_id: number
  address_detail: string
}

export interface Company {
  id: string
  tax_code: string
  company_name: string
  international_name: string | null
  short_name: string | null
  slug: string
  director: string
  headquarters_address: string
  issued_date: string | null
  email: string
  phone_number: string
  website: string | null
  logo_url: string | null
  company_size: CompanySize
  category_group_id: string | null
  description_html: string | null
  status: CompanyStatus
  rejected_reason: string | null
  verification_tier: VerificationTier
  /** NULL nghĩa là chưa đối chiếu được tên công ty với VietQR. */
  tax_code_verified_at: string | null
  created_at: string
  addresses: CompanyAddress[]
}

export interface CompanyListItem {
  id: string
  tax_code: string
  company_name: string
  short_name: string | null
  slug: string
  director: string
  email: string
  phone_number: string
  company_size: CompanySize
  status: CompanyStatus
  verification_tier: VerificationTier
  tax_code_verified_at: string | null
  created_at: string
}

export interface AdminUser {
  id: string
  email: string
  role: UserRole
  full_name: string
  phone_number: string | null
  is_active: boolean
  created_at: string
}

export interface PageMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface Page<T> {
  items: T[]
  meta: PageMeta
}

export const COMPANY_STATUS_LABELS: Record<CompanyStatus, string> = {
  PENDING: 'Chờ duyệt',
  APPROVED: 'Đã duyệt',
  REJECTED: 'Đã từ chối',
}
