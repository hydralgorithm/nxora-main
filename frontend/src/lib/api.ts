import type { Analysis } from './types'
import mockAnalysis from '../mocks/analyze.json'

// Backend runs on a separate machine/branch during dev; mock mode is the
// default so the UI is fully demoable offline. Flip with VITE_API_MODE=live
// (VITE_API_BASE defaults to the spec's hardcoded demo URL).
const MODE = import.meta.env.VITE_API_MODE ?? 'mock'
const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export const isMock = MODE === 'mock'

/** Abortable fetch with the spec's 60s budget (first call after server start can take ~20s+). */
async function fetchWithTimeout(url: string, init: RequestInit, ms = 60_000): Promise<Response> {
  const ctl = new AbortController()
  const timer = setTimeout(() => ctl.abort(), ms)
  try {
    return await fetch(url, { ...init, signal: ctl.signal })
  } finally {
    clearTimeout(timer)
  }
}

async function errorDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string }
    if (body.detail) return body.detail
  } catch {
    /* non-JSON body */
  }
  return `Request failed (${res.status}).`
}

export async function analyze(
  jdFile: File | null,
  jdText: string | null,
  resumes: File[],
): Promise<Analysis> {
  if (isMock) {
    // Simulate a realistic warm-request duration so the loading state shows.
    await new Promise((r) => setTimeout(r, 2200))
    return mockAnalysis as unknown as Analysis
  }
  const form = new FormData()
  if (jdFile) form.append('jd_file', jdFile)
  if (jdText) form.append('jd_text', jdText)
  resumes.forEach((f) => form.append('resumes', f))
  // No manual Content-Type: the browser must set the multipart boundary.
  const res = await fetchWithTimeout(`${BASE}/api/analyze`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await errorDetail(res))
  return res.json()
}

export async function health(): Promise<boolean> {
  if (isMock) return true
  try {
    const res = await fetchWithTimeout(`${BASE}/health`, { method: 'GET' }, 4000)
    return res.ok
  } catch {
    return false
  }
}

export async function chat(question: string, analysis: Analysis): Promise<string> {
  if (isMock) return mockChat(question, analysis)
  const res = await fetchWithTimeout(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, analysis }),
  }, 15_000)
  if (!res.ok) throw new Error(await errorDetail(res))
  return ((await res.json()) as { answer: string }).answer
}

// ---------------------------------------------------------------------------
// Mock chat — mirrors the documented /api/chat behaviors (FRONTEND_SPEC §2):
// rank-number + name resolution, delta explanations from the engine's own
// numbers, single-candidate profiles, top-3 podium summary, empty-state hint.
// Deterministic, no LLM — same rule as the real backend.
// ---------------------------------------------------------------------------
function resolveMentions(question: string, analysis: Analysis) {
  const q = question.toLowerCase()
  const ranks: number[] = []
  for (const m of q.matchAll(/(?:candidate|rank(?:ed)?|number|#)\s*(\d+)|#(\d+)/g)) {
    const n = Number(m[1] ?? m[2])
    if (n >= 1 && n <= analysis.ranking.length && !ranks.includes(n)) ranks.push(n)
    if (ranks.length === 2) break
  }
  const byName: number[] = []
  for (const c of analysis.ranking) {
    const words = c.name.toLowerCase().split(/\s+/).filter((w) => w.length > 2)
    if (words.some((w) => q.includes(w))) {
      if (!ranks.includes(c.rank) && !byName.includes(c.rank)) byName.push(c.rank)
      if (ranks.length + byName.length === 2) break
    }
  }
  const ids = [...ranks, ...byName].slice(0, 2)
  return ids.map((r) => analysis.ranking.find((c) => c.rank === r)!).filter(Boolean)
}

function profile(c: Analysis['ranking'][number]): string {
  const matched = c.matched_skills.length ? c.matched_skills.join(', ') : 'none'
  const missing = c.missing_skills.length ? c.missing_skills.join(', ') : 'none'
  return `${c.name} ranks #${c.rank} with an overall fit of ${c.overall_score.toFixed(1)}/100 ` +
    `(keyword ${c.keyword_score.toFixed(1)}, semantic ${c.semantic_score.toFixed(1)} — band: ${c.band}). ` +
    `Matched: ${matched}. Missing: ${missing}. ` +
    `Key evidence: "${c.evidence.highlight}"`
}

function mockChat(question: string, analysis: Analysis): string {
  const trimmed = question.trim()
  if (!trimmed || analysis.ranking.length === 0) {
    return 'Upload a JD and resumes first, then ask me about the candidates.'
  }
  const found = resolveMentions(trimmed, analysis)
  if (found.length >= 2) {
    const [a, b] = found
    const d = a.overall_score - b.overall_score
    const kwD = a.keyword_score - b.keyword_score
    const semD = a.semantic_score - b.semantic_score
    const aOnly = a.matched_skills.filter((s) => !b.matched_skills.includes(s))
    const bOnly = b.matched_skills.filter((s) => !a.matched_skills.includes(s))
    return `${a.name} (#${a.rank}) is ${d.toFixed(1)} points ahead of ${b.name} (#${b.rank}). ` +
      `Keyword track: ${a.keyword_score.toFixed(1)} vs ${b.keyword_score.toFixed(1)} (${kwD >= 0 ? '+' : ''}${kwD.toFixed(1)}); ` +
      `semantic track: ${a.semantic_score.toFixed(1)} vs ${b.semantic_score.toFixed(1)} (${semD >= 0 ? '+' : ''}${semD.toFixed(1)}). ` +
      (aOnly.length ? `${a.name} demonstrates: ${aOnly.join(', ')}. ` : '') +
      (bOnly.length ? `${b.name} demonstrates: ${bOnly.join(', ')}. ` : '') +
      `Strongest evidence for #${a.rank}: "${a.evidence.highlight}"`
  }
  if (found.length === 1) return profile(found[0])
  const top3 = analysis.ranking.slice(0, 3)
  return `Top of the shortlist: ${top3.map((c) => `#${c.rank} ${c.name} (${c.overall_score.toFixed(1)})`).join(', ')}. ` +
    `Ask me "why is candidate 1 above candidate 2?" or name any candidate to see their breakdown.`
}
