import { useState } from 'react'
import { motion, useReducedMotion, type Variants } from 'motion/react'
import type { Analysis, Band } from '../lib/types'
import { SkillChipGroup } from '../components/SkillChips'
import CandidateDetail from '../components/CandidateDetail'
import ChatPanel from '../components/ChatPanel'
import { IconAlert } from '../components/Icon'

interface Props {
  analysis: Analysis
  onNewAnalysis: () => void
}

const BAND_STYLE: Record<Band, string> = {
  strong: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  weak: 'bg-zinc-100 text-zinc-500',
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

/** Pool-aware flags call out a skill screening out the uploaded pool; the rest are JD wording. */
const isPoolFlag = (phrase: string) => phrase.includes('candidates show it')

export default function Results({ analysis, onNewAnalysis }: Props) {
  const [selectedRank, setSelectedRank] = useState(1)
  const [bandFilter, setBandFilter] = useState<'all' | Band>('all')
  const selected = analysis.ranking.find((c) => c.rank === selectedRank) ?? analysis.ranking[0]
  const top = analysis.ranking[0]
  const reduced = useReducedMotion()

  const visible =
    bandFilter === 'all' ? analysis.ranking : analysis.ranking.filter((c) => c.band === bandFilter)
  const bandCount = (b: Band) => analysis.ranking.filter((c) => c.band === b).length

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

  const top3 = analysis.ranking.filter((c) => c.explanation).slice(0, 3)

  return (
    <div className="min-h-[100dvh] bg-zinc-100">
      {/* Top bar */}
      <header className="bg-white border-b border-zinc-200 px-5 h-14 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span className="font-semibold tracking-tight text-[15px] shrink-0">Shortlist</span>
          <span className="text-zinc-300">/</span>
          <span className="text-sm text-zinc-600 truncate max-w-[32ch]">
            {analysis.jd.title ?? 'Job Description'}
          </span>
          {analysis.meta.duplicates_removed > 0 && (
            <span className="group relative shrink-0">
              <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] font-medium text-zinc-600 bg-zinc-100 border border-zinc-200 rounded-full px-2.5 py-0.5 cursor-default">
                <IconAlert className="w-3 h-3 text-zinc-400" />
                {analysis.meta.duplicates_removed} duplicate
                {analysis.meta.duplicates_removed > 1 ? 's' : ''} merged
              </span>
              <span className="hidden group-hover:block absolute left-0 top-full mt-2 z-40 w-72 bg-white border border-zinc-200 rounded-[10px] shadow-[0_8px_24px_rgba(24,24,27,0.1)] p-3 text-left">
                <span className="block text-[11px] font-semibold text-zinc-700 mb-1.5">
                  Merged by matching email
                </span>
                {analysis.meta.duplicates.map((d) => (
                  <span key={d.file} className="block text-[11px] text-zinc-600 leading-relaxed">
                    {d.name} — <span className="font-mono">{d.file}</span> merged into{' '}
                    <span className="font-mono">{d.kept_file}</span>
                  </span>
                ))}
              </span>
            </span>
          )}
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <span className="hidden lg:inline font-mono text-[11px] text-zinc-500">
            ranked in {(analysis.meta.elapsed_ms / 1000).toFixed(1)}s · {analysis.meta.engine}
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
        {/* Column 1: JD + bias audit */}
        <aside className="space-y-4">
          <section className="bg-white rounded-[10px] border border-zinc-200 p-4">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-1">
              Job description
            </h2>
            <p className="text-sm font-medium">{analysis.jd.title ?? 'Job Description'}</p>
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

          {/* Bias & pool health — the clean result is itself a feature, so this
              section never hides (FRONTEND_SPEC §3d). */}
          <section className="bg-white rounded-[10px] border border-zinc-200 p-4">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2.5">
              Bias & pool health
            </h2>
            {analysis.bias_flags.length === 0 ? (
              <div className="rounded-md bg-emerald-50 border border-emerald-100 px-3 py-2.5">
                <p className="text-xs text-emerald-800 font-medium">
                  No bias signals detected in this JD or pool
                </p>
              </div>
            ) : (
              <ul className="space-y-3">
                {analysis.bias_flags.map((flag, i) => (
                  <li key={i} className="text-xs leading-relaxed">
                    <span
                      className={`inline-block text-[10px] font-medium px-1.5 py-0.5 rounded mb-1.5 ${
                        isPoolFlag(flag.phrase)
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-zinc-100 text-zinc-600'
                      }`}
                    >
                      {isPoolFlag(flag.phrase) ? 'Pool health' : 'JD wording'}
                    </span>
                    <p className="flex gap-2">
                      <IconAlert className="w-3.5 h-3.5 mt-px shrink-0 text-amber-600" />
                      <span className="text-zinc-800 font-medium">“{flag.phrase}”</span>
                    </p>
                    <p className="text-zinc-600 mt-1 pl-[22px]">{flag.why}</p>
                    <p className="text-zinc-600 mt-1 pl-[22px]">
                      <span className="text-emerald-700 font-medium">Rewrite: </span>
                      {flag.suggestion}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>

        {/* Column 2: top-3 explanations + ranked list */}
        <div className="space-y-4 min-w-0">
          {top3.length > 0 && (
            <section aria-label="Top 3 explanations">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {top3.map((c) => (
                  <article
                    key={c.rank}
                    onClick={() => setSelectedRank(c.rank)}
                    className="bg-white rounded-[10px] border border-zinc-200 p-4 cursor-pointer hover:border-blue-300 transition-colors"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className={`flex items-center justify-center w-5 h-5 rounded-[6px] font-mono text-[11px] font-semibold ${
                          c.rank === 1 ? 'bg-blue-600 text-white' : 'bg-zinc-100 text-zinc-600'
                        }`}
                      >
                        {c.rank}
                      </span>
                      <span className="text-[13px] font-semibold text-zinc-900 truncate">
                        {c.name}
                      </span>
                      <span className="font-mono text-[12px] font-semibold text-emerald-700 ml-auto">
                        {c.overall_score.toFixed(1)}
                      </span>
                    </div>
                    <p className="text-[12px] leading-relaxed text-zinc-600">{c.explanation}</p>
                  </article>
                ))}
              </div>
            </section>
          )}

          <main className="bg-white rounded-[10px] border border-zinc-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-200 flex items-center justify-between gap-3 flex-wrap">
              <h2 className="text-sm font-semibold">Ranked candidates</h2>
              <div
                className="flex items-center gap-1"
                role="group"
                aria-label="Filter candidates by band"
              >
                {(
                  [
                    ['all', `All ${analysis.ranking.length}`],
                    ['strong', `Strong ${bandCount('strong')}`],
                    ['medium', `Medium ${bandCount('medium')}`],
                    ['weak', `Weak ${bandCount('weak')}`],
                  ] as const
                ).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setBandFilter(key)}
                    aria-pressed={bandFilter === key}
                    className={`text-[11px] px-2 py-1 rounded-full transition-colors ${
                      bandFilter === key
                        ? 'bg-zinc-900 text-white'
                        : 'text-zinc-500 hover:text-zinc-800 hover:bg-zinc-100'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <motion.ul
              className="divide-y divide-zinc-100"
              variants={listVariants}
              initial="hidden"
              animate="visible"
              key={bandFilter}
            >
              {visible.map((c) => {
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
                          c.rank <= 3
                            ? 'text-blue-700 font-semibold'
                            : isSel
                              ? 'text-zinc-700'
                              : 'text-zinc-400'
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
                          {c.parse_warning && (
                            <span title={c.parse_warning} className="shrink-0">
                              <IconAlert className="w-3.5 h-3.5 text-amber-500" />
                            </span>
                          )}
                        </div>
                        <p className="font-mono text-[11px] text-zinc-500 truncate">
                          {c.file} · {c.matched_skills.length} matched ·{' '}
                          {c.missing_skills.length} missing
                        </p>
                      </div>
                      <div className="hidden sm:block w-36 space-y-1 shrink-0">
                        <ScoreBar label="KW" value={c.keyword_score} />
                        <ScoreBar label="SEM" value={c.semantic_score} />
                      </div>
                      <span
                        className={`text-[10px] font-medium px-1.5 py-0.5 rounded shrink-0 ${BAND_STYLE[c.band]}`}
                      >
                        {c.band}
                      </span>
                      <span
                        className={`font-mono text-sm font-semibold w-10 text-right shrink-0 ${
                          c.band === 'strong'
                            ? 'text-emerald-700'
                            : c.band === 'medium'
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
            {visible.length === 0 && (
              <p className="px-4 py-6 text-sm text-zinc-500 text-center">
                No candidates in this band.
              </p>
            )}
          </main>
        </div>

        {/* Column 3: candidate detail */}
        <aside>
          <CandidateDetail candidate={selected} topOverall={top.overall_score} />
        </aside>
      </div>

      {/* Deterministic recruiter Q&A over the stored analysis (§3e) */}
      <ChatPanel analysis={analysis} />
    </div>
  )
}
