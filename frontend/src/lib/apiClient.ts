import { useAuthStore } from '@/stores/authStore'
import type { LoginResponse } from '@/types/auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

/** Lỗi nghiệp vụ từ backend: { detail: { code, message } } */
export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
    /** Lỗi validate 422: map field -> thông báo, để gán vào đúng ô nhập. */
    readonly fieldErrors?: Record<string, string>,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface RequestOptions {
  method?: string
  body?: unknown
  /** Bỏ qua bước tự làm mới token — dùng cho chính các endpoint auth. */
  skipAuthRefresh?: boolean
}

/**
 * Chỉ cho phép một lượt gọi /auth/refresh tại một thời điểm.
 *
 * Backend luân chuyển refresh token mỗi lần dùng, nên nếu hai request cùng hết
 * hạn và cùng gọi refresh thì lượt thứ hai sẽ dùng token đã bị thu hồi và
 * người dùng bị đăng xuất oan.
 */
let pendingRefresh: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  pendingRefresh ??= (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      })
      if (!response.ok) return null

      const session = (await response.json()) as LoginResponse
      useAuthStore.getState().setSession(session)
      return session.access_token
    } catch {
      return null
    } finally {
      pendingRefresh = null
    }
  })()

  return pendingRefresh
}

async function send(path: string, options: RequestOptions, token: string | null): Promise<Response> {
  const headers: Record<string, string> = {}
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  return fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    // Cần cho httpOnly cookie chứa refresh token.
    credentials: 'include',
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response = await send(path, options, useAuthStore.getState().accessToken)

  // Access token sống 15 phút. Hết hạn thì lấy token mới rồi thử lại đúng
  // một lần — người dùng không thấy gì bất thường.
  if (response.status === 401 && !options.skipAuthRefresh) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      response = await send(path, options, newToken)
    } else {
      useAuthStore.getState().clearSession()
    }
  }

  if (!response.ok) throw await toApiError(response)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const apiGet = <T>(path: string): Promise<T> => apiRequest<T>(path)

export const apiPost = <T>(path: string, body?: unknown, skipAuthRefresh = false): Promise<T> =>
  apiRequest<T>(path, { method: 'POST', body, skipAuthRefresh })

async function toApiError(response: Response): Promise<ApiError> {
  let body: unknown
  try {
    body = await response.json()
  } catch {
    // Backend chết hoặc proxy trả HTML — vẫn phải báo lỗi rõ ràng.
    return new ApiError('NETWORK_ERROR', 'Không kết nối được máy chủ.', response.status)
  }

  const detail = (body as { detail?: unknown }).detail

  // 422 của FastAPI: detail là mảng lỗi theo từng trường.
  if (Array.isArray(detail)) {
    const fieldErrors: Record<string, string> = {}
    for (const item of detail as Array<{ loc?: unknown[]; msg?: string }>) {
      // loc dạng ["body", "company", "tax_code"] -> "company.tax_code"
      const field = (item.loc ?? []).slice(1).join('.')
      if (field && item.msg) fieldErrors[field] = normalizeMessage(item.msg)
    }
    return new ApiError(
      'VALIDATION_ERROR',
      'Thông tin nhập chưa hợp lệ. Vui lòng kiểm tra lại.',
      response.status,
      fieldErrors,
    )
  }

  const typed = detail as { code?: string; message?: string } | undefined
  return new ApiError(
    typed?.code ?? 'UNKNOWN_ERROR',
    typed?.message ?? 'Đã có lỗi xảy ra, vui lòng thử lại.',
    response.status,
  )
}

/** Pydantic gắn tiền tố "Value error, " vào thông báo của validator tự viết. */
const normalizeMessage = (message: string): string => message.replace(/^Value error,\s*/, '')
