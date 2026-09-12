import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'motion/react'

interface Props {
  children: ReactNode
  delay?: number
  direction?: 'up' | 'down'
  className?: string
}

// Blur+rise entrance, Magic UI pattern (https://magicui.design/docs/components/blur-fade),
// adapted: runs on mount, honors prefers-reduced-motion.
export function BlurFade({ children, delay = 0, direction = 'up', className }: Props) {
  const reduced = useReducedMotion()
  return (
    <motion.div
      className={className}
      initial={reduced ? false : { opacity: 0, filter: 'blur(6px)', y: direction === 'up' ? 8 : -8 }}
      animate={{ opacity: 1, filter: 'blur(0px)', y: 0 }}
      transition={{ duration: 0.55, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  )
}
