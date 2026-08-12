import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactElement } from 'react'
import { Suspense, lazy } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import LoginPage from '@/features/auth/LoginPage'
import RegisterCandidatePage from '@/features/auth/RegisterCandidatePage'
import RegisterEmployerPage from '@/features/auth/RegisterEmployerPage'
import { useSessionBootstrap } from '@/features/auth/useSessionBootstrap'
import AdminCompaniesPage from '@/features/admin/AdminCompaniesPage'
import AdminUsersPage from '@/features/admin/AdminUsersPage'
import CompanyProfilePage from '@/features/employer/CompanyProfilePage'
import JobListPage from '@/features/employer/JobListPage'
import HomePage from '@/pages/HomePage'
import {
  CandidateProfilePage,
  EmployerDashboardPage,
  ForbiddenPage,
  NotFoundPage,
} from '@/pages/DashboardPages'
import { useAuthStore } from '@/stores/authStore'

/**
 * Trang soạn tin kéo theo TipTap + ProseMirror (~500 kB) nhưng chỉ nhà tuyển
 * dụng đang đăng tin mới dùng tới. Tách ra để ứng viên và khách không phải tải.
 */
const JobFormPage = lazy(() => import('@/features/employer/JobFormPage'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Người dùng chuyển tab quay lại không cần gọi lại toàn bộ API.
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function PageLoader() {
  return <p className="p-8 text-center text-sm text-slate-500">Đang tải…</p>
}

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
        <Route path="/ntd/cong-ty" element={<CompanyProfilePage />} />
        <Route path="/ntd/tin-tuyen-dung" element={<JobListPage />} />
        {/* "tao" đứng trước ":jobId" để không bị bắt nhầm thành id tin. */}
        <Route
          path="/ntd/tin-tuyen-dung/tao"
          element={
            <Suspense fallback={<PageLoader />}>
              <JobFormPage />
            </Suspense>
          }
        />
        <Route
          path="/ntd/tin-tuyen-dung/:jobId"
          element={
            <Suspense fallback={<PageLoader />}>
              <JobFormPage />
            </Suspense>
          }
        />
      </Route>

      <Route element={<ProtectedRoute allow={['ADMIN']} />}>
        <Route path="/admin/cong-ty" element={<AdminCompaniesPage />} />
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
