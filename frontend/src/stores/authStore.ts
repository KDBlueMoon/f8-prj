import { create } from 'zustand'
import type { CompanyBrief, User } from '@/types/auth'

/**
 * `checking` là trạng thái lúc mới tải trang: chưa biết người dùng đã đăng nhập
 * hay chưa vì access token chỉ nằm trong bộ nhớ, phải gọi /auth/refresh mới rõ.
 * Thiếu trạng thái này thì ProtectedRoute sẽ đá người dùng ra trang đăng nhập
 * ngay khi họ F5.
 */
export type AuthStatus = 'checking' | 'authenticated' | 'anonymous'

interface AuthState {
  status: AuthStatus
  user: User | null
  company: CompanyBrief | null
  /** Cố ý KHÔNG lưu vào localStorage: XSS đọc được localStorage. */
  accessToken: string | null
  setSession: (session: { access_token: string; user: User; company: CompanyBrief | null }) => void
  clearSession: () => void
  markAnonymous: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  status: 'checking',
  user: null,
  company: null,
  accessToken: null,

  setSession: ({ access_token, user, company }) =>
    set({ status: 'authenticated', accessToken: access_token, user, company }),

  clearSession: () =>
    set({ status: 'anonymous', accessToken: null, user: null, company: null }),

  markAnonymous: () => set({ status: 'anonymous' }),
}))

/** Đọc token ngoài React (dùng trong apiClient). */
export const getAccessToken = (): string | null => useAuthStore.getState().accessToken
