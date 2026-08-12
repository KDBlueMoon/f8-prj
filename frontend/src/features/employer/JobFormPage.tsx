import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PageShell } from '@/components/layout/PageShell'
import { JobStatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { SelectField, TextField } from '@/components/ui/FormField'
import { RichTextEditor } from '@/components/ui/RichTextEditor'
import { SafeHtml } from '@/components/ui/SafeHtml'
import { createJob, getMyJob, updateJob } from '@/features/jobs/api'
import { toDateInputValue, toDeadlineIso } from '@/features/jobs/format'
import { ApiError, apiGet } from '@/lib/apiClient'
import { useAuthStore } from '@/stores/authStore'
import type { CategoryGroup, City } from '@/types/catalog'
import {
  EXPERIENCE_LABELS,
  GENDER_LABELS,
  JOB_TYPE_LABELS,
  SALARY_FIELDS,
  SALARY_TYPE_LABELS,
  type ExperienceLevel,
  type Gender,
  type Job,
  type JobInput,
  type JobType,
  type SalaryType,
} from '@/types/job'

const DEFAULT_DEADLINE_DAYS = 30
const HANOI_CITY_ID = 1

interface FormState {
  title: string
  category_id: string
  specialty: string
  job_type: JobType
  experience_level: ExperienceLevel
  gender: Gender
  quantity: string
  salary_type: SalaryType
  salary_min: string
  salary_max: string
  deadline: string
  description_html: string
  requirements_html: string
  benefits_html: string
  locations: Array<{ city_id: number; address_detail: string }>
}

function emptyForm(): FormState {
  const deadline = new Date()
  deadline.setDate(deadline.getDate() + DEFAULT_DEADLINE_DAYS)

  return {
    title: '',
    category_id: '',
    specialty: '',
    job_type: 'FULL_TIME',
    experience_level: 'NO_EXP',
    gender: 'NOT_REQUIRED',
    quantity: '1',
    salary_type: 'RANGE',
    salary_min: '',
    salary_max: '',
    deadline: toDateInputValue(deadline.toISOString()),
    description_html: '',
    requirements_html: '',
    benefits_html: '',
    locations: [{ city_id: HANOI_CITY_ID, address_detail: '' }],
  }
}

function toForm(job: Job): FormState {
  return {
    title: job.title,
    category_id: job.category_id,
    specialty: job.specialty ?? '',
    job_type: job.job_type,
    experience_level: job.experience_level,
    gender: job.gender,
    quantity: String(job.quantity),
    salary_type: job.salary_type,
    salary_min: job.salary_min === null ? '' : String(job.salary_min),
    salary_max: job.salary_max === null ? '' : String(job.salary_max),
    deadline: toDateInputValue(job.deadline),
    description_html: job.description_html,
    requirements_html: job.requirements_html,
    benefits_html: job.benefits_html,
    locations: job.locations.map((item) => ({
      city_id: item.city_id,
      address_detail: item.address_detail ?? '',
    })),
  }
}

/** Ô lương không dùng tới phải gửi null, không phải 0 — 0 nghĩa là "lương 0đ". */
function toPayload(form: FormState): JobInput {
  const usedFields = SALARY_FIELDS[form.salary_type]
  const parseSalary = (field: 'salary_min' | 'salary_max'): number | null =>
    usedFields.includes(field) && form[field] !== '' ? Number(form[field]) : null

  return {
    title: form.title.trim(),
    category_id: form.category_id,
    specialty: form.specialty.trim() || null,
    job_type: form.job_type,
    experience_level: form.experience_level,
    gender: form.gender,
    quantity: Number(form.quantity),
    salary_type: form.salary_type,
    salary_min: parseSalary('salary_min'),
    salary_max: parseSalary('salary_max'),
    deadline: toDeadlineIso(form.deadline),
    description_html: form.description_html,
    requirements_html: form.requirements_html,
    benefits_html: form.benefits_html,
    locations: form.locations.map((item) => ({
      city_id: item.city_id,
      address_detail: item.address_detail.trim() || null,
    })),
  }
}

/**
 * Xem trước đúng cách ứng viên sẽ thấy: cùng `SafeHtml`, cùng class `rich-text`.
 *
 * Có ích thật chứ không chỉ để cho đẹp — nhà tuyển dụng thấy ngay phần định dạng
 * nào bị lược bỏ khi dán nội dung từ Word, thay vì tới lúc tin đã đăng mới biết.
 */
function ContentPreview({ form }: { form: FormState }) {
  const blocks: Array<[string, string]> = [
    ['Mô tả công việc', form.description_html],
    ['Yêu cầu ứng viên', form.requirements_html],
    ['Quyền lợi', form.benefits_html],
  ]

  return (
    <div className="space-y-5">
      {blocks.map(([heading, html]) => (
        <div key={heading}>
          <h3 className="mb-1.5 text-sm font-semibold text-slate-700">{heading}</h3>
          {html ? (
            <SafeHtml html={html} className="rounded-lg border border-slate-200 p-4" />
          ) : (
            <p className="rounded-lg border border-dashed border-slate-300 p-4 text-sm text-slate-500">
              Chưa có nội dung.
            </p>
          )}
        </div>
      ))}
    </div>
  )
}

export default function JobFormPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const isEditing = Boolean(jobId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const company = useAuthStore((state) => state.company)
  const canPublish = company?.status === 'APPROVED'

  const [form, setForm] = useState<FormState | null>(isEditing ? null : emptyForm())
  const [error, setError] = useState<string | null>(null)
  const [previewing, setPreviewing] = useState(false)

  const { data: job } = useQuery({
    queryKey: ['employer', 'job', jobId],
    queryFn: () => getMyJob(jobId as string),
    enabled: isEditing,
  })
  const { data: categoryGroups } = useQuery({
    queryKey: ['categories'],
    queryFn: () => apiGet<CategoryGroup[]>('/categories'),
    staleTime: 60 * 60 * 1000,
  })
  const { data: cities } = useQuery({
    queryKey: ['cities'],
    queryFn: () => apiGet<City[]>('/cities'),
    staleTime: 60 * 60 * 1000,
  })

  // Nạp một lần khi tải xong; sau đó form tự quản lý để không đè lên phần
  // người dùng đang gõ dở.
  useEffect(() => {
    if (job && form === null) setForm(toForm(job))
  }, [job, form])

  // Tin mới cần một ngành nghề mặc định, nếu không select sẽ hiện rỗng mà vẫn
  // gửi lên chuỗi trống rồi bị backend từ chối.
  useEffect(() => {
    const firstCategory = categoryGroups?.[0]?.categories[0]?.id
    if (!firstCategory) return
    setForm((previous) =>
      previous && !previous.category_id ? { ...previous, category_id: firstCategory } : previous,
    )
  }, [categoryGroups])

  const saveMutation = useMutation({
    mutationFn: ({ values, publish }: { values: FormState; publish: boolean }) => {
      const payload = toPayload(values)
      return isEditing
        ? updateJob(jobId as string, payload)
        : createJob({ ...payload, status: publish ? 'PUBLISHED' : 'DRAFT' })
    },
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: ['employer', 'jobs'] })
      queryClient.invalidateQueries({ queryKey: ['employer', 'jobCounts'] })
      queryClient.setQueryData(['employer', 'job', saved.id], saved)
      navigate('/ntd/tin-tuyen-dung')
    },
    onError: (cause: unknown) =>
      setError(cause instanceof ApiError ? cause.message : 'Lưu tin không thành công.'),
  })

  if (!form) {
    return (
      <PageShell title="Tin tuyển dụng">
        <p className="text-sm text-slate-500">Đang tải…</p>
      </PageShell>
    )
  }

  // Cập nhật theo dạng hàm chứ không đọc `form` từ closure: TipTap giữ lại
  // callback `onUpdate` của lần render tạo editor, nên nếu ghi đè bằng bản
  // `form` cũ thì gõ ở ô mô tả sẽ xoá mất nội dung vừa nhập ở ô khác.
  const update = <K extends keyof FormState>(field: K, value: FormState[K]) =>
    setForm((previous) => (previous ? { ...previous, [field]: value } : previous))

  const salaryFields = SALARY_FIELDS[form.salary_type]

  return (
    <PageShell
      title={isEditing ? 'Sửa tin tuyển dụng' : 'Đăng tin tuyển dụng'}
      subtitle={company?.company_name}
      actions={job && <JobStatusBadge status={job.status} />}
    >
      {job?.status === 'TAKEN_DOWN' && (
        <div className="mb-5 rounded-lg border border-red-300 bg-red-50 p-4 text-sm">
          <p className="font-semibold text-red-900">Tin đã bị quản trị viên gỡ</p>
          <p className="mt-0.5 text-red-800">{job.takedown_reason}</p>
          <p className="mt-2 text-red-800">
            Sửa lại nội dung và lưu, tin sẽ về dạng nháp để bạn đăng lại.
          </p>
        </div>
      )}

      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault()
          setError(null)
          saveMutation.mutate({ values: form, publish: false })
        }}
      >
        {error && (
          <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-4 font-bold text-slate-800">Thông tin chung</h2>

          <div className="space-y-4">
            <TextField
              label="Tiêu đề tin"
              required
              minLength={5}
              maxLength={255}
              value={form.title}
              onChange={(event) => update('title', event.target.value)}
              placeholder="VD: Lập trình viên Backend Python (Junior)"
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <SelectField
                label="Ngành nghề"
                required
                value={form.category_id}
                onChange={(event) => update('category_id', event.target.value)}
              >
                {categoryGroups?.map((group) => (
                  <optgroup key={group.id} label={group.group_name}>
                    {group.categories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </SelectField>
              <TextField
                label="Chuyên môn"
                value={form.specialty}
                onChange={(event) => update('specialty', event.target.value)}
                placeholder="VD: Frontend Developer"
                hint="Không bắt buộc — giúp ứng viên hình dung rõ hơn vị trí"
              />
              <SelectField
                label="Hình thức làm việc"
                value={form.job_type}
                onChange={(event) => update('job_type', event.target.value as JobType)}
              >
                {Object.entries(JOB_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </SelectField>
              <SelectField
                label="Kinh nghiệm"
                value={form.experience_level}
                onChange={(event) =>
                  update('experience_level', event.target.value as ExperienceLevel)
                }
              >
                {Object.entries(EXPERIENCE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </SelectField>
              <SelectField
                label="Giới tính"
                value={form.gender}
                onChange={(event) => update('gender', event.target.value as Gender)}
              >
                {Object.entries(GENDER_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </SelectField>
              <TextField
                label="Số lượng tuyển"
                type="number"
                min={1}
                max={999}
                required
                value={form.quantity}
                onChange={(event) => update('quantity', event.target.value)}
              />
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-4 font-bold text-slate-800">Mức lương và hạn nộp</h2>

          <div className="grid gap-4 sm:grid-cols-2">
            <SelectField
              label="Kiểu lương"
              value={form.salary_type}
              onChange={(event) => update('salary_type', event.target.value as SalaryType)}
            >
              {Object.entries(SALARY_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </SelectField>
            <TextField
              label="Hạn nộp hồ sơ"
              type="date"
              required
              value={form.deadline}
              onChange={(event) => update('deadline', event.target.value)}
              hint="Tính đến hết ngày đã chọn (giờ Việt Nam)"
            />
            {salaryFields.includes('salary_min') && (
              <TextField
                label="Lương tối thiểu (VNĐ)"
                type="number"
                min={0}
                required
                value={form.salary_min}
                onChange={(event) => update('salary_min', event.target.value)}
                placeholder="20000000"
              />
            )}
            {salaryFields.includes('salary_max') && (
              <TextField
                label="Lương tối đa (VNĐ)"
                type="number"
                min={0}
                required
                value={form.salary_max}
                onChange={(event) => update('salary_max', event.target.value)}
                placeholder="35000000"
              />
            )}
          </div>
          {form.salary_type === 'AGREEMENT' && (
            <p className="mt-3 text-xs text-slate-500">
              Tin sẽ hiển thị "Thoả thuận", không kèm con số nào.
            </p>
          )}
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-bold text-slate-800">Địa điểm làm việc</h2>
            <Button
              type="button"
              variant="secondary"
              onClick={() =>
                update('locations', [
                  ...form.locations,
                  { city_id: HANOI_CITY_ID, address_detail: '' },
                ])
              }
            >
              + Thêm địa điểm
            </Button>
          </div>

          <div className="space-y-3">
            {form.locations.map((location, index) => (
              <div key={index} className="flex flex-col gap-2 sm:flex-row sm:items-end">
                <div className="sm:w-56">
                  <SelectField
                    label="Tỉnh/thành"
                    value={String(location.city_id)}
                    onChange={(event) =>
                      update(
                        'locations',
                        form.locations.map((item, position) =>
                          position === index
                            ? { ...item, city_id: Number(event.target.value) }
                            : item,
                        ),
                      )
                    }
                  >
                    {cities?.map((city) => (
                      <option key={city.id} value={city.id}>
                        {city.name}
                      </option>
                    ))}
                  </SelectField>
                </div>
                <div className="flex-1">
                  <TextField
                    label="Địa chỉ chi tiết"
                    value={location.address_detail}
                    onChange={(event) =>
                      update(
                        'locations',
                        form.locations.map((item, position) =>
                          position === index
                            ? { ...item, address_detail: event.target.value }
                            : item,
                        ),
                      )
                    }
                    placeholder="Tầng 3, Toà FS GoldSeason, 47 Nguyễn Tuân"
                  />
                </div>
                {/* Luôn phải còn ít nhất một địa điểm — backend cũng bắt buộc. */}
                {form.locations.length > 1 && (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() =>
                      update(
                        'locations',
                        form.locations.filter((_, position) => position !== index),
                      )
                    }
                  >
                    Xoá
                  </Button>
                )}
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-5 rounded-xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-800">Nội dung tin</h2>
            <Button type="button" variant="ghost" onClick={() => setPreviewing(!previewing)}>
              {previewing ? 'Quay lại soạn thảo' : 'Xem trước'}
            </Button>
          </div>

          {previewing ? (
            <ContentPreview form={form} />
          ) : (
            <div className="space-y-5">
              <RichTextEditor
                label="Mô tả công việc"
                required
                value={form.description_html}
                onChange={(html) => update('description_html', html)}
              />
              <RichTextEditor
                label="Yêu cầu ứng viên"
                required
                value={form.requirements_html}
                onChange={(html) => update('requirements_html', html)}
              />
              <RichTextEditor
                label="Quyền lợi"
                required
                value={form.benefits_html}
                onChange={(html) => update('benefits_html', html)}
              />
            </div>
          )}
        </section>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" variant="secondary" loading={saveMutation.isPending}>
            {isEditing ? 'Lưu thay đổi' : 'Lưu nháp'}
          </Button>

          {!isEditing && (
            <Button
              type="button"
              disabled={!canPublish}
              title={canPublish ? undefined : 'Hồ sơ công ty chưa được duyệt'}
              loading={saveMutation.isPending}
              onClick={() => {
                setError(null)
                saveMutation.mutate({ values: form, publish: true })
              }}
            >
              Đăng tin ngay
            </Button>
          )}

          <Button type="button" variant="ghost" onClick={() => navigate('/ntd/tin-tuyen-dung')}>
            Huỷ
          </Button>

          {!canPublish && (
            <span className="text-xs text-amber-700">
              Hồ sơ công ty chưa được duyệt — bạn chỉ lưu nháp được.
            </span>
          )}
        </div>
      </form>
    </PageShell>
  )
}
