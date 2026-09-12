import { useRef, useState } from 'react'
import type { Analysis } from '../lib/types'
import { analyze } from '../lib/api'
import { IconFile } from '../components/Icon'

interface Props {
  onComplete: (analysis: Analysis) => void
  onCancel: () => void
}

type JdMode = 'file' | 'text'

const MAX_RESUMES = 50

// Pre-filled so a judge can demo in one click (FRONTEND_SPEC §3a). Contains a
// biased phrase + an over-constrained must-have list on purpose — it lights up
// the bias audit on the results screen.
const SAMPLE_JD = `Junior Full Stack Developer — TechNova Solutions

We're looking for a rockstar coder who ships fast. You'll build responsive interfaces with React, write server-side logic in Node.js, design and consume REST APIs, and work with MongoDB data models alongside a small product team.

Requirements: JavaScript, React, Node.js, MongoDB, REST APIs, Git, HTML/CSS, Docker, AWS, TypeScript.
Nice to have: Express.
0–2 years of experience — juniors encouraged to apply.`

export default function AnalysisScreen({ onComplete, onCancel }: Props) {
  const [jdMode, setJdMode] = useState<JdMode>('file')
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [jdText, setJdText] = useState(SAMPLE_JD)
  const [resumes, setResumes] = useState<File[]>([])
  const [jdDrag, setJdDrag] = useState(false)
  const [resDrag, setResDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const jdInputRef = useRef<HTMLInputElement>(null)
  const resInputRef = useRef<HTMLInputElement>(null)

  const jdReady = jdMode === 'file' ? jdFile !== null : jdText.trim().length > 0
  const canRun = jdReady && resumes.length > 0 && !busy

  async function run() {
    if (!canRun) return
    setBusy(true)
    setError(null)
    setElapsed(0)
    const started = Date.now()
    const timer = setInterval(() => setElapsed(Math.round((Date.now() - started) / 100) / 10), 100)
    try {
      const result = await analyze(
        jdMode === 'file' ? jdFile : null,
        jdMode === 'text' ? jdText.trim() : null,
        resumes,
      )
      onComplete(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
      setBusy(false)
    } finally {
      clearInterval(timer)
    }
  }

  function addResumes(files: FileList | null) {
    if (!files) return
    setResumes((prev) => {
      const seen = new Set(prev.map((f) => f.name + f.size))
      const fresh = Array.from(files).filter((f) => !seen.has(f.name + f.size))
      // Hard client-side cap (FRONTEND_SPEC §5: backend 400s above 50).
      return [...prev, ...fresh].slice(0, MAX_RESUMES)
    })
  }

  if (busy) {
    return (
      <main className="min-h-[100dvh] bg-zinc-100 flex items-center justify-center px-6">
        <div className="w-full max-w-md bg-white rounded-[10px] border border-zinc-200 p-6">
          <h1 className="text-base font-semibold tracking-tight">Analyzing candidates</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Scoring {resumes.length} {resumes.length === 1 ? 'resume' : 'resumes'} against the job
            description — keyword and semantic tracks, side by side.
          </p>
          <div className="mt-5 space-y-2.5" aria-live="polite">
            {['Parsing resumes', 'Matching skills against the JD', 'Ranking candidates'].map(
              (step, i) => (
                <div key={step} className="flex items-center gap-3">
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse"
                    style={{ animationDelay: `${i * 300}ms` }}
                  />
                  <span className="text-sm text-zinc-700">{step}</span>
                </div>
              ),
            )}
          </div>
          <p className="font-mono text-[11px] text-zinc-500 mt-5">
            {elapsed.toFixed(1)}s elapsed · hybrid engine · local
          </p>
          <p className="text-[11px] text-zinc-400 mt-1">
            Takes 2–8s warm. First run after a server start loads the AI models — up to 20s.
          </p>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-[100dvh] bg-zinc-100 flex items-center justify-center px-6 py-10">
      <div className="w-full max-w-2xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="font-semibold tracking-tight text-[15px]">Shortlist</span>
            <span className="text-zinc-300">/</span>
            <span className="text-sm text-zinc-600">New analysis</span>
          </div>
          <button
            onClick={onCancel}
            className="text-sm text-zinc-500 hover:text-zinc-900 transition-colors"
          >
            Back
          </button>
        </div>

        {error && (
          <div className="mb-4 flex items-start gap-3 rounded-[10px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            <p className="flex-1">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-rose-400 hover:text-rose-700 transition-colors shrink-0"
              aria-label="Dismiss error"
            >
              <svg viewBox="0 0 16 16" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                <path d="M4 4l8 8M12 4l-8 8" />
              </svg>
            </button>
          </div>
        )}

        {/* Job description */}
        <section className="bg-white rounded-[10px] border border-zinc-200 p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold">Job description</h2>
            <div className="flex rounded-md border border-zinc-200 p-0.5">
              {(['file', 'text'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setJdMode(mode)}
                  className={`text-xs px-2.5 py-1 rounded-[5px] transition-colors ${
                    jdMode === mode ? 'bg-blue-600 text-white' : 'text-zinc-500 hover:text-zinc-800'
                  }`}
                >
                  {mode === 'file' ? 'Upload PDF' : 'Paste text'}
                </button>
              ))}
            </div>
          </div>

          {jdMode === 'file' ? (
            jdFile ? (
              <div className="flex items-center gap-3 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2.5">
                <IconFile className="w-4 h-4 text-zinc-500 shrink-0" />
                <span className="text-sm flex-1 truncate">{jdFile.name}</span>
                <span className="font-mono text-[11px] text-zinc-500">
                  {(jdFile.size / 1024).toFixed(0)} KB
                </span>
                <button
                  onClick={() => setJdFile(null)}
                  className="text-zinc-500 hover:text-rose-600 transition-colors text-sm"
                  aria-label="Remove job description"
                >
                  Remove
                </button>
              </div>
            ) : (
              <button
                onClick={() => jdInputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setJdDrag(true) }}
                onDragLeave={() => setJdDrag(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setJdDrag(false)
                  const f = e.dataTransfer.files?.[0]
                  if (f) setJdFile(f)
                }}
                className={`w-full rounded-md border border-dashed px-4 py-8 text-sm transition-colors ${
                  jdDrag
                    ? 'border-blue-600 bg-blue-50/50 text-blue-700'
                    : 'border-zinc-300 text-zinc-500 hover:border-zinc-400 hover:text-zinc-600'
                }`}
              >
                Drop the JD PDF here, or click to browse
              </button>
            )
          ) : (
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the full job description text…"
              rows={6}
              className="w-full rounded-md border border-zinc-200 px-3 py-2.5 text-sm resize-y placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600"
            />
          )}
          <input
            ref={jdInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.xml"
            className="hidden"
            onChange={(e) => setJdFile(e.target.files?.[0] ?? null)}
          />
        </section>

        {/* Resumes */}
        <section className="bg-white rounded-[10px] border border-zinc-200 p-5 mt-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold">
              Resumes
              {resumes.length > 0 && (
                <span className="ml-2 font-mono text-[11px] font-normal text-zinc-500">
                  {resumes.length} / {MAX_RESUMES} files
                </span>
              )}
            </h2>
          </div>

          <button
            onClick={() => resInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setResDrag(true) }}
            onDragLeave={() => setResDrag(false)}
            onDrop={(e) => {
              e.preventDefault()
              setResDrag(false)
              addResumes(e.dataTransfer.files)
            }}
            className={`w-full rounded-md border border-dashed px-4 py-8 text-sm transition-colors ${
              resDrag
                ? 'border-blue-600 bg-blue-50/50 text-blue-700'
                : 'border-zinc-300 text-zinc-500 hover:border-zinc-400 hover:text-zinc-600'
            }`}
          >
            Drop resumes here, or click to browse — up to {MAX_RESUMES} files
          </button>
          <input
            ref={resInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.xml,.html,.txt"
            multiple
            className="hidden"
            onChange={(e) => addResumes(e.target.files)}
          />

          {resumes.length > 0 && (
            <ul className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {resumes.map((f) => (
                <li
                  key={f.name + f.size}
                  className="flex items-center gap-2 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2"
                >
                  <IconFile className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                  <span className="text-[13px] flex-1 truncate">{f.name}</span>
                  <button
                    onClick={() => setResumes((prev) => prev.filter((x) => x !== f))}
                    className="text-zinc-500 hover:text-rose-600 transition-colors text-xs"
                    aria-label={`Remove ${f.name}`}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <div className="flex items-center justify-between mt-6">
          <p className="text-xs text-zinc-500 max-w-[36ch]">
            Scoring runs locally: keyword and semantic tracks, blended 50/50. No LLM in the ranking
            path.
          </p>
          <button
            onClick={run}
            disabled={!canRun}
            className={`text-sm font-medium px-5 py-2.5 rounded-[10px] transition-colors ${
              canRun
                ? 'bg-blue-600 text-white hover:bg-blue-700 active:translate-y-[1px]'
                : 'bg-zinc-200 text-zinc-400 cursor-not-allowed'
            }`}
          >
            Analyze & Rank
          </button>
        </div>
      </div>
    </main>
  )
}
