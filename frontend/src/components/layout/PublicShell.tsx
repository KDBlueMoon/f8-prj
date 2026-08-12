import type { ReactNode } from 'react'
import { AppHeader } from './AppHeader'

/**
 * Khung cho các trang công khai.
 *
 * Khác `PageShell` ở chỗ không áp đặt sẵn tiêu đề trang — trang chi tiết việc
 * làm và trang công ty tự dựng phần đầu riêng.
 */
export function PublicShell({
  children,
  width = 'wide',
}: {
  children: ReactNode
  width?: 'wide' | 'narrow'
}) {
  return (
    <div className="min-h-screen bg-slate-100">
      <AppHeader />
      <main className={`mx-auto px-4 py-6 ${width === 'wide' ? 'max-w-6xl' : 'max-w-4xl'}`}>
        {children}
      </main>
    </div>
  )
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
      <p className="font-medium text-slate-700">{title}</p>
      {hint && <p className="mt-1 text-sm text-slate-500">{hint}</p>}
    </div>
  )
}

export function Pagination({
  page,
  totalPages,
  onChange,
}: {
  page: number
  totalPages: number
  onChange: (page: number) => void
}) {
  if (totalPages <= 1) return null

  return (
    <div className="mt-6 flex items-center justify-center gap-3 text-sm">
      <button
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Trước
      </button>
      <span className="text-slate-600">
        Trang {page} / {totalPages}
      </span>
      <button
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
        className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Sau
      </button>
    </div>
  )
}
