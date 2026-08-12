import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { AppHeader } from '@/components/layout/AppHeader'
import { useAuthStore } from '@/stores/authStore'

/**
 * Các trang tạm của P1: chỉ đủ để chứng minh phân quyền hoạt động.
 * Nội dung thật sẽ thay dần từ P2 trở đi.
 */

function PageShell({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-100">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="mb-4 text-xl font-bold text-slate-900">{title}</h1>
        {children}
      </main>
    </div>
  )
}

export function CandidateProfilePage() {
  const user = useAuthStore((state) => state.user)

  return (
    <PageShell title="Hồ sơ ứng viên">
      <dl className="max-w-md rounded-xl border border-slate-200 bg-white p-5 text-sm">
        <div className="flex justify-between border-b border-slate-100 py-2">
          <dt className="text-slate-500">Họ và tên</dt>
          <dd className="font-medium text-slate-800">{user?.full_name}</dd>
        </div>
        <div className="flex justify-between border-b border-slate-100 py-2">
          <dt className="text-slate-500">Email</dt>
          <dd className="font-medium text-slate-800">{user?.email}</dd>
        </div>
        <div className="flex justify-between py-2">
          <dt className="text-slate-500">Số điện thoại</dt>
          <dd className="font-medium text-slate-800">{user?.phone_number ?? '—'}</dd>
        </div>
      </dl>
      <p className="mt-4 text-sm text-slate-500">
        Quản lý CV và lịch sử ứng tuyển sẽ có ở phase P5.
      </p>
    </PageShell>
  )
}

export function EmployerDashboardPage() {
  const company = useAuthStore((state) => state.company)

  return (
    <PageShell title="Tổng quan nhà tuyển dụng">
      {company?.status === 'PENDING' && (
        <div className="mb-5 flex gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4">
          <span aria-hidden className="text-xl">
            ⏳
          </span>
          <div className="text-sm">
            <p className="font-semibold text-amber-900">Hồ sơ công ty đang chờ duyệt</p>
            <p className="mt-0.5 text-amber-800">
              Bạn chưa thể đăng tin tuyển dụng cho tới khi quản trị viên duyệt hồ sơ.
            </p>
          </div>
        </div>
      )}

      {company?.status === 'REJECTED' && (
        <div className="mb-5 rounded-lg border border-red-300 bg-red-50 p-4 text-sm">
          <p className="font-semibold text-red-900">Hồ sơ công ty bị từ chối</p>
          <p className="mt-0.5 text-red-800">{company.rejected_reason}</p>
        </div>
      )}

      <div className="max-w-md rounded-xl border border-slate-200 bg-white p-5 text-sm">
        <p className="font-semibold text-slate-800">{company?.company_name}</p>
        <p className="mt-1 text-slate-500">Trạng thái: {company?.status}</p>
        <p className="text-slate-500">Xác thực: {company?.verification_tier}</p>
      </div>
      <p className="mt-4 text-sm text-slate-500">
        Quản lý tin tuyển dụng sẽ có ở phase P3.
      </p>
    </PageShell>
  )
}

export function AdminUsersPage() {
  return (
    <PageShell title="Quản lý người dùng">
      <p className="text-sm text-slate-500">
        Danh sách người dùng và duyệt công ty sẽ có ở phase P2.
      </p>
    </PageShell>
  )
}

export function ForbiddenPage() {
  return (
    <PageShell title="Không có quyền truy cập">
      <p className="text-sm text-slate-600">
        Tài khoản của bạn không được phép xem trang này.{' '}
        <Link to="/" className="font-semibold text-brand hover:underline">
          Về trang chủ
        </Link>
      </p>
    </PageShell>
  )
}

export function NotFoundPage() {
  return (
    <PageShell title="Không tìm thấy trang">
      <Link to="/" className="text-sm font-semibold text-brand hover:underline">
        Về trang chủ
      </Link>
    </PageShell>
  )
}
