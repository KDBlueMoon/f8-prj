import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { AppHeader } from '@/components/layout/AppHeader'
import { apiGet } from '@/lib/apiClient'
import { useAuthStore } from '@/stores/authStore'
import { HOME_BY_ROLE } from '@/features/auth/useAuthSubmit'
import type { CategoryGroup, City } from '@/types/catalog'

/** Trang chủ tạm của P1. Danh sách việc làm thật sẽ thay thế ở P4. */
export default function HomePage() {
  const user = useAuthStore((state) => state.user)

  const { data: cities } = useQuery({
    queryKey: ['cities'],
    queryFn: () => apiGet<City[]>('/cities'),
    staleTime: 60 * 60 * 1000,
  })
  const { data: groups } = useQuery({
    queryKey: ['categories'],
    queryFn: () => apiGet<CategoryGroup[]>('/categories'),
    staleTime: 60 * 60 * 1000,
  })

  return (
    <div className="min-h-screen bg-slate-100">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-2xl font-bold text-slate-900">Nền tảng tuyển dụng TopCV</h1>
        <p className="mt-1 text-sm text-slate-500">
          Phase P1 — đã có đăng ký, đăng nhập và phân quyền.
        </p>

        {user ? (
          <Link
            to={HOME_BY_ROLE[user.role]}
            className="mt-4 inline-block font-semibold text-brand hover:underline"
          >
            Vào khu vực của tôi →
          </Link>
        ) : (
          <div className="mt-4 flex gap-3 text-sm">
            <Link to="/dang-ky" className="font-semibold text-brand hover:underline">
              Đăng ký ứng viên
            </Link>
            <span className="text-slate-300">|</span>
            <Link
              to="/dang-ky/nha-tuyen-dung"
              className="font-semibold text-brand hover:underline"
            >
              Đăng ký nhà tuyển dụng
            </Link>
          </div>
        )}

        <section className="mt-8">
          <h2 className="mb-3 font-bold text-slate-800">
            Ngành nghề {groups && <span className="text-slate-400">({groups.length} nhóm)</span>}
          </h2>
          <ul className="space-y-3">
            {groups?.map((group) => (
              <li key={group.id} className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="font-semibold text-slate-800">{group.group_name}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {group.categories.map((category) => (
                    <span
                      key={category.id}
                      className="rounded bg-brand-light px-2 py-1 text-xs text-brand-dark"
                    >
                      {category.name}
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-8">
          <h2 className="mb-3 font-bold text-slate-800">
            Tỉnh/thành {cities && <span className="text-slate-400">({cities.length})</span>}
          </h2>
          <div className="flex flex-wrap gap-2">
            {cities?.map((city) => (
              <span
                key={city.id}
                className={`rounded border px-2 py-1 text-xs ${
                  city.is_municipality
                    ? 'border-brand bg-brand-light font-medium text-brand-dark'
                    : 'border-slate-200 bg-white text-slate-600'
                }`}
              >
                {city.name}
              </span>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
