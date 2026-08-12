import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'
import { forwardRef } from 'react'

interface FieldWrapperProps {
  label: string
  error?: string
  required?: boolean
  hint?: ReactNode
  children: ReactNode
}

function FieldWrapper({ label, error, required, hint, children }: FieldWrapperProps) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </span>
      {children}
      {/* role=alert để trình đọc màn hình thông báo lỗi ngay khi xuất hiện. */}
      {error ? (
        <span role="alert" className="mt-1 block text-xs text-red-600">
          {error}
        </span>
      ) : (
        hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>
      )}
    </label>
  )
}

const controlClass = (hasError: boolean) =>
  [
    'w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition',
    'focus:ring-2 focus:ring-brand/20',
    hasError ? 'border-red-400 focus:border-red-500' : 'border-slate-300 focus:border-brand',
  ].join(' ')

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> &
  Omit<FieldWrapperProps, 'children'>

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, error, required, hint, ...inputProps },
  ref,
) {
  return (
    <FieldWrapper label={label} error={error} required={required} hint={hint}>
      <input
        ref={ref}
        aria-invalid={Boolean(error)}
        className={controlClass(Boolean(error))}
        {...inputProps}
      />
    </FieldWrapper>
  )
})

type SelectFieldProps = SelectHTMLAttributes<HTMLSelectElement> &
  Omit<FieldWrapperProps, 'children'>

export const SelectField = forwardRef<HTMLSelectElement, SelectFieldProps>(function SelectField(
  { label, error, required, hint, children, ...selectProps },
  ref,
) {
  return (
    <FieldWrapper label={label} error={error} required={required} hint={hint}>
      <select
        ref={ref}
        aria-invalid={Boolean(error)}
        className={`${controlClass(Boolean(error))} bg-white`}
        {...selectProps}
      >
        {children}
      </select>
    </FieldWrapper>
  )
})
