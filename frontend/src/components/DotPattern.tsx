import { useId } from 'react'

interface Props {
  width?: number
  height?: number
  cr?: number
  className?: string
}

// Subtle dot-grid background, Magic UI pattern
// (https://magicui.design/docs/components/dot-pattern). Fade it with a mask
// via className, e.g. [mask-image:radial-gradient(...)].
export function DotPattern({ width = 16, height = 16, cr = 1, className }: Props) {
  const id = useId()
  return (
    <svg
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 w-full h-full ${className ?? ''}`}
    >
      <defs>
        <pattern id={id} width={width} height={height} patternUnits="userSpaceOnUse">
          <circle cx={1} cy={1} r={cr} />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id})`} />
    </svg>
  )
}
