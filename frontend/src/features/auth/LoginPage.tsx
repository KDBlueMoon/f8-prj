import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { TextField } from '@/components/ui/FormField'
import { login } from './api'
import { AuthCard } from './AuthCard'
import { loginSchema, type LoginValues } from './schemas'
import { useAuthSubmit } from './useAuthSubmit'

export default function LoginPage() {
  const [searchParams] = useSearchParams()
  // Người dùng bị chặn ở trang cần đăng nhập -> quay lại đúng chỗ đó sau khi vào.
  const nextPath = searchParams.get('next') ?? undefined

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const { formError, isSubmitting, submit } = useAuthSubmit<LoginValues>(nextPath)

  const onSubmit = handleSubmit((values) => submit(() => login(values), setError))

  return (
    <AuthCard
      title="Đăng nhập"
      subtitle="Chào mừng bạn quay lại TopCV"
      error={formError}
      footer={
        <>
          Chưa có tài khoản?{' '}
          <Link to="/dang-ky" className="font-semibold text-brand hover:underline">
            Đăng ký ứng viên
          </Link>
          {' · '}
          <Link to="/dang-ky/nha-tuyen-dung" className="font-semibold text-brand hover:underline">
            Đăng ký nhà tuyển dụng
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          required
          placeholder="ban@email.com"
          error={errors.email?.message}
          {...register('email')}
        />
        <TextField
          label="Mật khẩu"
          type="password"
          autoComplete="current-password"
          required
          error={errors.password?.message}
          {...register('password')}
        />
        <Button type="submit" fullWidth loading={isSubmitting}>
          Đăng nhập
        </Button>
      </form>
    </AuthCard>
  )
}
