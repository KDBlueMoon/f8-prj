import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/layout/PageShell'
import { Badge, JobStatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { changeJobStatus, countMyJobs, deleteJob, listMyJobs } from '@/features/jobs/api'
import { daysUntil, formatDate, formatSalary } from '@/features/jobs/format'
import { ApiError } from '@/lib/apiClient'
import { useAuthStore } from '@/stores/authStore'
import { JOB_STATUS_LABELS, type JobListItem, type JobStatus } from '@/types/job'

const TABS: Array<JobStatus | 'ALL'> = ['ALL', 'PUBLISHED', 'DRAFT', 'CLOSED', 'TAKEN_DOWN']

export default function JobListPage() {
  const queryClient = useQueryClient()
  const company = useAuthStore((state) => state.company)
  const [tab, setTab] = useState<JobStatus | 'ALL'>('ALL')
  const [keyword, setKeyword] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [actionError, setActionError] = useState<string | null>(null)

  const { data: counts } = useQuery({ queryKey: ['employer', 'jobCounts'], queryFn: countMyJobs })
  const { data, isPending } = useQuery({
    queryKey: ['employer', 'jobs', tab, search, page],
    queryFn: () =>
      listMyJobs({ status: tab === 'ALL' ? undefined : tab, q: search || undefined, page }),
  })

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['employer', 'jobs'] })
    queryClient.invalidateQueries({ queryKey: ['employer', 'jobCounts'] })
  }

  const handleError = (error: unknown) =>
    setActionError(error instanceof ApiError ? error.message : 'Thao tác không thành công.')

  const statusMutation = useMutation({
    mutationFn: (input: { id: string; status: 'PUBLISHED' | 'CLOSED' }) =>
      changeJobStatus(input.id, input.status),
    onSuccess: () => {
      setActionError(null)
      refresh()
    },
    onError: handleError,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteJob,
    onSuccess: () => {
      setActionError(null)
      refresh()
    },
    onError: handleError,
  })

  const canPublish = company?.status === 'APPROVED'

  return (
    <PageShell
      title="Tin tuyển dụng"
      subtitle="Quản lý toàn bộ tin của công ty bạn"
      actions={
        <Link to="/ntd/tin-tuyen-dung/tao">
          <Button>+ Đăng tin mới</Button>
        </Link>
      }
    >
      {!canPublish && (
        <div className="mb-5 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm">
          <p className="font-semibold text-amber-900">
            Hồ sơ công ty chưa được duyệt — bạn chưa thể đăng tin
          </p>
          <p className="mt-0.5 text-amber-800">
            Bạn vẫn soạn và lưu nháp được. Tin sẽ đăng lên ngay sau khi hồ sơ công ty được duyệt.{' '}
            <Link to="/ntd/cong-ty" className="font-medium underline">
              Xem hồ sơ công ty
            </Link>
          </p>
        </div>
      )}

      <div className="mb-4 flex flex-wrap items-center gap-2">
        {TABS.map((value) => (
          <button
            key={value}
            onClick={() => {
              setTab(value)
              setPage(1)
            }}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              tab === value
                ? 'bg-brand text-white'
                : 'border border-slate-300 bg-white text-slate-700 hover:border-brand'
            }`}
          >
            {value === 'ALL' ? 'Tất cả' : JOB_STATUS_LABELS[value]}
            {counts && value !== 'ALL' && ` (${counts[value] ?? 0})`}
          </button>
        ))}

        <form
          className="ml-auto flex gap-2"
          onSubmit={(event) => {
            event.preventDefault()
            setSearch(keyword.trim())
            setPage(1)
          }}
        >
          <input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="Tìm theo tiêu đề tin"
            className="w-64 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
          />
          <Button type="submit" variant="secondary">
            Tìm
          </Button>
        </form>
      </div>

      {actionError && (
        <div role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {actionError}
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[860px] text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="p-3 text-left font-semibold">Tin tuyển dụng</th>
              <th className="p-3 text-left font-semibold">Mức lương</th>
              <th className="p-3 text-left font-semibold">Hạn nộp</th>
              <th className="p-3 text-left font-semibold">Trạng thái</th>
              <th className="p-3 text-right font-semibold">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isPending && (
              <tr>
                <td colSpan={5} className="p-6 text-center text-slate-500">
                  Đang tải…
                </td>
              </tr>
            )}

            {data?.items.length === 0 && (
              <tr>
                <td colSpan={5} className="p-6 text-center text-slate-500">
                  Chưa có tin nào ở mục này.
                </td>
              </tr>
            )}

            {data?.items.map((job) => (
              <JobRow
                key={job.id}
                job={job}
                canPublish={canPublish}
                isBusy={statusMutation.isPending || deleteMutation.isPending}
                onChangeStatus={(status) => statusMutation.mutate({ id: job.id, status })}
                onDelete={() => {
                  if (window.confirm(`Xoá tin "${job.title}"?`)) deleteMutation.mutate(job.id)
                }}
              />
            ))}
          </tbody>
        </table>
      </div>

      {data && data.meta.total_pages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-3 text-sm">
          <Button variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Trước
          </Button>
          <span className="text-slate-600">
            Trang {data.meta.page} / {data.meta.total_pages}
          </span>
          <Button
            variant="secondary"
            disabled={page >= data.meta.total_pages}
            onClick={() => setPage(page + 1)}
          >
            Sau
          </Button>
        </div>
      )}
    </PageShell>
  )
}

interface JobRowProps {
  job: JobListItem
  canPublish: boolean
  isBusy: boolean
  onChangeStatus: (status: 'PUBLISHED' | 'CLOSED') => void
  onDelete: () => void
}

function JobRow({ job, canPublish, isBusy, onChangeStatus, onDelete }: JobRowProps) {
  const remaining = daysUntil(job.deadline)
  // Tin bị gỡ không có nút đăng lại: phải sửa nội dung để tin về nháp trước —
  // backend cũng chặn, đây chỉ là để nhà tuyển dụng khỏi bấm vào chỗ vô ích.
  const canRepublish = job.status === 'DRAFT' || job.status === 'CLOSED' || job.status === 'EXPIRED'

  return (
    <tr className="hover:bg-slate-50">
      <td className="p-3">
        <p className="font-semibold leading-snug text-slate-800">{job.title}</p>
        <p className="mt-0.5 text-xs text-slate-500">
          {job.quantity} người · {job.locations.length} địa điểm · {job.view_count} lượt xem
        </p>
        {job.status === 'TAKEN_DOWN' && job.takedown_reason && (
          <p className="mt-1 text-xs text-red-700">Lý do bị gỡ: {job.takedown_reason}</p>
        )}
      </td>
      <td className="p-3 text-slate-700">{formatSalary(job)}</td>
      <td className="p-3">
        <p className="text-slate-700">{formatDate(job.deadline)}</p>
        <p className={`text-xs ${remaining < 0 ? 'text-red-600' : 'text-slate-500'}`}>
          {remaining < 0 ? 'Đã quá hạn' : `Còn ${remaining} ngày`}
        </p>
      </td>
      <td className="p-3">
        <JobStatusBadge status={job.status} />
        {job.is_hot && (
          <div className="mt-1">
            <Badge tone="warning">Nổi bật</Badge>
          </div>
        )}
      </td>
      <td className="whitespace-nowrap p-3 text-right">
        <div className="inline-flex gap-2">
          <Link to={`/ntd/tin-tuyen-dung/${job.id}`}>
            <Button variant="secondary">Sửa</Button>
          </Link>
          {canRepublish && (
            <Button
              disabled={!canPublish}
              title={canPublish ? undefined : 'Hồ sơ công ty chưa được duyệt'}
              loading={isBusy}
              onClick={() => onChangeStatus('PUBLISHED')}
            >
              Đăng
            </Button>
          )}
          {job.status === 'PUBLISHED' && (
            <Button variant="secondary" loading={isBusy} onClick={() => onChangeStatus('CLOSED')}>
              Đóng tin
            </Button>
          )}
          <Button variant="ghost" onClick={onDelete}>
            Xoá
          </Button>
        </div>
      </td>
    </tr>
  )
}
