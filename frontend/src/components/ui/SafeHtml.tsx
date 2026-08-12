import DOMPurify from 'dompurify'
import { useMemo } from 'react'

/**
 * Lớp phòng thủ XSS thứ hai (DESIGN mục 6.4).
 *
 * Lớp chính là `bleach` ở backend — dữ liệu đã sạch từ lúc lưu. Vẫn lọc lại ở
 * đây vì `dangerouslySetInnerHTML` bỏ qua toàn bộ cơ chế escape của React: chỉ
 * cần một đường nào đó (import dữ liệu cũ, sửa tay trong DB, endpoint mới quên
 * sanitize) là HTML bẩn ra thẳng trình duyệt người dùng.
 */

// Giữ khớp với ALLOWED_TAGS/ALLOWED_ATTRIBUTES trong backend/app/utils/sanitize.py.
// Lệch nhau thì hoặc mất định dạng, hoặc thừa bề mặt tấn công.
const ALLOWED_TAGS = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h3', 'ul', 'ol', 'li', 'a']
const ALLOWED_ATTR = ['href', 'title', 'target', 'rel']

// Link trong tin tuyển dụng trỏ ra ngoài. `noopener` chặn trang đích chiếm
// quyền điều khiển tab gốc qua `window.opener`.
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A' && node.getAttribute('href')) {
    node.setAttribute('target', '_blank')
    node.setAttribute('rel', 'noopener noreferrer')
  }
})

interface SafeHtmlProps {
  html: string
  className?: string
}

export function SafeHtml({ html, className = '' }: SafeHtmlProps) {
  const clean = useMemo(
    () => DOMPurify.sanitize(html, { ALLOWED_TAGS, ALLOWED_ATTR }),
    [html],
  )

  return (
    <div className={`rich-text ${className}`} dangerouslySetInnerHTML={{ __html: clean }} />
  )
}
