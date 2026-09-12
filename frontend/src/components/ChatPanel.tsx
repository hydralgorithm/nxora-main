import { useRef, useState, useEffect } from 'react'
import type { Analysis } from '../lib/types'
import { chat } from '../lib/api'
import { IconChat, IconClose, IconSend } from './Icon'

interface Props {
  analysis: Analysis
}

interface Msg {
  role: 'user' | 'assistant'
  text: string
}

// The backend's empty-state answer renders as a hint, not an error (§2).
const EMPTY_HINT = 'Upload a JD and resumes first, then ask me about the candidates.'

export default function ChatPanel({ analysis }: Props) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState<string | null>(null) // last question that failed
  const listRef = useRef<HTMLDivElement>(null)

  const top = analysis.ranking[0]
  const suggestions = [
    'Why is candidate 1 above candidate 2?',
    'What is candidate 3 missing?',
    top ? `Tell me about ${top.name.split(' ')[0]}` : 'Top candidates',
  ]

  useEffect(() => {
    // Keep the newest message in view.
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, busy])

  async function ask(question: string) {
    const q = question.trim()
    if (!q || busy) return
    setInput('')
    setFailed(null)
    setMessages((m) => [...m, { role: 'user', text: q }])
    setBusy(true)
    try {
      const answer = await chat(q, analysis)
      setMessages((m) => [...m, { role: 'assistant', text: answer }])
    } catch {
      // Network failure only — /api/chat never returns an error status.
      setFailed(q)
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-40 flex items-center gap-2 px-4 py-2.5 rounded-[10px] bg-blue-600 text-white text-sm font-medium shadow-[0_8px_24px_rgba(24,24,27,0.18)] hover:bg-blue-700 active:translate-y-[1px] transition-colors"
      >
        <IconChat className="w-4 h-4" />
        Ask about candidates
      </button>
    )
  }

  return (
    <div className="fixed bottom-5 right-5 z-40 w-[calc(100vw-2.5rem)] sm:w-[380px] bg-white rounded-[10px] border border-zinc-200 shadow-[0_16px_48px_rgba(24,24,27,0.18)] overflow-hidden flex flex-col max-h-[min(520px,calc(100dvh-6rem))]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-zinc-200 flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-sm font-semibold">Ask about candidates</h2>
          <p className="text-[11px] text-zinc-500">Deterministic — the engine explains itself</p>
        </div>
        <button
          onClick={() => setOpen(false)}
          className="text-zinc-400 hover:text-zinc-700 transition-colors"
          aria-label="Close chat"
        >
          <IconClose className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div ref={listRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-2.5">
        {messages.length === 0 && (
          <div>
            <p className="text-xs text-zinc-500 leading-relaxed">
              Ask me why one candidate ranks above another, or what someone is missing.
              Every answer comes from the engine&rsquo;s own numbers — no LLM involved.
            </p>
            <div className="flex flex-wrap gap-1.5 mt-3">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => ask(s)}
                  className="text-[11px] text-zinc-600 bg-zinc-100 hover:bg-zinc-200 border border-zinc-200 rounded-full px-2.5 py-1 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
            <p
              className={`max-w-[85%] rounded-[10px] px-3 py-2 text-[13px] leading-relaxed ${
                m.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : m.text === EMPTY_HINT
                    ? 'bg-zinc-50 border border-zinc-100 text-zinc-500' // hint styling
                    : 'bg-zinc-50 border border-zinc-100 text-zinc-700'
              }`}
            >
              {m.text}
            </p>
          </div>
        ))}
        {busy && (
          <div className="flex justify-start" aria-live="polite">
            <div className="flex gap-1 items-center bg-zinc-50 border border-zinc-100 rounded-[10px] px-3 py-2.5">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-pulse"
                  style={{ animationDelay: `${i * 160}ms` }}
                />
              ))}
            </div>
          </div>
        )}
        {failed && (
          <div className="flex flex-col items-start gap-1.5">
            <p className="text-[12px] text-rose-700 bg-rose-50 border border-rose-100 rounded-[10px] px-3 py-2">
              Couldn&rsquo;t reach the engine. Check the backend and try again.
            </p>
            <button
              onClick={() => ask(failed)}
              className="text-[11px] font-medium text-blue-700 hover:text-blue-900 transition-colors"
            >
              Try again
            </button>
          </div>
        )}
      </div>

      {/* Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          ask(input)
        }}
        className="p-3 border-t border-zinc-200 flex items-center gap-2 shrink-0"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. why is candidate 1 above candidate 2?"
          className="flex-1 min-w-0 rounded-[8px] border border-zinc-200 px-3 py-2 text-[13px] placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className={`p-2 rounded-[8px] transition-colors shrink-0 ${
            busy || !input.trim()
              ? 'bg-zinc-100 text-zinc-400 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
          aria-label="Send question"
        >
          <IconSend className="w-4 h-4" />
        </button>
      </form>
    </div>
  )
}
