import { useRef, type ReactNode, type PointerEvent } from 'react'
import {
  motion,
  useMotionValue,
  useSpring,
  useTransform,
  useReducedMotion,
} from 'motion/react'

interface Props {
  children: ReactNode
  className?: string
  /** Max tilt in degrees at the card edges */
  maxTilt?: number
}

// Floating, pointer-tilting card — React Bits "Tilted Card" pattern
// (https://reactbits.dev/backgrounds/tilted-card), adapted. Pure CSS 3D
// transforms via Motion; no Three.js, since one card doesn't justify a
// WebGL context. Idle float + tilt + a ground shadow that breathes in sync.
export function TiltedCard({ children, className, maxTilt = 7 }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()

  // Pointer position on the card, normalized to 0..1. Springs smooth the tilt.
  const px = useMotionValue(0.5)
  const py = useMotionValue(0.5)
  const sx = useSpring(px, { stiffness: 280, damping: 26 })
  const sy = useSpring(py, { stiffness: 280, damping: 26 })
  const rotateY = useTransform(sx, [0, 1], [-maxTilt, maxTilt])
  const rotateX = useTransform(sy, [0, 1], [maxTilt, -maxTilt])

  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    const r = ref.current?.getBoundingClientRect()
    if (!r) return
    px.set((e.clientX - r.left) / r.width)
    py.set((e.clientY - r.top) / r.height)
  }
  const onPointerLeave = () => {
    px.set(0.5)
    py.set(0.5)
  }

  if (reduced) {
    return <div className={className}>{children}</div>
  }

  return (
    <div className={`relative ${className ?? ''}`} style={{ perspective: 1100 }}>
      {/* Ground shadow — scales/fades in sync with the 7s idle float */}
      <motion.div
        aria-hidden="true"
        className="absolute -bottom-7 left-1/2 -translate-x-1/2 h-8 w-[78%] rounded-[100%] bg-zinc-900/[0.07] blur-xl"
        animate={{ opacity: [0.75, 0.45, 0.75], scale: [1, 0.93, 1] }}
        transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        ref={ref}
        onPointerMove={onPointerMove}
        onPointerLeave={onPointerLeave}
        style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
        className="will-change-transform"
      >
        {children}
      </motion.div>
    </div>
  )
}
