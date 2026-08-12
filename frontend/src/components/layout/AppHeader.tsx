import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { logout } from '@/features/auth/api'
import { useAuthStore } from '@/stores/authStore'
import type { UserRole } from '@/types/auth'

const ROLE_LABELS = {
  CANDIDATE: 'Ứng viên',
  EMPLOYER: 'Nhà tuyển dụng',
  ADMIN: 'Quản trị viên',
} as const

/** Luôn hiện, kể cả khi chưa đăng nhập — trang việc làm là công khai. */
const PUBLIC_NAV = [
  { to: '/viec-lam', label: 'Việc làm' },
  { to: '/cong-ty', label: 'Công ty' },
]

const NAV_BY_ROLE: Record<UserRole, Array<{ to: string; label: string }>> = {
  CANDIDATE: [{ to: '/ung-vien/ho-so', label: 'Hồ sơ' }],
  EMPLOYER: [
    { to: '/ntd/tong-quan', label: 'Tổng quan' },
    { to: '/ntd/tin-tuyen-dung', label: 'Tin tuyển dụng' },
    { to: '/ntd/cong-ty', label: 'Hồ sơ công ty' },
  ],
  ADMIN: [
    { to: '/admin/cong-ty', label: 'Công ty' },
    { to: '/admin/nguoi-dung', label: 'Người dùng' },
  ],
}

export function AppHeader() {
  const user = useAuthStore((state) => state.user)
  const status = useAuthStore((state) => state.status)
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/dang-nhap', { replace: true })
  }

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-4">
        <Link to="/" className="text-2xl font-black text-brand">
          Top<span className="text-slate-800">CV</span>
        </Link>

        <nav className="hidden gap-5 text-sm font-medium md:flex">
          {[...PUBLIC_NAV, ...(user ? NAV_BY_ROLE[user.role] : [])].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? 'text-brand' : 'text-slate-600 hover:text-brand'
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-3">
          {status === 'authenticated' && user ? (
            <>
              <div className="text-right">
                <p className="text-sm font-semibold text-slate-800">{user.full_name}</p>
                <p className="text-xs text-slate-500">{ROLE_LABELS[user.role]}</p>
              </div>
              <span className="grid h-9 w-9 place-items-center rounded-full bg-brand font-bold text-white">
                {user.full_name.trim().slice(-1).toUpperCase()}
              </span>
              <Button variant="secondary" onClick={handleLogout}>
                Đăng xuất
              </Button>
            </>
          ) : (
            <>
              <Link to="/dang-nhap">
                <Button variant="secondary">Đăng nhập</Button>
              </Link>
              <Link to="/dang-ky">
                <Button>Đăng ký</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
