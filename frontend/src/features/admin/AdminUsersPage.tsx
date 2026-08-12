import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { PageShell } from '@/components/layout/PageShell'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ApiError } from '@/lib/apiClient'
import { useAuthStore } from '@/stores/authStore'
import type { UserRole } from '@/types/auth'
import { listUsers, setUserActive } from './api'

const ROLE_LABELS: Record<UserRole, string> = {
  CANDIDATE: 'Ứng viên',
  EMPLOYER: 'Nhà tuyển dụng',
  ADMIN: 'Quản trị viên',
}

export default function AdminUsersPage() {
  const queryClient = useQueryClient()
  const currentUser = useAuthStore((state) => state.user)
  const [keyword, setKeyword] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isPending } = useQuery({
    queryKey: ['admin', 'users', search, page],
    queryFn: () => listUsers({ q: search || undefined, page }),
  })

  const toggleMutation = useMutation({
    mutationFn: (input: { id: string; isActive: boolean }) =>
      setUserActive(input.id, input.isActive),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })

  return (
    <PageShell title="Quản lý người dùng" subtitle="Khoá hoặc mở lại tài khoản">
      <form
        className="mb-4 flex gap-2"
        onSubmit={(event) => {
          event.preventDefault()
          setSearch(keyword.trim())
          setPage(1)
        }}
      >
        <input
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
          placeholder="Tìm theo họ tên hoặc email"
          className="w-72 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <Button type="submit" variant="secondary">
          Tìm
        </Button>
      </form>

      {toggleMutation.error instanceof ApiError && (
        <div role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {toggleMutation.error.message}
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full min-w-[720px] text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="p-3 text-left font-semibold">Người dùng</th>
              <th className="p-3 text-left font-semibold">Vai trò</th>
              <th className="p-3 text-left font-semibold">Trạng thái</th>
              <th className="p-3 text-right font-semibold">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isPending && (
              <tr>
                <td colSpan={4} className="p-6 text-center text-slate-500">
                  Đang tải…
                </td>
              </tr>
            )}

            {data?.items.map((user) => {
              const isSelf = user.id === currentUser?.id

              return (
                <tr key={user.id} className="hover:bg-slate-50">
                  <td className="p-3">
                    <p className="font-semibold text-slate-800">{user.full_name}</p>
                    <p className="text-xs text-slate-500">
                      {user.email}
                      {user.phone_number && ` · ${user.phone_number}`}
                    </p>
                  </td>
                  <td className="p-3 text-slate-700">{ROLE_LABELS[user.role]}</td>
                  <td className="p-3">
                    {user.is_active ? (
                      <Badge tone="success">Đang hoạt động</Badge>
                    ) : (
                      <Badge tone="danger">Đã khoá</Badge>
                    )}
                  </td>
                  <td className="p-3 text-right">
                    <Button
                      variant="secondary"
                      // Tự khoá tài khoản của mình là mất luôn quyền quản trị.
                      // Backend cũng chặn, nút disabled chỉ để đỡ bấm nhầm.
                      disabled={isSelf}
                      title={isSelf ? 'Không thể khoá chính tài khoản của bạn' : undefined}
                      loading={toggleMutation.isPending}
                      onClick={() =>
                        toggleMutation.mutate({ id: user.id, isActive: !user.is_active })
                      }
                    >
                      {user.is_active ? 'Khoá' : 'Mở khoá'}
                    </Button>
                  </td>
                </tr>
              )
            })}
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
