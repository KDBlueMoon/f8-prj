import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useState } from 'react'
import { PageShell } from '@/components/layout/PageShell'
import { Badge, CompanyStatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ApiError } from '@/lib/apiClient'
import type { CompanyStatus } from '@/types/auth'
import { COMPANY_STATUS_LABELS, type CompanyListItem } from '@/types/company'
import { countCompanies, decideCompany, getCompany, listCompanies, setVerification } from './api'

const TABS: CompanyStatus[] = ['PENDING', 'APPROVED', 'REJECTED']

export default function AdminCompaniesPage() {
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<CompanyStatus>('PENDING')
  const [keyword, setKeyword] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [detailId, setDetailId] = useState<string | null>(null)
  const [rejecting, setRejecting] = useState<CompanyListItem | null>(null)

  const { data: counts } = useQuery({ queryKey: ['admin', 'counts'], queryFn: countCompanies })
  const { data, isPending } = useQuery({
    queryKey: ['admin', 'companies', tab, search, page],
    queryFn: () => listCompanies({ status: tab, q: search || undefined, page }),
  })

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['admin', 'companies'] })
    queryClient.invalidateQueries({ queryKey: ['admin', 'counts'] })
  }

  const decisionMutation = useMutation({
    mutationFn: (input: { id: string; status: 'APPROVED' | 'REJECTED'; reason?: string }) =>
      decideCompany(input.id, { status: input.status, rejected_reason: input.reason }),
    onSuccess: () => {
      setRejecting(null)
      refresh()
    },
  })

  const verificationMutation = useMutation({
    mutationFn: (input: { id: string; verified: boolean }) =>
      setVerification(input.id, input.verified ? 'VERIFIED' : 'UNVERIFIED'),
    onSuccess: refresh,
  })

  return (
    <PageShell title="Quản lý công ty" subtitle="Duyệt hồ sơ đăng ký của nhà tuyển dụng">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {TABS.map((status) => (
          <button
            key={status}
            onClick={() => {
              setTab(status)
              setPage(1)
            }}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              tab === status
                ? 'bg-brand text-white'
                : 'border border-slate-300 bg-white text-slate-700 hover:border-brand'
            }`}
          >
            {COMPANY_STATUS_LABELS[status]}
            {counts && ` (${counts[status] ?? 0})`}
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
            placeholder="Tìm theo tên công ty hoặc mã số thuế"
            className="w-72 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
          />
          <Button type="submit" variant="secondary">
            Tìm
          </Button>
        </form>
      </div>

      {decisionMutation.error instanceof ApiError && (
        <div role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {decisionMutation.error.message}
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[900px] text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="p-3 text-left font-semibold">Công ty</th>
              <th className="p-3 text-left font-semibold">Mã số thuế</th>
              <th className="p-3 text-left font-semibold">Người đại diện</th>
              <th className="p-3 text-left font-semibold">Liên hệ</th>
              <th className="p-3 text-left font-semibold">Trạng thái</th>
              <th className="p-3 text-right font-semibold">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isPending && (
              <tr>
                <td colSpan={6} className="p-6 text-center text-slate-500">
                  Đang tải…
                </td>
              </tr>
            )}

            {data?.items.length === 0 && (
              <tr>
                <td colSpan={6} className="p-6 text-center text-slate-500">
                  Không có hồ sơ nào.
                </td>
              </tr>
            )}

            {data?.items.map((company) => (
              <tr key={company.id} className="hover:bg-slate-50">
                <td className="p-3">
                  <p className="font-semibold leading-snug text-slate-800">
                    {company.company_name}
                  </p>
                  <p className="text-xs text-slate-500">{company.short_name ?? '—'}</p>
                </td>
                <td className="p-3">
                  <p className="font-mono text-xs">{company.tax_code}</p>
                  {company.tax_code_verified_at ? (
                    <span className="text-[11px] text-brand-dark">✔ Khớp VietQR</span>
                  ) : (
                    <span className="text-[11px] text-amber-700">Chưa đối chiếu được</span>
                  )}
                </td>
                <td className="p-3 text-slate-700">{company.director}</td>
                <td className="p-3 text-xs">
                  <p>{company.email}</p>
                  <p className="text-slate-500">{company.phone_number}</p>
                </td>
                <td className="p-3">
                  <CompanyStatusBadge status={company.status} />
                  {company.verification_tier === 'VERIFIED' && (
                    <div className="mt-1">
                      <Badge tone="success">✔ Đã xác thực</Badge>
                    </div>
                  )}
                </td>
                <td className="whitespace-nowrap p-3 text-right">
                  <div className="inline-flex gap-2">
                    <Button variant="secondary" onClick={() => setDetailId(company.id)}>
                      Xem
                    </Button>
                    {company.status !== 'APPROVED' && (
                      <Button
                        onClick={() =>
                          decisionMutation.mutate({ id: company.id, status: 'APPROVED' })
                        }
                        loading={decisionMutation.isPending}
                      >
                        Duyệt
                      </Button>
                    )}
                    {company.status !== 'REJECTED' && (
                      <Button variant="secondary" onClick={() => setRejecting(company)}>
                        Từ chối
                      </Button>
                    )}
                    {company.status === 'APPROVED' && (
                      <Button
                        variant="secondary"
                        onClick={() =>
                          verificationMutation.mutate({
                            id: company.id,
                            verified: company.verification_tier !== 'VERIFIED',
                          })
                        }
                        loading={verificationMutation.isPending}
                      >
                        {company.verification_tier === 'VERIFIED' ? 'Gỡ xác thực' : 'Xác thực'}
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
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

      {rejecting && (
        <RejectDialog
          company={rejecting}
          isPending={decisionMutation.isPending}
          onCancel={() => setRejecting(null)}
          onConfirm={(reason) =>
            decisionMutation.mutate({ id: rejecting.id, status: 'REJECTED', reason })
          }
        />
      )}

      {detailId && <CompanyDetailDialog companyId={detailId} onClose={() => setDetailId(null)} />}
    </PageShell>
  )
}

function RejectDialog({
  company,
  isPending,
  onCancel,
  onConfirm,
}: {
  company: CompanyListItem
  isPending: boolean
  onCancel: () => void
  onConfirm: (reason: string) => void
}) {
  const [reason, setReason] = useState('')

  return (
    <Overlay onClose={onCancel}>
      <h2 className="border-b border-slate-200 px-5 py-3 font-bold">Từ chối hồ sơ công ty</h2>
      <form
        className="p-5"
        onSubmit={(event) => {
          event.preventDefault()
          onConfirm(reason.trim())
        }}
      >
        <p className="mb-3 text-sm text-slate-600">{company.company_name}</p>
        <label className="block text-sm font-medium text-slate-700">
          Lý do từ chối <span className="text-red-500">*</span>
          <textarea
            rows={3}
            required
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="VD: Mã số thuế không khớp với tên doanh nghiệp"
            className="mt-1.5 w-full rounded-lg border border-slate-300 p-3 text-sm outline-none focus:border-brand"
          />
        </label>
        <p className="mt-2 text-xs text-slate-500">
          Lý do sẽ hiển thị cho nhà tuyển dụng để họ biết cần sửa gì.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onCancel}>
            Huỷ
          </Button>
          <Button type="submit" loading={isPending} disabled={!reason.trim()}>
            Xác nhận từ chối
          </Button>
        </div>
      </form>
    </Overlay>
  )
}

function CompanyDetailDialog({
  companyId,
  onClose,
}: {
  companyId: string
  onClose: () => void
}) {
  const { data: company, isPending } = useQuery({
    queryKey: ['admin', 'company', companyId],
    queryFn: () => getCompany(companyId),
  })

  return (
    <Overlay onClose={onClose}>
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
        <h2 className="font-bold">Chi tiết hồ sơ công ty</h2>
        <button onClick={onClose} aria-label="Đóng" className="text-xl text-slate-400 hover:text-slate-700">
          ×
        </button>
      </div>
      <div className="max-h-[70vh] overflow-y-auto p-5 text-sm">
        {isPending && <p className="text-slate-500">Đang tải…</p>}
        {company && (
          <dl className="space-y-2">
            {[
              ['Tên công ty', company.company_name],
              ['Tên quốc tế', company.international_name],
              ['Tên viết tắt', company.short_name],
              ['Mã số thuế', company.tax_code],
              ['Đối chiếu VietQR', company.tax_code_verified_at ? 'Khớp' : 'Chưa đối chiếu được'],
              ['Người đại diện', company.director],
              ['Địa chỉ trụ sở', company.headquarters_address],
              ['Ngày cấp GPKD', company.issued_date],
              ['Email', company.email],
              ['Điện thoại', company.phone_number],
              ['Website', company.website],
              ['Quy mô', company.company_size],
            ].map(([label, value]) => (
              <div key={label} className="flex gap-3 border-b border-slate-100 py-1.5">
                <dt className="w-40 shrink-0 text-slate-500">{label}</dt>
                <dd className="text-slate-800">{value || '—'}</dd>
              </div>
            ))}
            <div className="flex gap-3 py-1.5">
              <dt className="w-40 shrink-0 text-slate-500">Địa điểm làm việc</dt>
              <dd className="text-slate-800">
                {company.addresses.length === 0
                  ? '—'
                  : company.addresses.map((address) => (
                      <p key={address.id}>{address.address_detail}</p>
                    ))}
              </dd>
            </div>
          </dl>
        )}
      </div>
    </Overlay>
  )
}

function Overlay({ children, onClose }: { children: ReactNode; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4"
      // Bấm ra ngoài để đóng — nhưng bấm bên trong hộp thoại thì không.
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        className="w-full max-w-lg overflow-hidden rounded-xl bg-white"
        onClick={(event) => event.stopPropagation()}
      >
        {children}
      </div>
    </div>
  )
}
