import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { PageShell } from '@/components/layout/PageShell'
import { Badge, CompanyStatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { SelectField, TextField } from '@/components/ui/FormField'
import { addAddress, deleteAddress, getMyCompany, updateMyCompany } from '@/features/companies/api'
import { ApiError, apiGet } from '@/lib/apiClient'
import { useAuthStore } from '@/stores/authStore'
import { COMPANY_SIZE_LABELS, type CompanySize } from '@/types/auth'
import type { City } from '@/types/catalog'
import type { Company } from '@/types/company'

const COMPANY_SIZES = Object.keys(COMPANY_SIZE_LABELS) as CompanySize[]

/** Chỉ những trường nhà tuyển dụng được tự sửa. Mã số thuế không nằm trong đây. */
const EDITABLE_FIELDS = [
  'company_name',
  'international_name',
  'short_name',
  'director',
  'headquarters_address',
  'email',
  'phone_number',
  'website',
  'company_size',
] as const

type EditableForm = Record<(typeof EDITABLE_FIELDS)[number], string>

function toForm(company: Company): EditableForm {
  return {
    company_name: company.company_name,
    international_name: company.international_name ?? '',
    short_name: company.short_name ?? '',
    director: company.director,
    headquarters_address: company.headquarters_address,
    email: company.email,
    phone_number: company.phone_number,
    website: company.website ?? '',
    company_size: company.company_size,
  }
}

export default function CompanyProfilePage() {
  const queryClient = useQueryClient()
  const setSession = useAuthStore((state) => state.setSession)
  const [form, setForm] = useState<EditableForm | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  const { data: company, isPending } = useQuery({
    queryKey: ['employer', 'company'],
    queryFn: getMyCompany,
  })
  const { data: cities } = useQuery({
    queryKey: ['cities'],
    queryFn: () => apiGet<City[]>('/cities'),
    staleTime: 60 * 60 * 1000,
  })

  // Nạp dữ liệu vào form một lần khi tải xong; sau đó form tự quản lý để không
  // đè lên những gì người dùng đang gõ dở.
  useEffect(() => {
    if (company && form === null) setForm(toForm(company))
  }, [company, form])

  const saveMutation = useMutation({
    mutationFn: (values: EditableForm) =>
      updateMyCompany({
        ...values,
        international_name: values.international_name || null,
        short_name: values.short_name || null,
        website: values.website || null,
      } as Partial<Company>),
    onSuccess: (updated) => {
      queryClient.setQueryData(['employer', 'company'], updated)
      setForm(toForm(updated))
      setSaveError(null)
      setSaved(true)
      // Header và banner đọc trạng thái công ty từ store, phải cập nhật theo.
      const { accessToken, user } = useAuthStore.getState()
      if (accessToken && user) {
        setSession({
          access_token: accessToken,
          user,
          company: {
            id: updated.id,
            company_name: updated.company_name,
            short_name: updated.short_name,
            slug: updated.slug,
            logo_url: updated.logo_url,
            status: updated.status,
            verification_tier: updated.verification_tier,
            rejected_reason: updated.rejected_reason,
          },
        })
      }
    },
    onError: (error: unknown) => {
      setSaved(false)
      setSaveError(error instanceof ApiError ? error.message : 'Lưu không thành công.')
    },
  })

  const addressMutation = useMutation({
    mutationFn: (payload: { city_id: number; address_detail: string }) => addAddress(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['employer', 'company'] }),
  })

  const removeAddressMutation = useMutation({
    mutationFn: deleteAddress,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['employer', 'company'] }),
  })

  if (isPending || !company || !form) {
    return <PageShell title="Hồ sơ công ty"><p className="text-sm text-slate-500">Đang tải…</p></PageShell>
  }

  const update = (field: keyof EditableForm, value: string) => {
    setForm({ ...form, [field]: value })
    setSaved(false)
  }

  return (
    <PageShell
      title="Hồ sơ công ty"
      subtitle={company.company_name}
      actions={
        <div className="flex items-center gap-2">
          <CompanyStatusBadge status={company.status} />
          {company.verification_tier === 'VERIFIED' && <Badge tone="success">✔ Đã xác thực</Badge>}
        </div>
      }
    >
      {company.status === 'PENDING' && (
        <div className="mb-5 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm">
          <p className="font-semibold text-amber-900">Hồ sơ đang chờ quản trị viên duyệt</p>
          <p className="mt-0.5 text-amber-800">
            Bạn chưa thể đăng tin tuyển dụng cho tới khi hồ sơ được duyệt.
          </p>
        </div>
      )}

      {company.status === 'REJECTED' && (
        <div className="mb-5 rounded-lg border border-red-300 bg-red-50 p-4 text-sm">
          <p className="font-semibold text-red-900">Hồ sơ bị từ chối</p>
          <p className="mt-0.5 text-red-800">{company.rejected_reason}</p>
          <p className="mt-2 text-red-800">
            Sửa lại thông tin bên dưới và lưu, hồ sơ sẽ tự được gửi duyệt lại.
          </p>
        </div>
      )}

      {company.tax_code_verified_at === null && (
        <div className="mb-5 rounded-lg border border-slate-300 bg-white p-4 text-sm text-slate-600">
          Tên công ty <strong>chưa được đối chiếu</strong> với dữ liệu đăng ký kinh doanh
          (VietQR không phản hồi lúc bạn đăng ký). Quản trị viên sẽ kiểm tra thủ công.
        </div>
      )}

      <form
        className="rounded-xl border border-slate-200 bg-white p-5"
        onSubmit={(event) => {
          event.preventDefault()
          saveMutation.mutate(form)
        }}
      >
        {saveError && (
          <div role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {saveError}
          </div>
        )}
        {saved && (
          <div className="mb-4 rounded-lg border border-green-200 bg-brand-light px-4 py-3 text-sm text-brand-dark">
            Đã lưu thay đổi.
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <TextField
            label="Mã số thuế"
            value={company.tax_code}
            readOnly
            disabled
            hint="Không sửa được — đây là khoá định danh doanh nghiệp trên hệ thống"
          />
          <SelectField
            label="Quy mô"
            value={form.company_size}
            onChange={(event) => update('company_size', event.target.value)}
          >
            {COMPANY_SIZES.map((size) => (
              <option key={size} value={size}>
                {COMPANY_SIZE_LABELS[size]}
              </option>
            ))}
          </SelectField>
        </div>

        <div className="mt-4 space-y-4">
          <TextField
            label="Tên công ty"
            required
            value={form.company_name}
            onChange={(event) => update('company_name', event.target.value)}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Tên quốc tế"
              value={form.international_name}
              onChange={(event) => update('international_name', event.target.value)}
            />
            <TextField
              label="Tên viết tắt"
              value={form.short_name}
              onChange={(event) => update('short_name', event.target.value)}
            />
            <TextField
              label="Người đại diện"
              required
              value={form.director}
              onChange={(event) => update('director', event.target.value)}
            />
            <TextField
              label="Website"
              value={form.website}
              onChange={(event) => update('website', event.target.value)}
            />
            <TextField
              label="Email công ty"
              type="email"
              required
              value={form.email}
              onChange={(event) => update('email', event.target.value)}
            />
            <TextField
              label="Số điện thoại"
              type="tel"
              required
              value={form.phone_number}
              onChange={(event) => update('phone_number', event.target.value)}
            />
          </div>
          <TextField
            label="Địa chỉ trụ sở"
            required
            value={form.headquarters_address}
            onChange={(event) => update('headquarters_address', event.target.value)}
          />
        </div>

        <div className="mt-5">
          <Button type="submit" loading={saveMutation.isPending}>
            Lưu thay đổi
          </Button>
        </div>
      </form>

      <section className="mt-6 rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="font-bold text-slate-800">Địa điểm làm việc</h2>
        <p className="mt-0.5 text-sm text-slate-500">
          Dùng để hiển thị nơi làm việc trên tin tuyển dụng.
        </p>

        <ul className="mt-4 space-y-2">
          {company.addresses.map((address) => (
            <li
              key={address.id}
              className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 text-sm"
            >
              <span className="font-medium text-slate-700">
                {cities?.find((city) => city.id === address.city_id)?.name ?? `#${address.city_id}`}
              </span>
              <span className="flex-1 text-slate-600">{address.address_detail}</span>
              <Button
                variant="secondary"
                onClick={() => removeAddressMutation.mutate(address.id)}
                loading={removeAddressMutation.isPending}
              >
                Xoá
              </Button>
            </li>
          ))}
          {company.addresses.length === 0 && (
            <li className="rounded-lg border border-dashed border-slate-300 p-4 text-center text-sm text-slate-500">
              Chưa có địa điểm nào.
            </li>
          )}
        </ul>

        <AddressForm
          cities={cities ?? []}
          onSubmit={(payload) => addressMutation.mutate(payload)}
          isPending={addressMutation.isPending}
          error={
            addressMutation.error instanceof ApiError ? addressMutation.error.message : null
          }
        />
      </section>
    </PageShell>
  )
}

function AddressForm({
  cities,
  onSubmit,
  isPending,
  error,
}: {
  cities: City[]
  onSubmit: (payload: { city_id: number; address_detail: string }) => void
  isPending: boolean
  error: string | null
}) {
  const [cityId, setCityId] = useState('1')
  const [detail, setDetail] = useState('')

  return (
    <form
      className="mt-4 border-t border-slate-200 pt-4"
      onSubmit={(event) => {
        event.preventDefault()
        if (!detail.trim()) return
        onSubmit({ city_id: Number(cityId), address_detail: detail.trim() })
        setDetail('')
      }}
    >
      {error && (
        <p role="alert" className="mb-2 text-xs text-red-600">
          {error}
        </p>
      )}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="sm:w-56">
          <SelectField
            label="Tỉnh/thành"
            value={cityId}
            onChange={(event) => setCityId(event.target.value)}
          >
            {cities.map((city) => (
              <option key={city.id} value={city.id}>
                {city.name}
              </option>
            ))}
          </SelectField>
        </div>
        <div className="flex-1">
          <TextField
            label="Địa chỉ chi tiết"
            value={detail}
            onChange={(event) => setDetail(event.target.value)}
            placeholder="Tầng 3, Toà FS GoldSeason, 47 Nguyễn Tuân"
          />
        </div>
        <Button type="submit" loading={isPending}>
          Thêm
        </Button>
      </div>
    </form>
  )
}
