import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { ApiError } from '@/lib/apiClient'
import type { TaxCodeLookup } from '@/types/company'
import { lookupTaxCode } from './api'

interface TaxCodeLookupFieldProps {
  taxCode: string
  error?: string
  register: Record<string, unknown>
  onFound: (info: TaxCodeLookup) => void
}

type LookupState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'found' }
  | { kind: 'failed'; message: string; canContinueManually: boolean }

/**
 * Ô nhập mã số thuế kèm nút tra cứu VietQR.
 *
 * VietQR chỉ trả tên công ty, tên quốc tế, tên viết tắt và địa chỉ trụ sở.
 * Người đại diện, số điện thoại, email, quy mô và lĩnh vực KHÔNG có — người
 * dùng phải tự nhập, nên giao diện phải nói rõ điều đó thay vì để họ tưởng
 * tra cứu xong là điền hết.
 */
export function TaxCodeLookupField({
  taxCode,
  error,
  register,
  onFound,
}: TaxCodeLookupFieldProps) {
  const [state, setState] = useState<LookupState>({ kind: 'idle' })

  const handleLookup = async () => {
    const cleaned = taxCode.trim()
    if (!/^\d{10}$|^\d{13}$/.test(cleaned)) {
      setState({
        kind: 'failed',
        message: 'Mã số thuế phải gồm 10 hoặc 13 chữ số.',
        canContinueManually: false,
      })
      return
    }

    setState({ kind: 'loading' })
    try {
      onFound(await lookupTaxCode(cleaned))
      setState({ kind: 'found' })
    } catch (caught) {
      const apiError = caught instanceof ApiError ? caught : null
      setState({
        kind: 'failed',
        message: apiError?.message ?? 'Không tra cứu được mã số thuế.',
        // VietQR chết thì vẫn cho đăng ký, chỉ là phải nhập tay.
        canContinueManually: apiError?.code === 'TAX_LOOKUP_UNAVAILABLE',
      })
    }
  }

  return (
    <div>
      <label className="block">
        <span className="mb-1.5 block text-sm font-medium text-slate-700">
          Mã số thuế<span className="text-red-500"> *</span>
        </span>
        <div className="flex gap-2">
          <input
            inputMode="numeric"
            placeholder="0108888888"
            aria-invalid={Boolean(error)}
            className={[
              'w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition',
              'focus:ring-2 focus:ring-brand/20',
              error ? 'border-red-400' : 'border-slate-300 focus:border-brand',
            ].join(' ')}
            {...register}
          />
          <Button
            type="button"
            variant="secondary"
            onClick={handleLookup}
            loading={state.kind === 'loading'}
            className="whitespace-nowrap"
          >
            Tra cứu
          </Button>
        </div>
      </label>

      {error && (
        <p role="alert" className="mt-1 text-xs text-red-600">
          {error}
        </p>
      )}

      {state.kind === 'found' && (
        <p className="mt-1.5 text-xs text-brand-dark">
          ✔ Đã điền <strong>tên công ty, tên quốc tế, tên viết tắt và địa chỉ trụ sở</strong> từ
          VietQR. Người đại diện, liên hệ, quy mô và lĩnh vực vui lòng nhập tay.
        </p>
      )}

      {state.kind === 'failed' && (
        <p
          role="alert"
          className={`mt-1.5 text-xs ${state.canContinueManually ? 'text-amber-700' : 'text-red-600'}`}
        >
          {state.message}
          {state.canContinueManually && ' Bạn vẫn có thể nhập thủ công và tiếp tục đăng ký.'}
        </p>
      )}
    </div>
  )
}
