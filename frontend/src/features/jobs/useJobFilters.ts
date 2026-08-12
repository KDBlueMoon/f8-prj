import { useSearchParams } from 'react-router-dom'
import type { PublicJobFilters } from '@/features/jobs/api'
import type { JobSort } from '@/types/job'

const SORTS: JobSort[] = ['newest', 'salary_desc', 'deadline']

/** Bộ lọc đang bật. `sort` và `page` không tính vì luôn có giá trị. */
const COUNTED_FILTERS = [
  'q',
  'category_id',
  'group_id',
  'city_id',
  'job_type',
  'experience_level',
  'salary_min',
  'is_hot',
] as const

function readNumber(params: URLSearchParams, key: string): number | undefined {
  const raw = params.get(key)
  if (raw === null) return undefined
  const value = Number(raw)
  return Number.isFinite(value) ? value : undefined
}

/** Đọc bộ lọc từ URL. Hàm thuần, tách riêng để test được không cần router. */
export function parseJobFilters(params: URLSearchParams): PublicJobFilters {
  const sort = params.get('sort') as JobSort | null

  return {
    q: params.get('q') ?? undefined,
    category_id: params.get('category_id') ?? undefined,
    group_id: params.get('group_id') ?? undefined,
    city_id: readNumber(params, 'city_id'),
    job_type: params.get('job_type') ?? undefined,
    experience_level: params.get('experience_level') ?? undefined,
    salary_min: readNumber(params, 'salary_min'),
    is_hot: params.get('is_hot') === 'true' ? true : undefined,
    // Giá trị lạ trên URL (người dùng tự gõ) rơi về mặc định thay vì gửi lên
    // backend rồi nhận 422.
    sort: sort && SORTS.includes(sort) ? sort : 'newest',
    page: readNumber(params, 'page') ?? 1,
  }
}

/**
 * Ghi bộ lọc mới lên URL.
 *
 * Luôn xoá `page`: đổi điều kiện lọc mà giữ nguyên trang 5 thì kết quả mới
 * thường không có tới trang đó và người dùng nhìn thấy màn hình trống.
 */
export function patchJobParams(
  params: URLSearchParams,
  patch: Partial<PublicJobFilters>,
): URLSearchParams {
  const next = new URLSearchParams(params)
  for (const [key, value] of Object.entries(patch)) {
    if (value === undefined || value === '' || value === false) next.delete(key)
    else next.set(key, String(value))
  }
  next.delete('page')
  return next
}

/** Trang 1 không cần nằm trên URL — giữ link sạch và ổn định. */
export function setPageParam(params: URLSearchParams, page: number): URLSearchParams {
  const next = new URLSearchParams(params)
  if (page <= 1) next.delete('page')
  else next.set('page', String(page))
  return next
}

export function countActiveFilters(filters: PublicJobFilters): number {
  return COUNTED_FILTERS.filter((key) => filters[key] !== undefined).length
}

/**
 * Bộ lọc việc làm sống trên URL chứ không trong state của component
 * (DESIGN mục 6.2).
 *
 * Nhờ vậy link chia sẻ được, nút back/forward của trình duyệt chạy đúng, và F5
 * không mất bộ lọc đang chọn — ba thứ mà state cục bộ không cho được.
 */
export function useJobFilters(): {
  filters: PublicJobFilters
  setFilter: (patch: Partial<PublicJobFilters>) => void
  setPage: (page: number) => void
  reset: () => void
  activeCount: number
} {
  const [params, setParams] = useSearchParams()
  const filters = parseJobFilters(params)

  return {
    filters,
    setFilter: (patch) => setParams(patchJobParams(params, patch)),
    setPage: (page) => setParams(setPageParam(params, page)),
    reset: () => setParams(new URLSearchParams()),
    activeCount: countActiveFilters(filters),
  }
}
