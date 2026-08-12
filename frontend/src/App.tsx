import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactElement } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import LoginPage from '@/features/auth/LoginPage'
import RegisterCandidatePage from '@/features/auth/RegisterCandidatePage'
import RegisterEmployerPage from '@/features/auth/RegisterEmployerPage'
import { useSessionBootstrap } from '@/features/auth/useSessionBootstrap'
import HomePage from '@/pages/HomePage'
import {
  AdminUsersPage,
  CandidateProfilePage,
  EmployerDashboardPage,
  ForbiddenPage,
  NotFoundPage,
} from '@/pages/DashboardPages'
import { useAuthStore } from '@/stores/authStore'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Người dùng chuyển tab quay lại không cần gọi lại toàn bộ API.
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

/** Người đã đăng nhập thì không cần thấy trang đăng nhập/đăng ký nữa. */
function GuestOnly({ children }: { children: ReactElement }) {
  const status = useAuthStore((state) => state.status)
  const user = useAuthStore((state) => state.user)

  if (status === 'checking') return null
  if (status === 'authenticated' && user) return <Navigate to="/" replace />
  return children
}

function AppRoutes() {
  useSessionBootstrap()

  return (
    <Routes>
      <Route path="/" element={<HomePage />} />

      <Route
        path="/dang-nhap"
        element={
          <GuestOnly>
            <LoginPage />
          </GuestOnly>
        }
      />
      <Route
        path="/dang-ky"
        element={
          <GuestOnly>
            <RegisterCandidatePage />
          </GuestOnly>
        }
      />
      <Route
        path="/dang-ky/nha-tuyen-dung"
        element={
          <GuestOnly>
            <RegisterEmployerPage />
          </GuestOnly>
        }
      />

      <Route element={<ProtectedRoute allow={['CANDIDATE']} />}>
        <Route path="/ung-vien/ho-so" element={<CandidateProfilePage />} />
      </Route>

      <Route element={<ProtectedRoute allow={['EMPLOYER']} />}>
        <Route path="/ntd/tong-quan" element={<EmployerDashboardPage />} />
      </Route>

      <Route element={<ProtectedRoute allow={['ADMIN']} />}>
        <Route path="/admin/nguoi-dung" element={<AdminUsersPage />} />
      </Route>

      <Route path="/khong-co-quyen" element={<ForbiddenPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
