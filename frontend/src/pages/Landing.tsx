import { IconArrowRight } from '../components/Icon'
import { BlurFade } from '../components/BlurFade'
import { DotPattern } from '../components/DotPattern'
import { NumberTicker } from '../components/NumberTicker'
import { TiltedCard } from '../components/TiltedCard'

export default function Landing({ onStart }: { onStart: () => void }) {
  const steps = [
    {
      title: 'Drop in the job description',
      body: 'Upload a JD or paste the text. We extract the skills that actually matter — and flag biased or bloated requirements before they skew your shortlist.',
    },
    {
      title: 'Upload the resume pile',
      body: 'Fifteen resumes or fifty. Messy formatting, unusual section names, non-standard layouts — the parser handles them all.',
    },
    {
      title: 'Get a ranked shortlist, with receipts',
      body: 'Every candidate scored on two independent tracks — exact keyword matches and semantic similarity — blended into one number you can defend.',
    },
  ]

  return (
    <div className="relative min-h-[100dvh] bg-zinc-100 overflow-hidden">
      {/* Dot grid across the whole page; fades out near the footer */}
      <DotPattern
        width={22}
        height={22}
        cr={1}
        className="fill-zinc-400/40 [mask-image:linear-gradient(to_bottom,white_0%,white_60%,transparent_92%)]"
      />

      {/* Nav */}
      <header className="relative px-6 lg:px-10 h-16 flex items-center justify-between max-w-[1200px] mx-auto">
        <span className="font-semibold tracking-tight text-[15px]">Shortlist</span>
        <button
          onClick={onStart}
          className="group text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors inline-flex items-center gap-1.5"
        >
          Run an analysis
          <IconArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
        </button>
      </header>

      {/* Hero — left-aligned split */}
      <main className="relative max-w-[1200px] mx-auto px-6 lg:px-10">
        <section className="relative grid lg:grid-cols-[1.2fr_1fr] gap-10 lg:gap-16 items-center pt-14 lg:pt-24 pb-16">
          <div className="relative">
            <BlurFade>
              <h1 className="text-4xl md:text-[52px] font-semibold tracking-[-0.04em] leading-[1.05] text-zinc-900">
                Rank every resume.
                <br />
                Show the receipts.
              </h1>
            </BlurFade>
            <BlurFade delay={0.1}>
              <p className="mt-5 text-base text-zinc-600 leading-relaxed max-w-[52ch]">
                Shortlist scores candidates against a job description on two independent tracks —
                exact keyword matches and semantic similarity — and shows you the evidence behind
                every score. No black box, no vibes, no LLM quietly deciding who gets an interview.
              </p>
            </BlurFade>
            <BlurFade delay={0.2}>
              <div className="mt-8 flex items-center gap-4">
                <button
                  onClick={onStart}
                  className="text-sm font-medium px-5 py-3 rounded-[10px] bg-blue-600 text-white hover:bg-blue-700 active:translate-y-[1px] transition-colors"
                >
                  Run an analysis
                </button>
                <span className="text-xs text-zinc-500">
                  18-sample dataset included — results in seconds
                </span>
              </div>
            </BlurFade>
          </div>

          {/* Mini preview: a slice of the ranked list, styled like the real thing */}
          <BlurFade delay={0.15} className="hidden lg:block">
            <TiltedCard>
            <div className="bg-white rounded-[10px] border border-zinc-200 overflow-hidden shadow-[0_1px_2px_rgba(24,24,27,0.05),0_16px_40px_rgba(24,24,27,0.09)] transition-shadow duration-500 hover:shadow-[0_1px_2px_rgba(24,24,27,0.06),0_28px_64px_rgba(24,24,27,0.14)]">
              <div className="px-4 py-2.5 border-b border-zinc-200 flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-700">Junior Full Stack Dev</span>
                <span className="font-mono text-[10px] text-zinc-500">hybrid · v1</span>
              </div>
              <ul className="divide-y divide-zinc-100">
                {(
                  [
                    ['1', 'Ananya S.', 87.4, 'react, node, mongodb'],
                    ['2', 'Rohan M.', 82.1, 'react, node, express'],
                    ['3', 'Priya N.', 78.9, 'react, mongodb'],
                  ] as [string, string, number, string][]
                ).map(([rank, name, score, tags]) => (
                  <li key={rank} className="px-4 py-3 flex items-center gap-3">
                    <span className="font-mono text-[11px] text-zinc-500 w-4">{rank}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-medium text-zinc-900">{name}</p>
                      <p className="font-mono text-[10px] text-zinc-500 truncate">{tags}</p>
                    </div>
                    <span className="font-mono text-[13px] font-semibold text-emerald-700">
                      <NumberTicker value={score} decimalPlaces={1} duration={1.2} />
                    </span>
                  </li>
                ))}
              </ul>
              <div className="px-4 py-2.5 border-t border-zinc-100 bg-zinc-50/60">
                <p className="font-mono text-[10px] text-zinc-500">
                  keyword 84.2 · semantic 90.6 — blended 50/50
                </p>
              </div>
            </div>
            </TiltedCard>
          </BlurFade>
        </section>

        {/* How it works — the copy carries the order; rules mark the columns */}
        <section className="border-t border-zinc-200 py-14">
          <h2 className="text-base font-semibold text-zinc-900 mb-8">How it works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((s, i) => (
              <BlurFade key={s.title} delay={0.1 + i * 0.08}>
                <div className="border-t-2 border-zinc-800 pt-4">
                  <h3 className="text-sm font-semibold text-zinc-900">{s.title}</h3>
                  <p className="mt-1.5 text-[13px] text-zinc-600 leading-relaxed max-w-[38ch]">
                    {s.body}
                  </p>
                </div>
              </BlurFade>
            ))}
          </div>
        </section>

        {/* Footer strip */}
        <footer className="border-t border-zinc-200 py-8 flex items-center justify-between gap-6">
          <p className="text-xs text-zinc-500">
            Scoring runs locally — keyword and semantic tracks, blended 50/50. No LLM in the
            ranking path.
          </p>
          <span className="font-mono text-[10px] text-zinc-500 shrink-0">
            Nexora · InternLoom 2026
          </span>
        </footer>
      </main>
    </div>
  )
}
