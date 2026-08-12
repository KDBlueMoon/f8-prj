import { z } from 'zod'

/**
 * Các luật ở đây phải khớp với validator phía backend (app/schemas/auth.py).
 * Kiểm tra ở client chỉ để báo lỗi sớm cho người dùng — backend mới là chốt chặn.
 */

const MIN_PASSWORD_LENGTH = 8
const PHONE_PATTERN = /^0\d{9,10}$/
const TAX_CODE_PATTERN = /^\d{10}$|^\d{13}$/

const email = z.string().min(1, 'Vui lòng nhập email').email('Email không hợp lệ')

const password = z
  .string()
  .min(MIN_PASSWORD_LENGTH, `Mật khẩu phải có tối thiểu ${MIN_PASSWORD_LENGTH} ký tự`)
  .refine((value) => value.trim().length >= MIN_PASSWORD_LENGTH, {
    message: 'Mật khẩu không được chủ yếu là khoảng trắng',
  })
  .refine((value) => /[a-zA-Z]/.test(value), { message: 'Mật khẩu phải có ít nhất một chữ cái' })
  .refine((value) => /\d/.test(value), { message: 'Mật khẩu phải có ít nhất một chữ số' })

const optionalPhone = z
  .string()
  .trim()
  .refine((value) => value === '' || PHONE_PATTERN.test(value), {
    message: 'Số điện thoại phải gồm 10-11 chữ số và bắt đầu bằng 0',
  })

const requiredPhone = z
  .string()
  .trim()
  .regex(PHONE_PATTERN, 'Số điện thoại phải gồm 10-11 chữ số và bắt đầu bằng 0')

export const loginSchema = z.object({
  email,
  password: z.string().min(1, 'Vui lòng nhập mật khẩu'),
})

export const candidateRegisterSchema = z
  .object({
    email,
    password,
    confirm_password: z.string(),
    full_name: z.string().trim().min(2, 'Vui lòng nhập họ tên'),
    phone_number: optionalPhone,
  })
  .refine((values) => values.password === values.confirm_password, {
    message: 'Mật khẩu nhập lại không khớp',
    path: ['confirm_password'],
  })

export const companySizeSchema = z.enum([
  '1-9',
  '10-24',
  '25-99',
  '100-499',
  '500-1000',
  '1000+',
])

export const employerRegisterSchema = z
  .object({
    email,
    password,
    confirm_password: z.string(),
    full_name: z.string().trim().min(2, 'Vui lòng nhập họ tên'),
    phone_number: optionalPhone,
    company: z.object({
      tax_code: z
        .string()
        .trim()
        .regex(TAX_CODE_PATTERN, 'Mã số thuế phải gồm 10 hoặc 13 chữ số'),
      company_name: z.string().trim().min(2, 'Vui lòng nhập tên công ty'),
      international_name: z.string().trim(),
      short_name: z.string().trim(),
      director: z.string().trim().min(2, 'Vui lòng nhập người đại diện'),
      headquarters_address: z.string().trim().min(5, 'Vui lòng nhập địa chỉ trụ sở'),
      email,
      phone_number: requiredPhone,
      company_size: companySizeSchema,
      website: z.string().trim(),
      category_group_id: z.string().trim(),
    }),
  })
  .refine((values) => values.password === values.confirm_password, {
    message: 'Mật khẩu nhập lại không khớp',
    path: ['confirm_password'],
  })

export type LoginValues = z.infer<typeof loginSchema>
export type CandidateRegisterValues = z.infer<typeof candidateRegisterSchema>
export type EmployerRegisterValues = z.infer<typeof employerRegisterSchema>
