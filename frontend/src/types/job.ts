export type JobStatus = 'DRAFT' | 'PUBLISHED' | 'CLOSED' | 'EXPIRED' | 'TAKEN_DOWN'
export type JobType = 'FULL_TIME' | 'PART_TIME' | 'CONTRACT' | 'INTERNSHIP' | 'FREELANCE'
export type ExperienceLevel = 'NO_EXP' | 'UNDER_1' | '1_2' | '2_3' | '3_5' | 'OVER_5'
export type Gender = 'NOT_REQUIRED' | 'MALE' | 'FEMALE'
export type SalaryType = 'RANGE' | 'FROM' | 'UP_TO' | 'AGREEMENT'

export interface JobLocation {
  id: string
  city_id: number
  address_detail: string | null
}

export interface JobLocationInput {
  city_id: number
  address_detail?: string | null
}

export interface JobListItem {
  id: string
  title: string
  slug: string
  category_id: string
  job_type: JobType
  experience_level: ExperienceLevel
  quantity: number
  salary_type: SalaryType
  salary_min: number | null
  salary_max: number | null
  currency: string
  deadline: string
  status: JobStatus
  takedown_reason: string | null
  is_hot: boolean
  view_count: number
  created_at: string
  locations: JobLocation[]
}

export interface Job extends JobListItem {
  company_id: string
  specialty: string | null
  gender: Gender
  description_html: string
  requirements_html: string
  benefits_html: string
  updated_at: string
}

/** Payload tạo tin. Sửa tin dùng cùng shape nhưng mọi trường đều tuỳ chọn. */
export interface JobInput {
  title: string
  category_id: string
  specialty: string | null
  job_type: JobType
  experience_level: ExperienceLevel
  gender: Gender
  quantity: number
  salary_type: SalaryType
  salary_min: number | null
  salary_max: number | null
  deadline: string
  description_html: string
  requirements_html: string
  benefits_html: string
  locations: JobLocationInput[]
  status?: Extract<JobStatus, 'DRAFT' | 'PUBLISHED'>
}

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  DRAFT: 'Nháp',
  PUBLISHED: 'Đang đăng',
  CLOSED: 'Đã đóng',
  EXPIRED: 'Hết hạn',
  TAKEN_DOWN: 'Bị gỡ',
}

export const JOB_TYPE_LABELS: Record<JobType, string> = {
  FULL_TIME: 'Toàn thời gian',
  PART_TIME: 'Bán thời gian',
  CONTRACT: 'Hợp đồng',
  INTERNSHIP: 'Thực tập',
  FREELANCE: 'Tự do',
}

export const EXPERIENCE_LABELS: Record<ExperienceLevel, string> = {
  NO_EXP: 'Không yêu cầu kinh nghiệm',
  UNDER_1: 'Dưới 1 năm',
  '1_2': '1 - 2 năm',
  '2_3': '2 - 3 năm',
  '3_5': '3 - 5 năm',
  OVER_5: 'Trên 5 năm',
}

export const GENDER_LABELS: Record<Gender, string> = {
  NOT_REQUIRED: 'Không yêu cầu',
  MALE: 'Nam',
  FEMALE: 'Nữ',
}

export const SALARY_TYPE_LABELS: Record<SalaryType, string> = {
  RANGE: 'Khoảng lương',
  FROM: 'Từ mức tối thiểu',
  UP_TO: 'Tới mức tối đa',
  AGREEMENT: 'Thoả thuận',
}

/** Kiểu lương nào cần ô nhập nào — dùng chung cho form và phần hiển thị. */
export const SALARY_FIELDS: Record<SalaryType, Array<'salary_min' | 'salary_max'>> = {
  RANGE: ['salary_min', 'salary_max'],
  FROM: ['salary_min'],
  UP_TO: ['salary_max'],
  AGREEMENT: [],
}
