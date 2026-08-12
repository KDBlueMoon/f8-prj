import { EditorContent, useEditor, useEditorState } from '@tiptap/react'
import type { Editor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import type { ReactNode } from 'react'

/**
 * Trình soạn thảo cho mô tả tin tuyển dụng (DESIGN mục 6.4).
 *
 * Toolbar cố tình hẹp: đậm, nghiêng, gạch chân, H3, hai kiểu danh sách, link,
 * hoàn tác. Không có chèn ảnh/iframe/màu chữ — vừa giảm bề mặt tấn công, vừa
 * giữ mọi tin tuyển dụng nhìn đồng nhất.
 */

// Đúng bằng whitelist của backend. Tắt hẳn những phần StarterKit bật sẵn nhưng
// backend sẽ gỡ đi, để người dùng không định dạng xong rồi mất trắng khi lưu.
const DISABLED_EXTENSIONS = {
  strike: false,
  code: false,
  codeBlock: false,
  blockquote: false,
  horizontalRule: false,
} as const

const HEADING_LEVEL = 3

interface RichTextEditorProps {
  label: string
  value: string
  onChange: (html: string) => void
  required?: boolean
  error?: string
  hint?: ReactNode
}

export function RichTextEditor({
  label,
  value,
  onChange,
  required,
  error,
  hint,
}: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        ...DISABLED_EXTENSIONS,
        heading: { levels: [HEADING_LEVEL] },
        link: {
          openOnClick: false,
          // Chỉ 3 giao thức này, khớp với ALLOWED_PROTOCOLS của backend —
          // `javascript:` bị chặn ngay trong trình soạn thảo.
          protocols: ['http', 'https', 'mailto'],
        },
      }),
    ],
    content: value,
    // Nội dung được đọc ngược lại từ editor, không phải từ prop: gán lại content
    // mỗi lần render sẽ nhảy con trỏ về đầu bài trong lúc người dùng đang gõ.
    onUpdate: ({ editor: instance }) => onChange(instance.getHTML()),
    editorProps: {
      attributes: {
        class: 'rich-text min-h-40 px-3 py-2.5 text-sm outline-none',
      },
    },
  })

  return (
    <div>
      <span className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </span>

      <div
        className={[
          'overflow-hidden rounded-lg border bg-white transition',
          'focus-within:ring-2 focus-within:ring-brand/20',
          error ? 'border-red-400 focus-within:border-red-500' : 'border-slate-300 focus-within:border-brand',
        ].join(' ')}
      >
        <Toolbar editor={editor} />
        <EditorContent editor={editor} />
      </div>

      {error ? (
        <span role="alert" className="mt-1 block text-xs text-red-600">
          {error}
        </span>
      ) : (
        hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>
      )}
    </div>
  )
}

function Toolbar({ editor }: { editor: Editor | null }) {
  // TipTap v3 không tự render lại theo từng transaction; hook này chỉ lấy đúng
  // phần state mà toolbar cần nên bấm phím không kéo theo render cả trang.
  const state = useEditorState({
    editor,
    selector: ({ editor: instance }) => ({
      bold: instance?.isActive('bold') ?? false,
      italic: instance?.isActive('italic') ?? false,
      underline: instance?.isActive('underline') ?? false,
      heading: instance?.isActive('heading', { level: HEADING_LEVEL }) ?? false,
      bulletList: instance?.isActive('bulletList') ?? false,
      orderedList: instance?.isActive('orderedList') ?? false,
      link: instance?.isActive('link') ?? false,
      canUndo: instance?.can().undo() ?? false,
      canRedo: instance?.can().redo() ?? false,
    }),
  })

  if (!editor || !state) return null

  const toggleLink = () => {
    if (state.link) {
      editor.chain().focus().unsetLink().run()
      return
    }
    const url = window.prompt('Nhập địa chỉ liên kết (bắt đầu bằng https://)')
    if (!url) return
    editor.chain().focus().setLink({ href: url }).run()
  }

  return (
    <div className="flex flex-wrap items-center gap-1 border-b border-slate-200 bg-slate-50 px-2 py-1.5">
      <ToolbarButton
        label="Đậm"
        active={state.bold}
        onClick={() => editor.chain().focus().toggleBold().run()}
      >
        <span className="font-bold">B</span>
      </ToolbarButton>
      <ToolbarButton
        label="Nghiêng"
        active={state.italic}
        onClick={() => editor.chain().focus().toggleItalic().run()}
      >
        <span className="italic">I</span>
      </ToolbarButton>
      <ToolbarButton
        label="Gạch chân"
        active={state.underline}
        onClick={() => editor.chain().focus().toggleUnderline().run()}
      >
        <span className="underline">U</span>
      </ToolbarButton>

      <Divider />

      <ToolbarButton
        label="Tiêu đề mục"
        active={state.heading}
        onClick={() => editor.chain().focus().toggleHeading({ level: HEADING_LEVEL }).run()}
      >
        H3
      </ToolbarButton>
      <ToolbarButton
        label="Gạch đầu dòng"
        active={state.bulletList}
        onClick={() => editor.chain().focus().toggleBulletList().run()}
      >
        •
      </ToolbarButton>
      <ToolbarButton
        label="Danh sách đánh số"
        active={state.orderedList}
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
      >
        1.
      </ToolbarButton>
      <ToolbarButton label="Chèn liên kết" active={state.link} onClick={toggleLink}>
        🔗
      </ToolbarButton>

      <Divider />

      <ToolbarButton
        label="Hoàn tác"
        disabled={!state.canUndo}
        onClick={() => editor.chain().focus().undo().run()}
      >
        ↶
      </ToolbarButton>
      <ToolbarButton
        label="Làm lại"
        disabled={!state.canRedo}
        onClick={() => editor.chain().focus().redo().run()}
      >
        ↷
      </ToolbarButton>
    </div>
  )
}

function Divider() {
  return <span className="mx-1 h-5 w-px bg-slate-300" />
}

interface ToolbarButtonProps {
  label: string
  active?: boolean
  disabled?: boolean
  onClick: () => void
  children: ReactNode
}

function ToolbarButton({ label, active, disabled, onClick, children }: ToolbarButtonProps) {
  return (
    <button
      // Mặc định của <button> trong <form> là submit — bấm "Đậm" mà gửi cả form
      // thì tin bị lưu giữa chừng.
      type="button"
      title={label}
      aria-label={label}
      aria-pressed={active}
      disabled={disabled}
      onClick={onClick}
      className={[
        'grid h-8 min-w-8 place-items-center rounded px-1.5 text-sm transition',
        'disabled:cursor-not-allowed disabled:opacity-40',
        active ? 'bg-brand-light text-brand-dark' : 'text-slate-600 hover:bg-slate-200',
      ].join(' ')}
    >
      {children}
    </button>
  )
}
