const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

/** Lỗi nghiệp vụ từ backend: { detail: { code, message } } */
export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    // Cần cho httpOnly cookie chứa refresh token (dùng từ P1).
    credentials: 'include',
  })

  if (!response.ok) {
    throw await toApiError(response)
  }
  return (await response.json()) as T
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as { detail?: { code?: string; message?: string } }
    return new ApiError(
      body.detail?.code ?? 'UNKNOWN_ERROR',
      body.detail?.message ?? 'Đã có lỗi xảy ra, vui lòng thử lại.',
      response.status,
    )
  } catch {
    // Response không phải JSON (proxy lỗi, backend chết...) — vẫn phải báo lỗi rõ ràng.
    return new ApiError('NETWORK_ERROR', 'Không kết nối được máy chủ.', response.status)
  }
}
