import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { SelectField, TextField } from '@/components/ui/FormField'
import { TaxCodeLookupField } from '@/features/companies/TaxCodeLookupField'
import { apiGet } from '@/lib/apiClient'
import type { CategoryGroup } from '@/types/catalog'
import { COMPANY_SIZE_LABELS, type CompanySize } from '@/types/auth'
import { registerEmployer } from './api'
import { AuthCard } from './AuthCard'
import { employerRegisterSchema, type EmployerRegisterValues } from './schemas'
import { useAuthSubmit } from './useAuthSubmit'

const COMPANY_SIZES = Object.keys(COMPANY_SIZE_LABELS) as CompanySize[]

export default function RegisterEmployerPage() {
  const { data: categoryGroups } = useQuery({
    queryKey: ['categories'],
    queryFn: () => apiGet<CategoryGroup[]>('/categories'),
    // Danh mục gần như không đổi — khỏi gọi lại mỗi lần mở trang.
    staleTime: 60 * 60 * 1000,
  })

  const {
    register,
    handleSubmit,
    setError,
    setValue,
    watch,
    formState: { errors },
  } = useForm<EmployerRegisterValues>({
    resolver: zodResolver(employerRegisterSchema),
    defaultValues: {
      email: '',
      password: '',
      confirm_password: '',
      full_name: '',
      phone_number: '',
      company: {
        tax_code: '',
        company_name: '',
        international_name: '',
        short_name: '',
        director: '',
        headquarters_address: '',
        email: '',
        phone_number: '',
        company_size: '10-24',
        website: '',
        category_group_id: '',
      },
    },
  })

  const { formError, isSubmitting, submit } = useAuthSubmit<EmployerRegisterValues>()

  const onSubmit = handleSubmit((values) => submit(() => registerEmployer(values), setError))

  return (
    <AuthCard
      wide
      title="Đăng ký tài khoản nhà tuyển dụng"
      subtitle="Hồ sơ công ty sẽ được quản trị viên xét duyệt trước khi bạn đăng tin"
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
      <form onSubmit={onSubmit} noValidate className="space-y-8">
        <section className="space-y-4">
          <h2 className="border-b border-slate-200 pb-2 font-bold text-brand">
            1. Tài khoản đăng nhập
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Họ và tên"
              required
              autoComplete="name"
              error={errors.full_name?.message}
              {...register('full_name')}
            />
            <TextField
              label="Số điện thoại cá nhân"
              type="tel"
              autoComplete="tel"
              hint="Không bắt buộc"
              error={errors.phone_number?.message}
              {...register('phone_number')}
            />
            <TextField
              label="Email đăng nhập"
              type="email"
              required
              autoComplete="email"
              error={errors.email?.message}
              {...register('email')}
            />
            <div className="hidden sm:block" />
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
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="border-b border-slate-200 pb-2 font-bold text-brand">
            2. Thông tin doanh nghiệp
          </h2>
          <TaxCodeLookupField
            taxCode={watch('company.tax_code')}
            error={errors.company?.tax_code?.message}
            register={register('company.tax_code')}
            onFound={(info) => {
              // shouldValidate: xoá lỗi đỏ còn sót từ lần submit trước ngay khi
              // giá trị mới được điền vào.
              const options = { shouldValidate: true, shouldDirty: true }
              setValue('company.company_name', info.company_name, options)
              setValue('company.international_name', info.international_name ?? '', options)
              setValue('company.short_name', info.short_name ?? '', options)
              if (info.headquarters_address) {
                setValue('company.headquarters_address', info.headquarters_address, options)
              }
            }}
          />
          <TextField
            label="Tên công ty"
            required
            error={errors.company?.company_name?.message}
            {...register('company.company_name')}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Tên quốc tế"
              hint="Không bắt buộc"
              error={errors.company?.international_name?.message}
              {...register('company.international_name')}
            />
            <TextField
              label="Tên viết tắt"
              hint="Không bắt buộc"
              error={errors.company?.short_name?.message}
              {...register('company.short_name')}
            />
            <TextField
              label="Người đại diện"
              required
              error={errors.company?.director?.message}
              {...register('company.director')}
            />
            <SelectField
              label="Quy mô"
              required
              error={errors.company?.company_size?.message}
              {...register('company.company_size')}
            >
              {COMPANY_SIZES.map((size) => (
                <option key={size} value={size}>
                  {COMPANY_SIZE_LABELS[size]}
                </option>
              ))}
            </SelectField>
          </div>
          <TextField
            label="Địa chỉ trụ sở"
            required
            error={errors.company?.headquarters_address?.message}
            {...register('company.headquarters_address')}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Email công ty"
              type="email"
              required
              error={errors.company?.email?.message}
              {...register('company.email')}
            />
            <TextField
              label="Số điện thoại công ty"
              type="tel"
              required
              error={errors.company?.phone_number?.message}
              {...register('company.phone_number')}
            />
            <TextField
              label="Website"
              hint="Không bắt buộc"
              placeholder="https://congty.vn"
              error={errors.company?.website?.message}
              {...register('company.website')}
            />
            <SelectField
              label="Lĩnh vực hoạt động"
              hint="Không bắt buộc"
              error={errors.company?.category_group_id?.message}
              {...register('company.category_group_id')}
            >
              <option value="">-- Chọn lĩnh vực --</option>
              {categoryGroups?.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.group_name}
                </option>
              ))}
            </SelectField>
          </div>
        </section>

        <Button type="submit" fullWidth loading={isSubmitting}>
          Hoàn tất đăng ký
        </Button>
      </form>
    </AuthCard>
  )
}
