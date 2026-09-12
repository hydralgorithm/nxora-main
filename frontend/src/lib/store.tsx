import { createContext, useContext, useState, type ReactNode } from 'react'
import type { Analysis } from './types'

// The whole latest /api/analyze response lives here; the chat panel and the
// candidate drawer both consume it. Persisted to sessionStorage so a page
// refresh on /results doesn't kill the demo (FRONTEND_SPEC §4).
const KEY = 'nxora-analysis'

interface Store {
  analysis: Analysis | null
  setAnalysis: (a: Analysis | null) => void
}

const Ctx = createContext<Store>({ analysis: null, setAnalysis: () => {} })

function readStored(): Analysis | null {
  try {
    const raw = sessionStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as Analysis) : null
  } catch {
    return null
  }
}

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [analysis, setAnalysisState] = useState<Analysis | null>(readStored)
  const setAnalysis = (a: Analysis | null) => {
    setAnalysisState(a)
    try {
      if (a) sessionStorage.setItem(KEY, JSON.stringify(a))
      else sessionStorage.removeItem(KEY)
    } catch {
      /* storage unavailable — in-memory demo still works */
    }
  }
  return <Ctx.Provider value={{ analysis, setAnalysis }}>{children}</Ctx.Provider>
}

export const useAnalysis = () => useContext(Ctx)
