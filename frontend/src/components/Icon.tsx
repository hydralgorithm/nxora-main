// Authored icons — one stroke weight (1.5), one 16px grid, currentColor.
// Small on purpose; extend only with glyphs that match this system.
export function IconAlert({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M8 2.5 14 13H2L8 2.5Z" />
      <path d="M8 6.75v2.5" />
      <circle cx="8" cy="11.6" r="0.15" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function IconArrowRight({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M3 8h10" />
      <path d="M9 4l4 4-4 4" />
    </svg>
  )
}

export function IconFile({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M4 1.75h5L12.25 5v9.25H4V1.75Z" />
      <path d="M9 1.75V5h3.25" />
    </svg>
  )
}

export function IconChat({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M2.5 3.5h11v7.5h-6L4 13.5V11H2.5V3.5Z" />
    </svg>
  )
}

export function IconSend({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M2.5 8 13.5 3 9.5 13.5 7.75 9.25 2.5 8Z" />
    </svg>
  )
}

export function IconClose({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M4 4l8 8M12 4l-8 8" />
    </svg>
  )
}
