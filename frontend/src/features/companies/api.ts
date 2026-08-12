import { apiDelete, apiGet, apiPatch, apiPost, buildQuery } from '@/lib/apiClient'
import type {
  Company,
  CompanyAddress,
  Page,
  PublicCompanyDetail,
  PublicCompanyListItem,
  TaxCodeLookup,
} from '@/types/company'

export const listPublicCompanies = (params: {
  q?: string
  group_id?: string
  page?: number
}): Promise<Page<PublicCompanyListItem>> =>
  apiGet<Page<PublicCompanyListItem>>(`/companies${buildQuery({ ...params })}`)

export const getPublicCompany = (slug: string): Promise<PublicCompanyDetail> =>
  apiGet<PublicCompanyDetail>(`/companies/${encodeURIComponent(slug)}`)

export const lookupTaxCode = (taxCode: string): Promise<TaxCodeLookup> =>
  apiGet<TaxCodeLookup>(`/companies/lookup-tax-code/${encodeURIComponent(taxCode)}`)

export const getMyCompany = (): Promise<Company> => apiGet<Company>('/employer/company')

export const updateMyCompany = (payload: Partial<Company>): Promise<Company> =>
  apiPatch<Company>('/employer/company', payload)

export const addAddress = (payload: {
  city_id: number
  address_detail: string
}): Promise<CompanyAddress> => apiPost<CompanyAddress>('/employer/company/addresses', payload)

export const deleteAddress = (addressId: string): Promise<void> =>
  apiDelete<void>(`/employer/company/addresses/${addressId}`)
