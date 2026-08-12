import { useState } from 'react'
import type { FieldValues, Path, UseFormSetError } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '@/lib/apiClient'
import { useAuthStore } from '@/stores/authStore'
import type { LoginResponse } from '@/types/auth'

/** Nơi điều hướng tới sau khi đăng nhập, tuỳ vai trò. */
export const HOME_BY_ROLE = {
  CANDIDATE: '/ung-vien/ho-so',
  EMPLOYER: '/ntd/tong-quan',
  ADMIN: '/admin/nguoi-dung',
} as const

interface UseAuthSubmitResult<TValues extends FieldValues> {
  formError: string | null
  isSubmitting: boolean
  submit: (
    action: () => Promise<LoginResponse>,
    setError: UseFormSetError<TValues>,
  ) => Promise<void>
}

/**
 * Gói phần lặp lại của 3 form auth: gọi API, lưu phiên, điều hướng, và rải lỗi
 * 422 của backend vào đúng ô nhập thay vì chỉ hiện một dòng lỗi chung.
 */
export function useAuthSubmit<TValues extends FieldValues>(
  redirectTo?: string,
): UseAuthSubmitResult<TValues> {
  const navigate = useNavigate()
  const setSession = useAuthStore((state) => state.setSession)
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const submit = async (
    action: () => Promise<LoginResponse>,
    setError: UseFormSetError<TValues>,
  ): Promise<void> => {
    setFormError(null)
    setIsSubmitting(true)
    try {
      const session = await action()
      setSession(session)
      navigate(redirectTo ?? HOME_BY_ROLE[session.user.role], { replace: true })
    } catch (error) {
      if (error instanceof ApiError && error.fieldErrors) {
        for (const [field, message] of Object.entries(error.fieldErrors)) {
          setError(field as Path<TValues>, { type: 'server', message })
        }
      }
      setFormError(
        error instanceof ApiError ? error.message : 'Đã có lỗi xảy ra, vui lòng thử lại.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return { formError, isSubmitting, submit }
}
