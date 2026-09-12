import { motion, useReducedMotion } from 'motion/react'
import type { Candidate } from '../lib/types'
import { SkillChipGroup } from './SkillChips'
import { NumberTicker } from './NumberTicker'

interface Props {
  candidate: Candidate
  topOverall: number
}

function BigBar({
  label,
  value,
  accent,
  reduced,
}: {
  label: string
  value: number
  accent: string
  reduced: boolean | null
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-[11px] font-medium text-zinc-500">{label}</span>
        <span className="font-mono text-sm font-semibold text-zinc-900">
          <NumberTicker value={value} decimalPlaces={1} />
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-zinc-100 overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${accent}`}
          initial={reduced ? false : { width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
    </div>
  )
}

export default function CandidateDetail({ candidate: c, topOverall }: Props) {
  const reduced = useReducedMotion()
  return (
    <div className="bg-white rounded-[10px] border border-zinc-200 p-4 lg:sticky lg:top-4">
      {/* Header */}
      <div className="flex items-start gap-3">
        <span
          className={`flex items-center justify-center w-8 h-8 rounded-[8px] font-mono text-sm font-semibold shrink-0 ${
            c.rank === 1
              ? 'bg-blue-600 text-white'
              : 'bg-zinc-100 text-zinc-600'
          }`}
        >
          {c.rank}
        </span>
        <div className="min-w-0">
          <h2 className="text-xl font-semibold tracking-tight truncate">{c.name}</h2>
          <p className="font-mono text-[11px] text-zinc-500 truncate">{c.file}</p>
        </div>
      </div>

      {c.rank === 1 && (
        <div className="mt-3 rounded-md bg-blue-50 border border-blue-100 px-3 py-2 text-xs text-blue-800">
          Best match in this pool — {c.overall_score.toFixed(1)} overall.
        </div>
      )}

      {/* Scores */}
      <div className="mt-4 space-y-3">
        <BigBar
          label="Overall"
          value={c.overall_score}
          accent={c.overall_score >= topOverall - 0.05 ? 'bg-blue-600' : 'bg-zinc-400'}
          reduced={reduced}
        />
        <div className="grid grid-cols-2 gap-3">
          <BigBar label="Keyword" value={c.keyword_score} accent="bg-emerald-500" reduced={reduced} />
          <BigBar label="Semantic" value={c.semantic_score} accent="bg-violet-500" reduced={reduced} />
        </div>
      </div>

      {/* Explanation (top 3 only) */}
      {c.explanation && (
        <div className="mt-4">
          <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500 mb-1.5">
            Why this rank
          </h3>
          <p className="text-[13px] leading-relaxed text-zinc-700">{c.explanation}</p>
        </div>
      )}

      {/* Skills */}
      <div className="mt-4 space-y-3">
        {(
          [
            ['Matched', c.matched_skills, 'matched'],
            ['Partial', c.partial_skills, 'partial'],
            ['Missing', c.missing_skills, 'missing'],
          ] as const
        ).map(([label, skills, variant]) =>
          skills.length > 0 ? (
            <div key={label}>
              <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500 mb-1.5">
                {label} · {skills.length}
              </h3>
              <SkillChipGroup skills={skills} variant={variant} max={10} />
            </div>
          ) : null,
        )}
      </div>

      {/* Evidence */}
      {c.evidence.sections.length > 0 && (
        <div className="mt-4 pt-4 border-t border-zinc-100">
          <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500 mb-2">
            Section similarity
          </h3>
          <ul className="space-y-1.5">
            {c.evidence.sections.map((s) => (
              <li key={s.name} className="flex items-center gap-2">
                <span className="text-[11px] text-zinc-600 w-[76px] shrink-0 truncate">
                  {s.name}
                </span>
                <div className="h-1 flex-1 rounded-full bg-zinc-100 overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full ${
                      s.similarity >= 0.6
                        ? 'bg-violet-500'
                        : s.similarity >= 0.35
                          ? 'bg-amber-400'
                          : 'bg-zinc-300'
                    }`}
                    initial={reduced ? false : { width: 0 }}
                    animate={{ width: `${s.similarity * 100}%` }}
                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
                <span className="font-mono text-[10px] text-zinc-500 w-7 text-right">
                  {(s.similarity * 100).toFixed(0)}%
                </span>
              </li>
            ))}
          </ul>
          {c.evidence.highlight && (
            <figure className="mt-3 bg-zinc-50 border border-zinc-100 rounded-md px-3 py-2.5">
              <blockquote className="text-xs leading-relaxed text-zinc-600">
                “{c.evidence.highlight}”
              </blockquote>
              <figcaption className="mt-1.5 text-[10px] text-zinc-500">
                Strongest match, from the resume
              </figcaption>
            </figure>
          )}
        </div>
      )}
    </div>
  )
}
