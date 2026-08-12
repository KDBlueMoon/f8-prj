import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { TextField } from '@/components/ui/FormField'
import { registerCandidate } from './api'
import { AuthCard } from './AuthCard'
import { candidateRegisterSchema, type CandidateRegisterValues } from './schemas'
import { useAuthSubmit } from './useAuthSubmit'

export default function RegisterCandidatePage() {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<CandidateRegisterValues>({
    resolver: zodResolver(candidateRegisterSchema),
    defaultValues: {
      email: '',
      password: '',
      confirm_password: '',
      full_name: '',
      phone_number: '',
    },
  })

  const { formError, isSubmitting, submit } = useAuthSubmit<CandidateRegisterValues>()

  const onSubmit = handleSubmit((values) => submit(() => registerCandidate(values), setError))

  return (
    <AuthCard
      title="Đăng ký tài khoản ứng viên"
      subtitle="Tạo tài khoản để ứng tuyển và theo dõi hồ sơ"
      error={formError}
      footer={
        <>
          Đã có tài khoản?{' '}
          <Link to="/dang-nhap" className="font-semibold text-brand hover:underline">
            Đăng nhập
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <TextField
          label="Họ và tên"
          required
          autoComplete="name"
          placeholder="Nguyễn Văn A"
          error={errors.full_name?.message}
          {...register('full_name')}
        />
        <TextField
          label="Email"
          type="email"
          required
          autoComplete="email"
          placeholder="ban@email.com"
          error={errors.email?.message}
          {...register('email')}
        />
        <TextField
          label="Số điện thoại"
          type="tel"
          autoComplete="tel"
          placeholder="0901234567"
          hint="Không bắt buộc"
          error={errors.phone_number?.message}
          {...register('phone_number')}
        />
        <TextField
          label="Mật khẩu"
          type="password"
          required
          autoComplete="new-password"
          hint="Tối thiểu 8 ký tự, có cả chữ và số"
          error={errors.password?.message}
          {...register('password')}
        />
        <TextField
          label="Nhập lại mật khẩu"
          type="password"
          required
          autoComplete="new-password"
          error={errors.confirm_password?.message}
          {...register('confirm_password')}
        />
        <Button type="submit" fullWidth loading={isSubmitting}>
          Đăng ký
        </Button>
      </form>
    </AuthCard>
  )
}
