import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { AnalysisProvider, useAnalysis } from './lib/store'
import HealthBanner from './components/HealthBanner'
import Landing from './pages/Landing'
import AnalysisScreen from './pages/Analysis'
import Results from './pages/Results'

function Shell() {
  const { analysis, setAnalysis } = useAnalysis()
  const navigate = useNavigate()

  return (
    <>
      <HealthBanner />
      <Routes>
        <Route path="/" element={<Landing onStart={() => navigate('/upload')} />} />
        <Route
          path="/upload"
          element={
            <AnalysisScreen
              onComplete={(a) => {
                setAnalysis(a)
                navigate('/results')
              }}
              onCancel={() => navigate('/')}
            />
          }
        />
        <Route
          path="/results"
          element={
            analysis ? (
              <Results analysis={analysis} onNewAnalysis={() => navigate('/upload')} />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        {/* Unknown routes → home (FRONTEND_SPEC §4) */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AnalysisProvider>
        <Shell />
      </AnalysisProvider>
    </BrowserRouter>
  )
}
