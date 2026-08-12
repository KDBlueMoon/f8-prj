import type { ReactNode } from 'react'
import type { CompanyStatus } from '@/types/auth'
import { COMPANY_STATUS_LABELS } from '@/types/company'
import { JOB_STATUS_LABELS, type JobStatus } from '@/types/job'

type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

const TONE_CLASSES: Record<Tone, string> = {
  neutral: 'border-slate-200 bg-slate-100 text-slate-600',
  success: 'border-green-200 bg-brand-light text-brand-dark',
  warning: 'border-amber-300 bg-amber-50 text-amber-800',
  danger: 'border-red-200 bg-red-50 text-red-700',
  info: 'border-blue-200 bg-blue-50 text-blue-700',
}

export function Badge({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-block rounded border px-2 py-1 text-xs font-medium ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  )
}

const STATUS_TONES: Record<CompanyStatus, Tone> = {
  PENDING: 'warning',
  APPROVED: 'success',
  REJECTED: 'danger',
}

export function CompanyStatusBadge({ status }: { status: CompanyStatus }) {
  return <Badge tone={STATUS_TONES[status]}>{COMPANY_STATUS_LABELS[status]}</Badge>
}

const JOB_STATUS_TONES: Record<JobStatus, Tone> = {
  DRAFT: 'neutral',
  PUBLISHED: 'success',
  CLOSED: 'info',
  EXPIRED: 'warning',
  TAKEN_DOWN: 'danger',
}

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return <Badge tone={JOB_STATUS_TONES[status]}>{JOB_STATUS_LABELS[status]}</Badge>
}
