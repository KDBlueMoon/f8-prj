import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { EmptyState, PublicShell } from '@/components/layout/PublicShell'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { SafeHtml } from '@/components/ui/SafeHtml'
import { getPublicJob } from '@/features/jobs/api'
import { CompanyLogo } from '@/features/jobs/JobCard'
import { daysUntil, formatDate, formatSalary } from '@/features/jobs/format'
import { apiGet } from '@/lib/apiClient'
import { useAuthStore } from '@/stores/authStore'
import { COMPANY_SIZE_LABELS } from '@/types/auth'
import type { City } from '@/types/catalog'
import { EXPERIENCE_LABELS, GENDER_LABELS, JOB_TYPE_LABELS } from '@/types/job'

export default function JobDetailPage() {
  const { slug } = useParams<{ slug: string }>()
  const user = useAuthStore((state) => state.user)

  const { data: job, isPending, isError } = useQuery({
    queryKey: ['publicJob', slug],
    queryFn: () => getPublicJob(slug as string),
    enabled: Boolean(slug),
  })
  const { data: cities } = useQuery({
    queryKey: ['cities'],
    queryFn: () => apiGet<City[]>('/cities'),
    staleTime: 60 * 60 * 1000,
  })

  if (isPending) {
    return (
      <PublicShell width="narrow">
        <p className="text-sm text-slate-500">Đang tải…</p>
      </PublicShell>
    )
  }

  if (isError || !job) {
    return (
      <PublicShell width="narrow">
        <EmptyState
          title="Tin tuyển dụng không còn tồn tại"
          hint="Tin có thể đã hết hạn, được đóng hoặc bị gỡ."
        />
        <div className="mt-4 text-center">
          <Link to="/viec-lam" className="text-sm font-medium text-brand hover:underline">
            ← Xem các việc làm khác
          </Link>
        </div>
      </PublicShell>
    )
  }

  const remaining = daysUntil(job.deadline)
  const cityName = (cityId: number) =>
    cities?.find((city) => city.id === cityId)?.name ?? `#${cityId}`

  return (
    <PublicShell>
      <div className="gap-5 lg:flex">
        <div className="min-w-0 flex-1">
          <header className="rounded-xl border border-slate-200 bg-white p-5">
            <div className="flex flex-wrap items-start gap-2">
              <h1 className="min-w-0 flex-1 text-xl font-bold text-slate-900">{job.title}</h1>
              {job.is_hot && <Badge tone="warning">Nổi bật</Badge>}
            </div>
            {job.specialty && <p className="mt-1 text-sm text-slate-500">{job.specialty}</p>}

            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <Highlight label="Mức lương" value={formatSalary(job)} />
              <Highlight
                label="Địa điểm"
                value={job.locations.map((item) => cityName(item.city_id)).join(', ')}
              />
              <Highlight label="Kinh nghiệm" value={EXPERIENCE_LABELS[job.experience_level]} />
            </div>

            <p className="mt-4 text-sm text-slate-600">
              Hạn nộp hồ sơ: <strong>{formatDate(job.deadline)}</strong>{' '}
              <span className={remaining <= 7 ? 'text-red-600' : 'text-slate-500'}>
                (còn {remaining} ngày)
              </span>
            </p>

            <div className="mt-4">
              <ApplyButton role={user?.role} />
            </div>
          </header>

          <section className="mt-4 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="mb-3 font-bold text-slate-800">Chi tiết tin tuyển dụng</h2>
            {/* SafeHtml lọc lại bằng DOMPurify dù backend đã sanitize lúc lưu. */}
            <ContentBlock title="Mô tả công việc" html={job.description_html} />
            <ContentBlock title="Yêu cầu ứng viên" html={job.requirements_html} />
            <ContentBlock title="Quyền lợi" html={job.benefits_html} />

            <h3 className="mb-2 mt-6 font-semibold text-slate-800">Địa điểm làm việc</h3>
            <ul className="space-y-1 text-sm text-slate-600">
              {job.locations.map((location) => (
                <li key={location.id}>
                  {cityName(location.city_id)}
                  {location.address_detail && ` — ${location.address_detail}`}
                </li>
              ))}
            </ul>
          </section>

          <section className="mt-4 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="mb-3 font-bold text-slate-800">Thông tin chung</h2>
            <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
              <Row label="Hình thức làm việc" value={JOB_TYPE_LABELS[job.job_type]} />
              <Row label="Số lượng tuyển" value={`${job.quantity} người`} />
              <Row label="Giới tính" value={GENDER_LABELS[job.gender]} />
              <Row label="Ngày đăng" value={formatDate(job.created_at)} />
            </dl>
          </section>
        </div>

        <aside className="mt-4 shrink-0 lg:mt-0 lg:w-80">
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <div className="flex gap-3">
              <CompanyLogo company={job.company} />
              <div className="min-w-0">
                <Link
                  to={`/cong-ty/${job.company.slug}`}
                  className="font-semibold leading-snug text-slate-900 hover:text-brand"
                >
                  {job.company.company_name}
                </Link>
                {job.company.verification_tier === 'VERIFIED' && (
                  <div className="mt-1">
                    <Badge tone="success">✔ Đã xác thực</Badge>
                  </div>
                )}
              </div>
            </div>

            <dl className="mt-4 space-y-2 text-sm">
              <Row label="Quy mô" value={COMPANY_SIZE_LABELS[job.company.company_size]} />
              <Row label="Địa chỉ" value={job.company.headquarters_address} />
              {job.company.website && <Row label="Website" value={job.company.website} />}
            </dl>

            <Link
              to={`/cong-ty/${job.company.slug}`}
              className="mt-4 block text-center text-sm font-medium text-brand hover:underline"
            >
              Xem trang công ty →
            </Link>
          </div>
        </aside>
      </div>
    </PublicShell>
  )
}

/**
 * Nút ứng tuyển.
 *
 * Luồng apply thật thuộc P5 nên ở đây chỉ dẫn đúng hướng theo vai trò: nhà
 * tuyển dụng không ứng tuyển được, khách chưa đăng nhập thì đưa về trang đăng
 * nhập kèm `next` để quay lại đúng tin này.
 */
function ApplyButton({ role }: { role?: 'CANDIDATE' | 'EMPLOYER' | 'ADMIN' }) {
  if (role === 'EMPLOYER' || role === 'ADMIN') {
    return (
      <p className="text-sm text-slate-500">
        Tài khoản {role === 'EMPLOYER' ? 'nhà tuyển dụng' : 'quản trị viên'} không ứng tuyển được.
      </p>
    )
  }

  if (!role) {
    return (
      <Link to={`/dang-nhap?next=${encodeURIComponent(window.location.pathname)}`}>
        <Button>Đăng nhập để ứng tuyển</Button>
      </Link>
    )
  }

  return (
    <Button disabled title="Tính năng ứng tuyển sẽ mở ở bước tiếp theo">
      Ứng tuyển ngay
    </Button>
  )
}

function ContentBlock({ title, html }: { title: string; html: string }) {
  return (
    <div className="mb-5">
      <h3 className="mb-1.5 font-semibold text-slate-800">{title}</h3>
      <SafeHtml html={html} />
    </div>
  )
}

function Highlight({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-0.5 font-semibold text-slate-800">{value || '—'}</p>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2">
      <dt className="shrink-0 text-slate-500">{label}:</dt>
      <dd className="min-w-0 break-words text-slate-800">{value}</dd>
    </div>
  )
}
