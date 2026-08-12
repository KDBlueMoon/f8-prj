import { describe, expect, it } from 'vitest'
import {
  countActiveFilters,
  parseJobFilters,
  patchJobParams,
  setPageParam,
} from './useJobFilters'

const params = (query: string) => new URLSearchParams(query)

describe('parseJobFilters', () => {
  it('đọc đủ bộ lọc từ URL và ép về đúng kiểu', () => {
    const filters = parseJobFilters(
      params('q=backend&city_id=2&salary_min=30000000&is_hot=true&sort=deadline&page=3'),
    )

    expect(filters).toMatchObject({
      q: 'backend',
      city_id: 2,
      salary_min: 30_000_000,
      is_hot: true,
      sort: 'deadline',
      page: 3,
    })
  })

  it('URL trống thì về mặc định', () => {
    const filters = parseJobFilters(params(''))

    expect(filters.sort).toBe('newest')
    expect(filters.page).toBe(1)
    expect(filters.q).toBeUndefined()
  })

  it('bỏ qua giá trị sort lạ thay vì gửi lên backend rồi nhận 422', () => {
    // Người dùng gõ tay lên thanh địa chỉ là chuyện có thật.
    expect(parseJobFilters(params('sort=luong_cao_nhat')).sort).toBe('newest')
  })

  it('bỏ qua tham số số học không parse được', () => {
    expect(parseJobFilters(params('city_id=abc&page=xyz')).city_id).toBeUndefined()
    expect(parseJobFilters(params('city_id=abc&page=xyz')).page).toBe(1)
  })

  it('chỉ coi is_hot là bật khi đúng chuỗi "true"', () => {
    expect(parseJobFilters(params('is_hot=false')).is_hot).toBeUndefined()
    expect(parseJobFilters(params('is_hot=1')).is_hot).toBeUndefined()
  })
})

describe('patchJobParams', () => {
  it('đổi bộ lọc thì luôn quay về trang 1', () => {
    // Giữ nguyên page=7 sau khi đổi lọc là người dùng nhìn thấy màn hình trống.
    const next = patchJobParams(params('page=7&q=cũ'), { q: 'mới' })

    expect(next.get('q')).toBe('mới')
    expect(next.has('page')).toBe(false)
  })

  it('giá trị rỗng, undefined hay false thì xoá khỏi URL', () => {
    const next = patchJobParams(params('q=backend&city_id=2&is_hot=true'), {
      q: '',
      city_id: undefined,
      is_hot: false,
    })

    expect(next.toString()).toBe('')
  })

  it('giữ nguyên các bộ lọc không nằm trong patch', () => {
    const next = patchJobParams(params('q=backend&city_id=2'), { job_type: 'FULL_TIME' })

    expect(next.get('q')).toBe('backend')
    expect(next.get('city_id')).toBe('2')
    expect(next.get('job_type')).toBe('FULL_TIME')
  })
})

describe('setPageParam', () => {
  it('trang 1 không để lại dấu vết trên URL', () => {
    expect(setPageParam(params('q=abc&page=4'), 1).toString()).toBe('q=abc')
  })

  it('trang khác 1 thì ghi lên URL', () => {
    expect(setPageParam(params('q=abc'), 3).get('page')).toBe('3')
  })
})

describe('countActiveFilters', () => {
  it('không đếm sort và page vì hai thứ đó luôn có giá trị', () => {
    expect(countActiveFilters(parseJobFilters(params('sort=deadline&page=2')))).toBe(0)
    expect(countActiveFilters(parseJobFilters(params('q=a&city_id=1&is_hot=true')))).toBe(3)
  })
})
