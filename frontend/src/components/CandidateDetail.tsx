import { motion, useReducedMotion } from 'motion/react'
import type { Candidate } from '../lib/types'
import { SkillChipGroup } from './SkillChips'
import { NumberTicker } from './NumberTicker'
import { IconAlert } from './Icon'

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
            c.rank === 1 ? 'bg-blue-600 text-white' : 'bg-zinc-100 text-zinc-600'
          }`}
        >
          {c.rank}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-semibold tracking-tight truncate">{c.name}</h2>
            <span
              className={`text-[10px] font-medium px-1.5 py-0.5 rounded shrink-0 ${
                c.band === 'strong'
                  ? 'bg-emerald-100 text-emerald-700'
                  : c.band === 'medium'
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-zinc-100 text-zinc-500'
              }`}
            >
              {c.band}
            </span>
          </div>
          <p className="font-mono text-[11px] text-zinc-500 truncate">{c.file}</p>
        </div>
      </div>

      {c.parse_warning && (
        <div className="mt-3 flex gap-2 rounded-md bg-amber-50 border border-amber-100 px-3 py-2 text-xs text-amber-800">
          <IconAlert className="w-3.5 h-3.5 mt-px shrink-0" />
          <p>{c.parse_warning}</p>
        </div>
      )}

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

      {/* Requirement evidence — the centerpiece: every JD requirement mapped to
          this candidate's best matching resume line (FRONTEND_SPEC §3c). */}
      {c.requirement_evidence.length > 0 && (
        <div className="mt-4 pt-4 border-t border-zinc-100">
          <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500 mb-2.5">
            Requirement-by-requirement
          </h3>
          <ul className="space-y-3">
            {c.requirement_evidence.map((r) => (
              <li key={r.requirement}>
                <div className="flex items-center gap-2">
                  <p className="text-[12px] text-zinc-800 font-medium flex-1">{r.requirement}</p>
                  <span className="font-mono text-[10px] text-zinc-500 shrink-0">
                    {(r.similarity * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="h-1 rounded-full bg-zinc-100 overflow-hidden mt-1">
                  <motion.div
                    className={`h-full rounded-full ${
                      r.similarity >= 0.6
                        ? 'bg-violet-500'
                        : r.similarity >= 0.4
                          ? 'bg-amber-400'
                          : 'bg-zinc-300'
                    }`}
                    initial={reduced ? false : { width: 0 }}
                    animate={{ width: `${r.similarity * 100}%` }}
                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
                <blockquote className="mt-1.5 text-[11px] leading-relaxed text-zinc-500">
                  “{r.line}” <span className="text-zinc-400">— {r.section}</span>
                </blockquote>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Skills — matched skills carry their evidence line from the resume */}
      <div className="mt-4 space-y-3">
        {c.matched_skills.length > 0 && (
          <div>
            <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500 mb-1.5">
              Matched · {c.matched_skills.length}
            </h3>
            <ul className="space-y-2">
              {c.matched_skills.map((s) => (
                <li key={s}>
                  <p className="text-[12px] font-medium text-emerald-700">{s}</p>
                  {c.skill_evidence[s] && (
                    <blockquote className="text-[11px] leading-relaxed text-zinc-500 mt-0.5">
                      “{c.skill_evidence[s]}”
                    </blockquote>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        {c.partial_skills.length > 0 && (
          <div>
            <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500 mb-1.5">
              Partial · {c.partial_skills.length}
            </h3>
            <SkillChipGroup skills={c.partial_skills} variant="partial" max={10} />
          </div>
        )}
        {c.missing_skills.length > 0 && (
          <div>
            <h3 className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500 mb-1.5">
              Missing · {c.missing_skills.length}
            </h3>
            <SkillChipGroup skills={c.missing_skills} variant="missing" max={10} />
          </div>
        )}
      </div>

      {/* Section similarity + highlight */}
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
