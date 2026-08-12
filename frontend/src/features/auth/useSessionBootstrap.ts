import { useEffect } from 'react'
import { apiPost } from '@/lib/apiClient'
import { useAuthStore } from '@/stores/authStore'
import type { LoginResponse } from '@/types/auth'

/**
 * Khôi phục phiên đăng nhập khi tải lại trang.
 *
 * Access token chỉ nằm trong bộ nhớ nên F5 là mất. Refresh token nằm trong
 * httpOnly cookie vẫn còn, nên gọi /auth/refresh một lần lúc khởi động để lấy
 * access token mới. Thất bại thì coi như chưa đăng nhập.
 */
export function useSessionBootstrap(): void {
  useEffect(() => {
    let cancelled = false

    apiPost<LoginResponse>('/auth/refresh', undefined, true)
      .then((session) => {
        if (!cancelled) useAuthStore.getState().setSession(session)
      })
      .catch(() => {
        if (!cancelled) useAuthStore.getState().markAnonymous()
      })

    return () => {
      cancelled = true
    }
  }, [])
}
