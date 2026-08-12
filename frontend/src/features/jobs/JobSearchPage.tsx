import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { EmptyState, Pagination, PublicShell } from '@/components/layout/PublicShell'
import { Button } from '@/components/ui/Button'
import { listPublicJobs } from '@/features/jobs/api'
import { JobCard } from '@/features/jobs/JobCard'
import { useJobFilters } from '@/features/jobs/useJobFilters'
import { apiGet } from '@/lib/apiClient'
import type { CategoryGroup, City } from '@/types/catalog'
import {
  EXPERIENCE_LABELS,
  JOB_SORT_LABELS,
  JOB_TYPE_LABELS,
  type JobSort,
} from '@/types/job'

/** Mốc lương gợi ý, đơn vị đồng. Người dùng chọn mốc thay vì tự gõ số. */
const SALARY_STEPS = [10_000_000, 15_000_000, 20_000_000, 30_000_000, 50_000_000]

const CATALOG_STALE_TIME = 60 * 60 * 1000

export default function JobSearchPage() {
  const { filters, setFilter, setPage, reset, activeCount } = useJobFilters()
  const [keyword, setKeyword] = useState(filters.q ?? '')

  // Người dùng bấm back/forward hoặc mở link có sẵn ?q= thì ô tìm kiếm phải
  // hiện đúng từ khoá đang áp dụng.
  useEffect(() => setKeyword(filters.q ?? ''), [filters.q])

  const { data: cities } = useQuery({
    queryKey: ['cities'],
    queryFn: () => apiGet<City[]>('/cities'),
    staleTime: CATALOG_STALE_TIME,
  })
  const { data: groups } = useQuery({
    queryKey: ['categories'],
    queryFn: () => apiGet<CategoryGroup[]>('/categories'),
    staleTime: CATALOG_STALE_TIME,
  })

  const { data, isPending, isError } = useQuery({
    queryKey: ['publicJobs', filters],
    queryFn: () => listPublicJobs(filters),
  })

  return (
    <PublicShell>
      <form
        className="mb-5 flex flex-col gap-2 rounded-xl border border-slate-200 bg-white p-4 sm:flex-row"
        onSubmit={(event) => {
          event.preventDefault()
          setFilter({ q: keyword.trim() || undefined })
        }}
      >
        <input
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
          placeholder="Tìm theo tên công việc, vị trí…"
          aria-label="Từ khoá tìm việc"
          className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none focus:border-brand"
        />
        <Button type="submit">Tìm việc làm</Button>
      </form>

      <div className="gap-5 lg:flex">
        <aside className="mb-5 shrink-0 lg:mb-0 lg:w-64">
          <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-slate-800">Bộ lọc</h2>
              {activeCount > 0 && (
                <button
                  onClick={reset}
                  className="text-xs font-medium text-brand hover:underline"
                >
                  Xoá lọc ({activeCount})
                </button>
              )}
            </div>

            <FilterSelect
              label="Tỉnh/thành"
              value={filters.city_id === undefined ? '' : String(filters.city_id)}
              onChange={(value) => setFilter({ city_id: value ? Number(value) : undefined })}
              options={(cities ?? []).map((city) => [String(city.id), city.name])}
            />

            <FilterSelect
              label="Nhóm ngành"
              value={filters.group_id ?? ''}
              onChange={(value) =>
                // Đổi nhóm ngành thì ngành nghề cụ thể đang chọn có thể không
                // còn thuộc nhóm mới — bỏ luôn để không ra kết quả rỗng khó hiểu.
                setFilter({ group_id: value || undefined, category_id: undefined })
              }
              options={(groups ?? []).map((group) => [group.id, group.group_name])}
            />

            <FilterSelect
              label="Ngành nghề"
              value={filters.category_id ?? ''}
              onChange={(value) => setFilter({ category_id: value || undefined })}
              options={(groups ?? [])
                .filter((group) => !filters.group_id || group.id === filters.group_id)
                .flatMap((group) =>
                  group.categories.map(
                    (category) => [category.id, category.name] as [string, string],
                  ),
                )}
            />

            <FilterSelect
              label="Hình thức làm việc"
              value={filters.job_type ?? ''}
              onChange={(value) => setFilter({ job_type: value || undefined })}
              options={Object.entries(JOB_TYPE_LABELS)}
            />

            <FilterSelect
              label="Kinh nghiệm"
              value={filters.experience_level ?? ''}
              onChange={(value) => setFilter({ experience_level: value || undefined })}
              options={Object.entries(EXPERIENCE_LABELS)}
            />

            <FilterSelect
              label="Mức lương từ"
              value={filters.salary_min === undefined ? '' : String(filters.salary_min)}
              onChange={(value) => setFilter({ salary_min: value ? Number(value) : undefined })}
              options={SALARY_STEPS.map(
                (step) => [String(step), `${step / 1_000_000} triệu trở lên`] as [string, string],
              )}
              hint="Tin lương thoả thuận sẽ không nằm trong kết quả"
            />

            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={filters.is_hot === true}
                onChange={(event) => setFilter({ is_hot: event.target.checked || undefined })}
                className="h-4 w-4 accent-[var(--color-brand)]"
              />
              Chỉ hiện tin nổi bật
            </label>
          </div>
        </aside>

        <section className="min-w-0 flex-1">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-slate-600">
              {isPending
                ? 'Đang tìm…'
                : `${data?.meta.total ?? 0} việc làm phù hợp`}
            </p>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              Sắp xếp
              <select
                value={filters.sort}
                onChange={(event) => setFilter({ sort: event.target.value as JobSort })}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm outline-none focus:border-brand"
              >
                {Object.entries(JOB_SORT_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {isError && (
            <EmptyState
              title="Không tải được danh sách việc làm"
              hint="Vui lòng thử lại sau ít phút."
            />
          )}

          {!isError && data?.items.length === 0 && (
            <EmptyState
              title="Không có việc làm nào khớp bộ lọc"
              hint="Thử bỏ bớt điều kiện hoặc đổi từ khoá tìm kiếm."
            />
          )}

          <div className="space-y-3">
            {data?.items.map((job) => <JobCard key={job.id} job={job} cities={cities} />)}
          </div>

          {data && (
            <Pagination
              page={data.meta.page}
              totalPages={data.meta.total_pages}
              onChange={setPage}
            />
          )}
        </section>
      </div>
    </PublicShell>
  )
}

interface FilterSelectProps {
  label: string
  value: string
  onChange: (value: string) => void
  options: Array<[string, string]>
  hint?: string
}

function FilterSelect({ label, value, onChange, options, hint }: FilterSelectProps) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-600">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-brand"
      >
        <option value="">Tất cả</option>
        {options.map(([optionValue, optionLabel]) => (
          <option key={optionValue} value={optionValue}>
            {optionLabel}
          </option>
        ))}
      </select>
      {hint && <span className="mt-1 block text-[11px] text-slate-500">{hint}</span>}
    </label>
  )
}
