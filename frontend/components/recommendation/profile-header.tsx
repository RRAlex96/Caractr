"use client"

import { useState } from "react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import type { UserProfile, ProfileNarrative } from "@/lib/types"

const PROFILE_LABELS: Record<string, string> = {
  economy: "Economia",
  comfort: "Conforto",
  driving: "Condução",
  practical: "Praticidade",
  status: "Imagem",
  reliability: "Fiabilidade",
}

interface ProfileHeaderProps {
  profile: UserProfile
  narrative?: ProfileNarrative | null
  profileSummary?: string | null
  className?: string
}

export function ProfileHeader({
  profile,
  narrative,
  profileSummary,
  className,
}: ProfileHeaderProps) {
  const [open, setOpen] = useState(false)
  const summaryText = narrative?.summary || profileSummary
  const lines = narrative
    ? [narrative.priorities, narrative.tension, narrative.aversion, narrative.identity, narrative.context].filter(Boolean) as string[]
    : []

  return (
    <section className={cn("bg-background px-[clamp(24px,5vw,80px)] pb-[clamp(48px,6vw,80px)] pt-24 md:pt-28", className)}>
      {/* Title */}
      <div className="mb-5 h-0.5 w-12 rounded-full bg-gold" />
      <h1 className="mb-6 font-display text-[clamp(36px,6vw,80px)] font-extrabold leading-[0.9] tracking-tight">
        A TUA SHORTLIST
      </h1>

      {/* Profile narrative */}
      {summaryText && (
        <div className="mb-3">
          {/* Summary pill */}
          <div className="mb-5 inline-flex items-center gap-4 rounded-full border border-gold/20 bg-gold/[0.06] px-4.5 py-2">
            <p className="text-[13px] font-light text-foreground/60">
              {summaryText}
            </p>
            <Link
              href="/escolher"
              className="whitespace-nowrap font-mono text-[9px] uppercase tracking-[1px] text-gold/70 hover:text-gold"
            >
              Alterar
            </Link>
          </div>

        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="text-[13px] text-muted-foreground underline-offset-4 hover:text-gold hover:underline"
      >
        {open ? "Esconder" : "Porque escolhemos estes"}
      </button>

      {open && (
        <div className="mt-5 max-w-[640px]">
          {lines.length > 0 && (
            <div className="mb-6 flex flex-col gap-3">
              {lines.map((line, i) => (
                <div key={i} className="flex items-start gap-3.5">
                  <div className="mt-[9px] h-[3px] w-[3px] shrink-0 rounded-full bg-gold" />
                  <p className="text-[14px] font-light leading-relaxed text-foreground/60">{line}</p>
                </div>
              ))}
            </div>
          )}
      <div className="grid grid-cols-[repeat(auto-fit,minmax(120px,1fr))] gap-5">
        {Object.entries(profile).map(([key, val]) => (
          <div key={key}>
            <div className="mb-2 flex items-baseline justify-between">
              <span className="text-[10px] uppercase tracking-[1px] text-foreground/30">
                {PROFILE_LABELS[key] || key}
              </span>
              <span className="font-mono text-xs text-gold">
                {Math.round(val * 100)}
              </span>
            </div>
            <div className="h-0.5 rounded-full bg-foreground/[0.08]">
              <div
                className="h-full rounded-full bg-gold transition-[width] duration-1000 ease-out"
                style={{ width: `${Math.round(val * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
        </div>
      )}
    </section>
  )
}
