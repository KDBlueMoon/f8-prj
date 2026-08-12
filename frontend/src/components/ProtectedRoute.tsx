import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import type { UserRole } from '@/types/auth'

interface ProtectedRouteProps {
  allow: UserRole[]
}

/**
 * Chặn route theo vai trò.
 *
 * Đây CHỈ là lớp trải nghiệm — ai cũng sửa được state phía trình duyệt. Quyền
 * thật do backend quyết định qua dependency require_role trên từng endpoint.
 */
export function ProtectedRoute({ allow }: ProtectedRouteProps) {
  const status = useAuthStore((state) => state.status)
  const user = useAuthStore((state) => state.user)
  const location = useLocation()

  // Vừa tải trang: còn đang gọi /auth/refresh để khôi phục phiên. Điều hướng
  // lúc này sẽ đá nhầm người dùng đang đăng nhập ra ngoài mỗi lần F5.
  if (status === 'checking') {
    return (
      <div className="grid min-h-screen place-items-center text-sm text-slate-500">
        Đang kiểm tra phiên đăng nhập…
      </div>
    )
  }

  if (status === 'anonymous' || !user) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/dang-nhap?next=${next}`} replace />
  }

  if (!allow.includes(user.role)) {
    return <Navigate to="/khong-co-quyen" replace />
  }

  return <Outlet />
}
