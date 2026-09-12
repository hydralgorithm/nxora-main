import { useEffect, useRef, useState } from 'react'
import { animate, useInView, useReducedMotion } from 'motion/react'

interface Props {
  value: number
  delay?: number
  decimalPlaces?: number
  duration?: number
  className?: string
}

// Count-up number, Magic UI pattern (https://magicui.design/docs/components/number-ticker),
// adapted: settles from the current value on prop change, honors prefers-reduced-motion.
export function NumberTicker({
  value,
  delay = 0,
  decimalPlaces = 0,
  duration = 0.9,
  className,
}: Props) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true })
  const reduced = useReducedMotion()
  // Start from 0 so the first reveal counts up; later prop changes roll from
  // the previous value. Reduced motion just shows the value.
  const [display, setDisplay] = useState(() => (reduced ? value : 0))

  useEffect(() => {
    if (!inView) return
    if (reduced) {
      setDisplay(value)
      return
    }
    const controls = animate(display, value, {
      duration,
      delay,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (latest) => setDisplay(latest),
    })
    return () => controls.stop()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inView, value, reduced])

  return (
    <span ref={ref} className={className}>
      {display.toFixed(decimalPlaces)}
    </span>
  )
}
