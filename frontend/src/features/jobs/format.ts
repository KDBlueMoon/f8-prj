import type { JobListItem } from '@/types/job'

const MILLION = 1_000_000

/** "25 triệu", "1,5 triệu" — bỏ phần thập phân thừa cho gọn. */
function toMillions(amount: number): string {
  const value = amount / MILLION
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(value)} triệu`
}

type SalaryFields = Pick<JobListItem, 'salary_type' | 'salary_min' | 'salary_max'>

/**
 * Hiển thị lương theo đúng kiểu lương đã chọn.
 *
 * Backend đảm bảo hai con số khớp với `salary_type`, nhưng vẫn có nhánh dự
 * phòng: dữ liệu cũ hoặc import về sau có thể thiếu, và mất chữ còn hơn vỡ trang.
 */
export function formatSalary({ salary_type, salary_min, salary_max }: SalaryFields): string {
  switch (salary_type) {
    case 'RANGE':
      return salary_min !== null && salary_max !== null
        ? `${toMillions(salary_min)} - ${toMillions(salary_max)}`
        : 'Thoả thuận'
    case 'FROM':
      return salary_min !== null ? `Từ ${toMillions(salary_min)}` : 'Thoả thuận'
    case 'UP_TO':
      return salary_max !== null ? `Tới ${toMillions(salary_max)}` : 'Thoả thuận'
    case 'AGREEMENT':
      return 'Thoả thuận'
  }
}

export function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('vi-VN')
}

/** Số ngày còn lại tới hạn nộp; âm nghĩa là đã quá hạn. */
export function daysUntil(isoDate: string): number {
  const millisecondsPerDay = 24 * 60 * 60 * 1000
  return Math.ceil((new Date(isoDate).getTime() - Date.now()) / millisecondsPerDay)
}

/** `<input type="date">` chỉ nhận YYYY-MM-DD, còn API trả về ISO đầy đủ. */
export function toDateInputValue(isoDate: string): string {
  return new Date(isoDate).toISOString().slice(0, 10)
}

/**
 * Ngày người dùng chọn -> hết ngày hôm đó theo giờ Việt Nam.
 *
 * Gửi kèm offset +07:00 chứ không để trình duyệt tự suy: máy đặt múi giờ khác
 * sẽ ra một thời điểm khác, và hạn nộp lệch cả nửa ngày so với ý người đăng.
 */
export function toDeadlineIso(dateInputValue: string): string {
  return `${dateInputValue}T23:59:59+07:00`
}
