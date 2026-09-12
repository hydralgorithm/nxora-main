type Variant = 'matched' | 'partial' | 'missing'

const styles: Record<Variant, string> = {
  matched: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  partial: 'bg-amber-50 text-amber-800 border-amber-200',
  missing: 'bg-rose-50 text-rose-800 border-rose-200',
}

export function SkillChip({ skill, variant }: { skill: string; variant: Variant }) {
  return (
    <span
      className={`text-[11px] px-2 py-0.5 rounded-md border ${styles[variant]}`}
    >
      {skill}
    </span>
  )
}

export function SkillChipGroup({
  skills,
  variant,
  max,
}: {
  skills: string[]
  variant: Variant
  max?: number
}) {
  const shown = max ? skills.slice(0, max) : skills
  const rest = skills.length - shown.length
  return (
    <span className="flex flex-wrap gap-1">
      {shown.map((s) => (
        <SkillChip key={s} skill={s} variant={variant} />
      ))}
      {rest > 0 && (
        <span className="text-[11px] px-1.5 py-0.5 text-zinc-500">+{rest}</span>
      )}
    </span>
  )
}
