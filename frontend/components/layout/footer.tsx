import Link from "next/link"

export function Footer() {
  return (
    <footer className="border-t border-border/50 bg-background">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-8">
        <span className="font-display text-[11px] font-bold tracking-[0.12em] text-muted-foreground/40">
          CARACTR
        </span>
        <span className="font-mono text-[9px] tracking-[2px] uppercase text-muted-foreground/30">
          informar nunca assustar
        </span>
        <div className="flex items-center gap-4">
          <Link
            href="/privacidade"
            className="text-[11px] text-muted-foreground/40 transition-colors hover:text-muted-foreground"
          >
            Privacidade
          </Link>
          <span className="text-[11px] text-muted-foreground/40">2026</span>
        </div>
      </div>
    </footer>
  )
}
