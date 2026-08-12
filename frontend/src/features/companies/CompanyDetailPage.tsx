import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { EmptyState, PublicShell } from '@/components/layout/PublicShell'
import { Badge } from '@/components/ui/Badge'
import { SafeHtml } from '@/components/ui/SafeHtml'
import { getPublicCompany } from '@/features/companies/api'
import { CompanyLogo } from '@/features/jobs/JobCard'
import { JobCard } from '@/features/jobs/JobCard'
import { apiGet } from '@/lib/apiClient'
import { COMPANY_SIZE_LABELS } from '@/types/auth'
import type { City } from '@/types/catalog'

export default function CompanyDetailPage() {
  const { slug } = useParams<{ slug: string }>()

  const { data: company, isPending, isError } = useQuery({
    queryKey: ['publicCompany', slug],
    queryFn: () => getPublicCompany(slug as string),
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

  if (isError || !company) {
    return (
      <PublicShell width="narrow">
        <EmptyState
          title="Không tìm thấy công ty này"
          hint="Hồ sơ có thể chưa được duyệt hoặc đã bị gỡ."
        />
        <div className="mt-4 text-center">
          <Link to="/cong-ty" className="text-sm font-medium text-brand hover:underline">
            ← Xem các công ty khác
          </Link>
        </div>
      </PublicShell>
    )
  }

  return (
    <PublicShell>
      <header className="rounded-xl border border-slate-200 bg-white p-5">
        <div className="flex flex-wrap gap-4">
          <CompanyLogo company={company} size="lg" />
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-bold text-slate-900">{company.company_name}</h1>
            {company.international_name && (
              <p className="mt-0.5 text-sm text-slate-500">{company.international_name}</p>
            )}
            <div className="mt-2 flex flex-wrap gap-2">
              {company.verification_tier === 'VERIFIED' && (
                <Badge tone="success">✔ Đã xác thực</Badge>
              )}
              <Badge>{COMPANY_SIZE_LABELS[company.company_size]}</Badge>
              <Badge tone="info">{company.open_jobs.length} tin đang tuyển</Badge>
            </div>
          </div>
        </div>

        <dl className="mt-4 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
          <Row label="Địa chỉ trụ sở" value={company.headquarters_address} />
          {company.website && <Row label="Website" value={company.website} />}
        </dl>
      </header>

      {company.description_html && (
        <section className="mt-4 rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-2 font-bold text-slate-800">Giới thiệu công ty</h2>
          <SafeHtml html={company.description_html} />
        </section>
      )}

      {company.addresses.length > 0 && (
        <section className="mt-4 rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-2 font-bold text-slate-800">Địa điểm làm việc</h2>
          <ul className="space-y-1 text-sm text-slate-600">
            {company.addresses.map((address) => (
              <li key={address.id}>
                {cities?.find((city) => city.id === address.city_id)?.name ??
                  `#${address.city_id}`}{' '}
                — {address.address_detail}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-4">
        <h2 className="mb-3 font-bold text-slate-800">
          Tin tuyển dụng đang mở ({company.open_jobs.length})
        </h2>
        {company.open_jobs.length === 0 ? (
          <EmptyState
            title="Công ty chưa có tin tuyển dụng nào"
            hint="Quay lại sau nhé, hoặc xem các công ty khác."
          />
        ) : (
          <div className="space-y-3">
            {company.open_jobs.map((job) => (
              <JobCard key={job.id} job={job} cities={cities} hideCompany />
            ))}
          </div>
        )}
      </section>
    </PublicShell>
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
