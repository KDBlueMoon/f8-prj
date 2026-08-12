import type { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  loading?: boolean
  fullWidth?: boolean
}

const VARIANT_CLASSES = {
  primary: 'bg-brand text-white hover:bg-brand-dark',
  secondary: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
  ghost: 'text-slate-600 hover:text-brand',
} as const

export function Button({
  variant = 'primary',
  loading = false,
  fullWidth = false,
  disabled,
  children,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      // Chặn bấm nhiều lần khi đang gửi request — tránh tạo trùng bản ghi.
      disabled={disabled || loading}
      aria-busy={loading}
      className={[
        'rounded-lg px-5 py-2.5 text-sm font-semibold transition',
        'disabled:cursor-not-allowed disabled:opacity-50',
        VARIANT_CLASSES[variant],
        fullWidth ? 'w-full' : '',
        className,
      ].join(' ')}
      {...props}
    >
      {loading ? 'Đang xử lý…' : children}
    </button>
  )
}
