import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { apiGet } from '@/lib/apiClient'
import type { CategoryGroup, City } from '@/types/catalog'

interface HealthResponse {
  status: string
  database: string
}

type LoadState =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; health: HealthResponse; cities: City[]; groups: CategoryGroup[] }

/**
 * Màn hình kiểm tra hạ tầng của phase P0.
 * Sẽ được thay bằng router + trang thật ở P1 trở đi.
 */
export default function App() {
  const [state, setState] = useState<LoadState>({ kind: 'loading' })

  useEffect(() => {
    let cancelled = false

    Promise.all([
      apiGet<HealthResponse>('/health'),
      apiGet<City[]>('/cities'),
      apiGet<CategoryGroup[]>('/categories'),
    ])
      .then(([health, cities, groups]) => {
        if (!cancelled) setState({ kind: 'ready', health, cities, groups })
      })
      .catch((error: unknown) => {
        if (cancelled) return
        const message = error instanceof Error ? error.message : 'Lỗi không xác định'
        setState({ kind: 'error', message })
      })

    // Tránh setState sau khi component đã unmount (StrictMode chạy effect 2 lần).
    return () => {
      cancelled = true
    }
  }, [])

  if (state.kind === 'loading') {
    return <Shell><p className="text-slate-500">Đang tải dữ liệu…</p></Shell>
  }

  if (state.kind === 'error') {
    return (
      <Shell>
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-700">
          <p className="font-semibold">Không gọi được API</p>
          <p className="mt-1 text-sm">{state.message}</p>
          <p className="mt-2 text-sm">Kiểm tra service backend đã chạy chưa: <code>docker compose ps</code></p>
        </div>
      </Shell>
    )
  }

  const { health, cities, groups } = state
  const totalCategories = groups.reduce((sum, group) => sum + group.categories.length, 0)

  return (
    <Shell>
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Backend" value={health.status} hint={`DB: ${health.database}`} />
        <Stat label="Tỉnh/thành" value={String(cities.length)} hint="sau sáp nhập 2025" />
        <Stat label="Ngành nghề" value={String(totalCategories)} hint={`${groups.length} nhóm ngành`} />
      </div>

      <section className="mt-8">
        <h2 className="mb-3 font-bold text-slate-800">Cây ngành nghề</h2>
        <ul className="space-y-3">
          {groups.map((group) => (
            <li key={group.id} className="rounded-lg border bg-white p-4">
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
        <h2 className="mb-3 font-bold text-slate-800">Tỉnh/thành ({cities.length})</h2>
        <div className="flex flex-wrap gap-2">
          {cities.map((city) => (
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
    </Shell>
  )
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="mx-auto max-w-4xl">
        <header className="mb-6">
          <h1 className="text-2xl font-black text-brand">
            Top<span className="text-slate-800">CV</span> Clone
          </h1>
          <p className="text-sm text-slate-500">Phase P0 — kiểm tra hạ tầng</p>
        </header>
        {children}
      </div>
    </div>
  )
}

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-lg border bg-white p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-brand">{value}</p>
      <p className="text-xs text-slate-400">{hint}</p>
    </div>
  )
}
