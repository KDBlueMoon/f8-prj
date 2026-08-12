import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { logout } from '@/features/auth/api'
import { useAuthStore } from '@/stores/authStore'

const ROLE_LABELS = {
  CANDIDATE: 'Ứng viên',
  EMPLOYER: 'Nhà tuyển dụng',
  ADMIN: 'Quản trị viên',
} as const

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
