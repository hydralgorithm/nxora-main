import { useState } from 'react'
import { motion, useReducedMotion, type Variants } from 'motion/react'
import type { Analysis } from '../lib/types'
import { SkillChipGroup } from '../components/SkillChips'
import CandidateDetail from '../components/CandidateDetail'
import { IconAlert } from '../components/Icon'

interface Props {
  analysis: Analysis
  onNewAnalysis: () => void
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-12 text-[10px] uppercase tracking-wide text-zinc-500">{label}</span>
      <div className="h-1 flex-1 rounded-full bg-zinc-200 overflow-hidden">
        <div
          className={`h-full rounded-full ${
            value >= 70 ? 'bg-emerald-500' : value >= 40 ? 'bg-amber-500' : 'bg-rose-400'
          }`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="font-mono text-[11px] text-zinc-600 w-7 text-right">
        {value.toFixed(0)}
      </span>
    </div>
  )
}

export default function Results({ analysis, onNewAnalysis }: Props) {
  const [selectedRank, setSelectedRank] = useState(1)
  const selected = analysis.ranking.find((c) => c.rank === selectedRank) ?? analysis.ranking[0]
  const top = analysis.ranking[0]
  const reduced = useReducedMotion()

  // Cascade the ranked rows in once, top of the list first (21st.dev
  // animated-list pattern). Skipped entirely under prefers-reduced-motion.
  const listVariants: Variants = {
    hidden: {},
    visible: { transition: { staggerChildren: reduced ? 0 : 0.022 } },
  }
  const rowVariants: Variants = {
    hidden: reduced ? {} : { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] } },
  }

  return (
    <div className="min-h-[100dvh] bg-zinc-100">
      {/* Top bar */}
      <header className="bg-white border-b border-zinc-200 px-5 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-semibold tracking-tight text-[15px]">Shortlist</span>
          <span className="text-zinc-300">/</span>
          <span className="text-sm text-zinc-600 truncate max-w-[40ch]">{analysis.jd.title}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="hidden md:inline font-mono text-[11px] text-zinc-500">
            {analysis.meta.resumes_processed} resumes · {(analysis.meta.elapsed_ms / 1000).toFixed(1)}s · {analysis.meta.engine}
          </span>
          <button
            onClick={onNewAnalysis}
            className="text-sm font-medium px-3.5 py-1.5 rounded-[8px] bg-blue-600 text-white hover:bg-blue-700 active:translate-y-[1px] transition-colors"
          >
            New analysis
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr_360px] gap-4 p-4 max-w-[1600px] mx-auto">
        {/* Column 1: JD sidebar */}
        <aside className="space-y-4">
          <section className="bg-white rounded-[10px] border border-zinc-200 p-4">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-1">
              Job description
            </h2>
            <p className="text-sm font-medium">{analysis.jd.title}</p>
            <p className="text-xs text-zinc-500">{analysis.jd.company}</p>

            <div className="mt-4 space-y-3">
              <div>
                <p className="text-[11px] font-medium text-zinc-500 mb-1.5">
                  Required · weight ×3
                </p>
                <SkillChipGroup skills={analysis.jd.required_skills} variant="matched" max={8} />
              </div>
              <div>
                <p className="text-[11px] font-medium text-zinc-500 mb-1.5">Nice to have · ×1</p>
                <SkillChipGroup skills={analysis.jd.nice_skills} variant="partial" max={6} />
              </div>
            </div>
          </section>

          {analysis.bias_flags.length > 0 && (
            <section className="bg-white rounded-[10px] border border-zinc-200 p-4">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2">
                JD audit
              </h2>
              <ul className="space-y-3">
                {analysis.bias_flags.map((flag, i) => (
                  <li key={i} className="text-xs leading-relaxed">
                    <p className="flex gap-2">
                      <IconAlert className="w-3.5 h-3.5 mt-px shrink-0 text-amber-600" />
                      <span className="text-zinc-800 font-medium">“{flag.phrase}”</span>
                    </p>
                    <p className="text-zinc-600 mt-1 pl-[22px]">{flag.why}</p>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </aside>

        {/* Column 2: ranked list */}
        <main className="bg-white rounded-[10px] border border-zinc-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-zinc-200 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Ranked candidates</h2>
            <span className="font-mono text-[11px] text-zinc-500">
              hybrid · keyword + semantic
            </span>
          </div>
          <motion.ul
            className="divide-y divide-zinc-100"
            variants={listVariants}
            initial="hidden"
            animate="visible"
          >
            {analysis.ranking.map((c) => {
              const isSel = c.rank === selected.rank
              return (
                <motion.li key={c.rank} variants={rowVariants}>
                  <button
                    onClick={() => setSelectedRank(c.rank)}
                    aria-current={isSel ? 'true' : undefined}
                    className={`w-full text-left px-4 py-3 flex items-center gap-4 transition-colors ${
                      isSel ? 'bg-blue-50/70' : 'hover:bg-zinc-50'
                    }`}
                  >
                    <span
                      className={`font-mono text-xs w-5 shrink-0 ${
                        isSel ? 'text-blue-700 font-semibold' : 'text-zinc-500'
                      }`}
                    >
                      {c.rank}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline gap-2">
                        <span
                          className={`text-sm truncate ${
                            isSel ? 'font-semibold text-zinc-900' : 'font-medium text-zinc-800'
                          }`}
                        >
                          {c.name}
                        </span>
                        {c.rank <= 3 && (
                          <span className="text-[10px] font-medium text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded shrink-0">
                            top 3
                          </span>
                        )}
                      </div>
                      <p className="font-mono text-[11px] text-zinc-500 truncate">{c.file}</p>
                    </div>
                    <div className="hidden sm:block w-36 space-y-1 shrink-0">
                      <ScoreBar label="KW" value={c.keyword_score} />
                      <ScoreBar label="SEM" value={c.semantic_score} />
                    </div>
                    <span
                      className={`font-mono text-sm font-semibold w-10 text-right shrink-0 ${
                        c.overall_score >= 70
                          ? 'text-emerald-700'
                          : c.overall_score >= 40
                            ? 'text-amber-700'
                            : 'text-zinc-500'
                      }`}
                    >
                      {c.overall_score.toFixed(1)}
                    </span>
                  </button>
                </motion.li>
              )
            })}
          </motion.ul>
        </main>

        {/* Column 3: candidate detail */}
        <aside>
          <CandidateDetail candidate={selected} topOverall={top.overall_score} />
        </aside>
      </div>
    </div>
  )
}
