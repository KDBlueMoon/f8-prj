import { apiGet, apiPost } from '@/lib/apiClient'
import { useAuthStore } from '@/stores/authStore'
import type { LoginResponse, MeResponse } from '@/types/auth'
import type { EmployerRegisterValues, LoginValues, CandidateRegisterValues } from './schemas'

// skipAuthRefresh = true: các endpoint này chính là nơi xử lý phiên đăng nhập,
// gọi lại /auth/refresh khi chúng trả 401 chỉ tạo vòng lặp vô nghĩa.
export const login = (values: LoginValues): Promise<LoginResponse> =>
  apiPost<LoginResponse>('/auth/login', values, true)

export const registerCandidate = (values: CandidateRegisterValues): Promise<LoginResponse> =>
  apiPost<LoginResponse>('/auth/register/candidate', toCandidatePayload(values), true)

export const registerEmployer = (values: EmployerRegisterValues): Promise<LoginResponse> =>
  apiPost<LoginResponse>('/auth/register/employer', toEmployerPayload(values), true)

export const fetchMe = (): Promise<MeResponse> => apiGet<MeResponse>('/auth/me')

export async function logout(): Promise<void> {
  try {
    await apiPost<void>('/auth/logout', undefined, true)
  } finally {
    // Xoá phiên ở client kể cả khi gọi API thất bại — người dùng bấm đăng xuất
    // thì phải được đăng xuất, không mắc kẹt vì lỗi mạng.
    useAuthStore.getState().clearSession()
  }
}

/** Bỏ confirm_password và các ô để trống trước khi gửi lên server. */
function toCandidatePayload(values: CandidateRegisterValues) {
  return {
    email: values.email,
    password: values.password,
    full_name: values.full_name,
    phone_number: values.phone_number || null,
  }
}

function toEmployerPayload(values: EmployerRegisterValues) {
  return {
    email: values.email,
    password: values.password,
    full_name: values.full_name,
    phone_number: values.phone_number || null,
    company: {
      tax_code: values.company.tax_code,
      company_name: values.company.company_name,
      international_name: values.company.international_name || null,
      short_name: values.company.short_name || null,
      director: values.company.director,
      headquarters_address: values.company.headquarters_address,
      email: values.company.email,
      phone_number: values.company.phone_number,
      company_size: values.company.company_size,
      website: values.company.website || null,
      category_group_id: values.company.category_group_id || null,
    },
  }
}
