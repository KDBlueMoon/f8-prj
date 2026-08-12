import { describe, expect, it } from 'vitest'
import { formatSalary, toDeadlineIso } from './format'

describe('formatSalary', () => {
  it('hiển thị khoảng lương theo đơn vị triệu', () => {
    expect(
      formatSalary({ salary_type: 'RANGE', salary_min: 20_000_000, salary_max: 35_000_000 }),
    ).toBe('20 triệu - 35 triệu')
  })

  it('rút gọn phần thập phân', () => {
    expect(formatSalary({ salary_type: 'FROM', salary_min: 1_500_000, salary_max: null })).toBe(
      'Từ 1,5 triệu',
    )
  })

  it('bỏ qua con số khi lương thoả thuận', () => {
    expect(formatSalary({ salary_type: 'AGREEMENT', salary_min: null, salary_max: null })).toBe(
      'Thoả thuận',
    )
  })

  it('không vỡ khi thiếu con số đáng lẽ phải có', () => {
    // Backend đã chặn trường hợp này, nhưng dữ liệu import về sau có thể thiếu.
    expect(formatSalary({ salary_type: 'RANGE', salary_min: 20_000_000, salary_max: null })).toBe(
      'Thoả thuận',
    )
  })
})

describe('toDeadlineIso', () => {
  it('gắn cứng múi giờ Việt Nam chứ không theo máy người dùng', () => {
    // Không có offset thì máy đặt múi giờ khác sẽ ra một thời điểm khác, và hạn
    // nộp lệch cả nửa ngày so với ý người đăng tin.
    expect(toDeadlineIso('2026-12-31')).toBe('2026-12-31T23:59:59+07:00')
  })
})
