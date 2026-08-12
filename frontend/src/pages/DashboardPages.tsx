import { Link } from 'react-router-dom'
import { PageShell } from '@/components/layout/PageShell'
import { CompanyStatusBadge } from '@/components/ui/Badge'
import { useAuthStore } from '@/stores/authStore'

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
    <PageShell
      title="Tổng quan nhà tuyển dụng"
      subtitle={company?.company_name}
      actions={company && <CompanyStatusBadge status={company.status} />}
    >
      {company?.status === 'PENDING' && (
        <div className="mb-5 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm">
          <p className="font-semibold text-amber-900">Hồ sơ công ty đang chờ duyệt</p>
          <p className="mt-0.5 text-amber-800">
            Bạn chưa thể đăng tin tuyển dụng cho tới khi quản trị viên duyệt hồ sơ.{' '}
            <Link to="/ntd/cong-ty" className="font-semibold underline">
              Xem hồ sơ công ty
            </Link>
          </p>
        </div>
      )}

      {company?.status === 'REJECTED' && (
        <div className="mb-5 rounded-lg border border-red-300 bg-red-50 p-4 text-sm">
          <p className="font-semibold text-red-900">Hồ sơ công ty bị từ chối</p>
          <p className="mt-0.5 text-red-800">{company.rejected_reason}</p>
          <Link to="/ntd/cong-ty" className="mt-2 inline-block font-semibold text-red-900 underline">
            Sửa hồ sơ và gửi duyệt lại
          </Link>
        </div>
      )}

      {company?.status === 'APPROVED' && (
        <div className="mb-5 rounded-lg border border-green-200 bg-brand-light p-4 text-sm text-brand-dark">
          Hồ sơ công ty đã được duyệt. Chức năng đăng tin tuyển dụng sẽ có ở phase P3.
        </div>
      )}
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
