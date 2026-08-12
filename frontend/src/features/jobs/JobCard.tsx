import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/Badge'
import { daysUntil, formatSalary } from '@/features/jobs/format'
import type { City } from '@/types/catalog'
import { EXPERIENCE_LABELS, JOB_TYPE_LABELS, type PublicJobListItem } from '@/types/job'

/** Số ngày còn lại mà dưới mức này thì nhắc "sắp hết hạn" cho ứng viên biết. */
const URGENT_DAYS = 7

interface JobCardProps {
  job: PublicJobListItem
  /** Tra tên tỉnh/thành từ id — danh sách này frontend đã cache sẵn 1 giờ. */
  cities?: City[]
  /** Trang công ty đã hiện tên công ty ở đầu trang rồi, không lặp lại. */
  hideCompany?: boolean
}

export function JobCard({ job, cities, hideCompany = false }: JobCardProps) {
  const remaining = daysUntil(job.deadline)
  const cityNames = job.locations
    .map((location) => cities?.find((city) => city.id === location.city_id)?.name)
    .filter(Boolean)

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 transition hover:border-brand">
      <div className="flex gap-4">
        <CompanyLogo company={job.company} />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start gap-2">
            <h3 className="min-w-0 flex-1 font-semibold leading-snug text-slate-900">
              <Link to={`/viec-lam/${job.slug}`} className="hover:text-brand">
                {job.title}
              </Link>
            </h3>
            {job.is_hot && <Badge tone="warning">Nổi bật</Badge>}
          </div>

          {!hideCompany && (
            <Link
              to={`/cong-ty/${job.company.slug}`}
              className="mt-0.5 block truncate text-sm text-slate-500 hover:text-brand"
            >
              {job.company.short_name ?? job.company.company_name}
              {job.company.verification_tier === 'VERIFIED' && (
                <span className="ml-1 text-brand" title="Đã xác thực">
                  ✔
                </span>
              )}
            </Link>
          )}

          <div className="mt-2 flex flex-wrap gap-1.5 text-xs">
            <Tag>{formatSalary(job)}</Tag>
            {cityNames.length > 0 && <Tag>{cityNames.join(' · ')}</Tag>}
            <Tag>{JOB_TYPE_LABELS[job.job_type]}</Tag>
            <Tag>{EXPERIENCE_LABELS[job.experience_level]}</Tag>
          </div>

          <p
            className={`mt-2 text-xs ${
              remaining <= URGENT_DAYS ? 'font-medium text-red-600' : 'text-slate-500'
            }`}
          >
            {remaining <= URGENT_DAYS
              ? `Còn ${remaining} ngày để ứng tuyển`
              : `Hạn nộp còn ${remaining} ngày`}
          </p>
        </div>
      </div>
    </article>
  )
}

function Tag({ children }: { children: ReactNode }) {
  return <span className="rounded bg-slate-100 px-2 py-1 text-slate-600">{children}</span>
}

/**
 * Logo công ty, thiếu thì lấy chữ cái đầu.
 *
 * Đặt `alt` rỗng có chủ đích: tên công ty đã nằm ngay bên cạnh dưới dạng chữ,
 * để trình đọc màn hình khỏi đọc lặp hai lần.
 */
export function CompanyLogo({
  company,
  size = 'md',
}: {
  company: { company_name: string; logo_url: string | null }
  size?: 'md' | 'lg'
}) {
  const box = size === 'lg' ? 'h-20 w-20 text-2xl' : 'h-14 w-14 text-lg'

  if (company.logo_url) {
    return (
      <img
        src={company.logo_url}
        alt=""
        className={`${box} shrink-0 rounded-lg border border-slate-200 object-contain`}
      />
    )
  }

  return (
    <span
      className={`${box} grid shrink-0 place-items-center rounded-lg border border-slate-200 bg-slate-50 font-bold text-slate-400`}
    >
      {company.company_name.trim().charAt(0).toUpperCase()}
    </span>
  )
}
