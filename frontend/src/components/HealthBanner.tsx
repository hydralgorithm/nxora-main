import { useEffect, useState } from 'react'
import { health, isMock } from '../lib/api'

// Polls GET /health every 10s (live mode only) and shows a persistent banner
// while the backend is down. The backend takes ~15–20s to boot its models,
// so the first poll runs immediately but the banner assumes online until
// proven otherwise (no offline flash on normal loads).
export default function HealthBanner() {
  const [online, setOnline] = useState(true)

  useEffect(() => {
    if (isMock) return
    let alive = true
    const poll = async () => {
      const ok = await health()
      if (alive) setOnline(ok)
    }
    poll()
    const id = setInterval(poll, 10_000)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [])

  if (online) return null
  return (
    <div
      role="alert"
      className="sticky top-0 z-50 bg-amber-50 border-b border-amber-200 px-4 py-2 text-center"
    >
      <p className="text-xs text-amber-800">
        Backend offline — start it with{' '}
        <code className="font-mono text-[11px]">
          cd backend && python -m uvicorn main:app --port 8000
        </code>
        . Retrying every 10s.
      </p>
    </div>
  )
}
