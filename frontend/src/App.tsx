import { useState } from 'react'
import type { Analysis } from './lib/types'
import Landing from './pages/Landing'
import AnalysisScreen from './pages/Analysis'
import Results from './pages/Results'

type Screen = 'landing' | 'analysis' | 'results'

export default function App() {
  const [screen, setScreen] = useState<Screen>('landing')
  const [analysis, setAnalysis] = useState<Analysis | null>(null)

  if (screen === 'landing') {
    return <Landing onStart={() => setScreen('analysis')} />
  }

  if (screen === 'analysis') {
    return (
      <AnalysisScreen
        onComplete={(result) => {
          setAnalysis(result)
          setScreen('results')
        }}
        onCancel={() => setScreen('landing')}
      />
    )
  }

  return (
    analysis && (
      <Results
        analysis={analysis}
        onNewAnalysis={() => {
          setAnalysis(null)
          setScreen('analysis')
        }}
      />
    )
  )
}
