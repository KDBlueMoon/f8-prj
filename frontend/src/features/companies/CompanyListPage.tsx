import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { EmptyState, Pagination, PublicShell } from '@/components/layout/PublicShell'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { listPublicCompanies } from '@/features/companies/api'
import { CompanyLogo } from '@/features/jobs/JobCard'
import { apiGet } from '@/lib/apiClient'
import { COMPANY_SIZE_LABELS } from '@/types/auth'
import type { CategoryGroup } from '@/types/catalog'

export default function CompanyListPage() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? undefined
  const groupId = params.get('group_id') ?? undefined
  const page = Number(params.get('page') ?? 1)
  const [keyword, setKeyword] = useState(q ?? '')

  useEffect(() => setKeyword(q ?? ''), [q])

  const { data: groups } = useQuery({
    queryKey: ['categories'],
    queryFn: () => apiGet<CategoryGroup[]>('/categories'),
    staleTime: 60 * 60 * 1000,
  })
  const { data, isPending } = useQuery({
    queryKey: ['publicCompanies', q, groupId, page],
    queryFn: () => listPublicCompanies({ q, group_id: groupId, page }),
  })

  /** Đổi bộ lọc thì về trang 1 — trang 3 của kết quả cũ không còn ý nghĩa. */
  const updateParam = (key: string, value: string | undefined) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    next.delete('page')
    setParams(next)
  }

  const setPage = (nextPage: number) => {
    const next = new URLSearchParams(params)
    if (nextPage <= 1) next.delete('page')
    else next.set('page', String(nextPage))
    setParams(next)
  }

  return (
    <PublicShell>
      <h1 className="text-xl font-bold text-slate-900">Danh sách công ty</h1>
      <p className="mt-0.5 text-sm text-slate-500">
        Các công ty đã được kiểm duyệt hồ sơ trên hệ thống.
      </p>

      <div className="mt-4 flex flex-col gap-2 rounded-xl border border-slate-200 bg-white p-4 sm:flex-row">
        <form
          className="flex flex-1 gap-2"
          onSubmit={(event) => {
            event.preventDefault()
            updateParam('q', keyword.trim() || undefined)
          }}
        >
          <input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="Tìm theo tên công ty"
            aria-label="Từ khoá tìm công ty"
            className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none focus:border-brand"
          />
          <Button type="submit">Tìm</Button>
        </form>

        <select
          value={groupId ?? ''}
          onChange={(event) => updateParam('group_id', event.target.value || undefined)}
          aria-label="Lọc theo nhóm ngành"
          className="rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand sm:w-56"
        >
          <option value="">Tất cả nhóm ngành</option>
          {groups?.map((group) => (
            <option key={group.id} value={group.id}>
              {group.group_name}
            </option>
          ))}
        </select>
      </div>

      <p className="mt-4 text-sm text-slate-600">
        {isPending ? 'Đang tải…' : `${data?.meta.total ?? 0} công ty`}
      </p>

      {data?.items.length === 0 && (
        <div className="mt-3">
          <EmptyState title="Không tìm thấy công ty nào" hint="Thử đổi từ khoá hoặc nhóm ngành." />
        </div>
      )}

      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {data?.items.map((company) => (
          <Link
            key={company.id}
            to={`/cong-ty/${company.slug}`}
            className="rounded-xl border border-slate-200 bg-white p-4 transition hover:border-brand"
          >
            <div className="flex gap-3">
              <CompanyLogo company={company} />
              <div className="min-w-0">
                <p className="font-semibold leading-snug text-slate-900">
                  {company.short_name ?? company.company_name}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">
                  {COMPANY_SIZE_LABELS[company.company_size]}
                </p>
                {company.verification_tier === 'VERIFIED' && (
                  <div className="mt-1.5">
                    <Badge tone="success">✔ Đã xác thực</Badge>
                  </div>
                )}
              </div>
            </div>
            <p className="mt-3 text-sm font-medium text-brand">
              {company.open_job_count > 0
                ? `${company.open_job_count} tin đang tuyển`
                : 'Chưa có tin tuyển dụng'}
            </p>
          </Link>
        ))}
      </div>

      {data && (
        <Pagination page={data.meta.page} totalPages={data.meta.total_pages} onChange={setPage} />
      )}
    </PublicShell>
  )
}
