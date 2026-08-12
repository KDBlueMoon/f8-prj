import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

interface AuthCardProps {
  title: string
  subtitle?: string
  error?: string | null
  footer?: ReactNode
  wide?: boolean
  children: ReactNode
}

export function AuthCard({ title, subtitle, error, footer, wide, children }: AuthCardProps) {
  return (
    <div className="min-h-screen bg-slate-100 px-4 py-10">
      <div className={`mx-auto ${wide ? 'max-w-3xl' : 'max-w-md'}`}>
        <div className="mb-6 text-center">
          <Link to="/" className="text-2xl font-black text-brand">
            Top<span className="text-slate-800">CV</span>
          </Link>
          <h1 className="mt-3 text-xl font-bold text-slate-900">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6">
          {error && (
            <div
              role="alert"
              className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {error}
            </div>
          )}
          {children}
        </div>

        {footer && <div className="mt-4 text-center text-sm text-slate-600">{footer}</div>}
      </div>
    </div>
  )
}
