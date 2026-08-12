import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AppHeader } from '@/components/layout/AppHeader'
import { Button } from '@/components/ui/Button'
import { listPublicJobs } from '@/features/jobs/api'
import { JobCard } from '@/features/jobs/JobCard'
import { apiGet } from '@/lib/apiClient'
import { buildQuery } from '@/lib/apiClient'
import type { CategoryGroup, City } from '@/types/catalog'

const FEATURED_JOB_COUNT = 6
const CATALOG_STALE_TIME = 60 * 60 * 1000

export default function HomePage() {
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')
  const [cityId, setCityId] = useState('')

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

  const { data: latest } = useQuery({
    queryKey: ['publicJobs', 'home'],
    queryFn: () => listPublicJobs({ page_size: FEATURED_JOB_COUNT, sort: 'newest' }),
  })

  return (
    <div className="min-h-screen bg-slate-100">
      <AppHeader />

      <section className="bg-brand-dark py-10">
        <div className="mx-auto max-w-6xl px-4">
          <h1 className="text-2xl font-bold text-white sm:text-3xl">
            Tìm việc làm phù hợp với bạn
          </h1>
          <p className="mt-1 text-sm text-white/80">
            Hàng nghìn tin tuyển dụng từ các công ty đã được kiểm duyệt hồ sơ.
          </p>

          <form
            className="mt-5 flex flex-col gap-2 rounded-xl bg-white p-3 sm:flex-row"
            onSubmit={(event) => {
              event.preventDefault()
              // Đẩy điều kiện lên URL của trang tìm việc thay vì giữ trong state:
              // kết quả tìm kiếm chia sẻ được và bấm back quay lại đúng chỗ.
              navigate(
                `/viec-lam${buildQuery({ q: keyword.trim(), city_id: cityId })}`,
              )
            }}
          >
            <input
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="Vị trí muốn ứng tuyển, VD: lập trình viên"
              aria-label="Từ khoá tìm việc"
              className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 text-sm outline-none focus:border-brand"
            />
            <select
              value={cityId}
              onChange={(event) => setCityId(event.target.value)}
              aria-label="Tỉnh/thành"
              className="rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand sm:w-48"
            >
              <option value="">Tất cả tỉnh/thành</option>
              {cities?.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>
            <Button type="submit">Tìm kiếm</Button>
          </form>
        </div>
      </section>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-bold text-slate-800">Việc làm mới nhất</h2>
            <Link to="/viec-lam" className="text-sm font-medium text-brand hover:underline">
              Xem tất cả →
            </Link>
          </div>

          {latest?.items.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
              Chưa có tin tuyển dụng nào được đăng.
            </p>
          ) : (
            <div className="grid gap-3 lg:grid-cols-2">
              {latest?.items.map((job) => <JobCard key={job.id} job={job} cities={cities} />)}
            </div>
          )}
        </section>

        <section className="mt-10">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-bold text-slate-800">Ngành nghề nổi bật</h2>
            <Link to="/cong-ty" className="text-sm font-medium text-brand hover:underline">
              Xem các công ty →
            </Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {groups?.map((group) => (
              <div key={group.id} className="rounded-xl border border-slate-200 bg-white p-4">
                <Link
                  to={`/viec-lam?group_id=${group.id}`}
                  className="font-semibold text-slate-800 hover:text-brand"
                >
                  {group.group_name}
                </Link>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {group.categories.map((category) => (
                    <Link
                      key={category.id}
                      to={`/viec-lam?category_id=${category.id}`}
                      className="rounded bg-brand-light px-2 py-1 text-xs text-brand-dark hover:underline"
                    >
                      {category.name}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
