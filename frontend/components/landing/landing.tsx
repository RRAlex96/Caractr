"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { warmBackend } from "@/lib/api"

export interface LandingStats {
  models: number
  engines: number
  listings: number | null
}

export interface FeaturedEngine {
  page: string
  engine: string
  problem: string
  years: string
  critical: boolean
}

const PROMISES = [
  {
    n: "01",
    title: "O preço é justo?",
    desc: "Comparamos com anúncios reais do mesmo modelo, com o preço de cada um ajustado ao ano e aos quilómetros deste carro.",
  },
  {
    n: "02",
    title: "Aquele motor tem problemas?",
    desc: "Se o motor ou a caixa daquele carro, naquele ano, tem uma avaria conhecida e cara, avisamos — com as fontes.",
  },
  {
    n: "03",
    title: "O que verificar e quanto oferecer",
    desc: "Os pontos a ver no test-drive, os documentos a pedir, uma margem para negociar e uma mensagem pronta para o vendedor.",
  },
]

const SOURCES = "Standvirtual · OLX · CustoJusto · qualquer stand"

function group(n: number) {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ")
}

export function Landing({ stats, engines }: { stats: LandingStats; engines: FeaturedEngine[] }) {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const [url, setUrl] = useState("")
  useEffect(() => {
    setMounted(true)
    warmBackend() // the API sleeps on the free tier: wake it while the visitor reads
  }, [])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const u = url.trim()
    router.push(u.startsWith("http") ? `/analisar?url=${encodeURIComponent(u)}` : "/analisar")
  }

  const fade = (d = "") => (mounted ? `animate-fadeUp${d}` : "opacity-0")

  return (
    <div className="relative">
      {/* ── HERO: paste the ad ─────────────────────────────── */}
      <section className="relative flex min-h-[100svh] flex-col overflow-hidden">
        <img
          src="/images/john-towner-3Kv48NS4WUU-unsplash.jpg"
          alt=""
          className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-[0.08] saturate-[0.4]"
        />
        <div className="pointer-events-none absolute -right-[10%] -top-[15%] h-[55vw] max-h-[700px] w-[55vw] max-w-[700px] rounded-full bg-[radial-gradient(circle,rgba(200,168,130,0.10)_0%,transparent_65%)]" />
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(rgba(250,250,249,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(250,250,249,0.02) 1px, transparent 1px)",
            backgroundSize: "80px 80px",
          }}
        />

        <div className="relative z-10 mx-auto flex w-full max-w-[880px] flex-1 flex-col items-center justify-center px-5 pb-16 pt-28 text-center">
          <p className={`font-mono text-[10px] uppercase tracking-[0.2em] text-foreground/35 ${fade()}`}>
            carros usados em Portugal
          </p>
          <h1
            className={`mt-5 font-display text-[clamp(34px,10.5vw,128px)] font-extrabold leading-[0.9] tracking-[-0.04em] ${fade()}`}
          >
            CARACTR
          </h1>
          <p
            className={`mt-7 max-w-[560px] text-[clamp(16px,1.6vw,20px)] font-light leading-relaxed text-foreground/70 ${fade("-d2")}`}
          >
            Cola o link do anúncio. Dizemos-te se o preço é justo, se aquele motor tem problemas conhecidos e o que
            verificar antes de comprar.
          </p>

          <form onSubmit={submit} className={`mt-9 flex w-full max-w-[600px] flex-col gap-2.5 sm:flex-row ${fade("-d3")}`}>
            <input
              type="url"
              inputMode="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.standvirtual.com/carros/anuncio/..."
              aria-label="Link do anúncio"
              className="min-w-0 flex-1 rounded-full border border-foreground/15 bg-foreground/[0.04] px-5 py-3.5 text-[14px] text-foreground placeholder:text-foreground/30 focus:border-gold/50 focus:outline-none"
            />
            <button
              type="submit"
              className="rounded-full bg-gold px-8 py-3.5 text-[14px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
            >
              Analisar
            </button>
          </form>
          <p className="mt-4 font-mono text-[10px] tracking-[0.5px] text-foreground/35">
            {SOURCES} · grátis durante o lançamento
          </p>
          <p className="mt-6 text-[13px] text-foreground/50">
            Sem anúncio à mão?{" "}
            <Link href="/exemplos" className="border-b border-gold/60 pb-px text-gold-dark hover:text-gold">
              Vê análises de exemplo
            </Link>
          </p>
        </div>
      </section>

      {/* ── WHAT YOU GET ───────────────────────────────────── */}
      <section className="relative px-5 py-24 lg:px-20">
        <div className="mx-auto w-full max-w-[1100px]">
          <p className="mb-5 text-[11px] uppercase tracking-[0.2em] text-muted-foreground">o que recebes</p>
          <h2 className="mb-12 font-display text-[clamp(28px,4vw,52px)] font-extrabold leading-[1.05] tracking-tight">
            Do lado de quem compra.
            <br />
            <span className="text-gold-dark">Não de quem vende.</span>
          </h2>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3 lg:gap-12">
            {PROMISES.map((p) => (
              <div key={p.n} className="border-t-2 border-border pt-6">
                <span className="font-display text-[clamp(32px,4vw,52px)] font-extrabold leading-none text-gold/55">
                  {p.n}
                </span>
                <h3 className="mb-3 mt-5 font-display text-[clamp(20px,2vw,26px)] font-extrabold tracking-tight">
                  {p.title}
                </h3>
                <p className="text-[15px] leading-relaxed text-foreground/60">{p.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-16 grid grid-cols-1 gap-6 border-t border-foreground/[0.08] pt-10 sm:grid-cols-3">
            {[
              stats.listings ? { v: group(stats.listings), l: "anúncios lidos este mês", s: "para calcular o preço de mercado" } : null,
              { v: group(stats.models), l: "modelos no catálogo", s: "com motores, anos e preços" },
              { v: String(stats.engines), l: "avarias de motor e caixa", s: "verificadas fonte a fonte" },
            ]
              .filter(Boolean)
              .map((m) => (
                <div key={m!.l}>
                  <p className="font-mono text-[clamp(22px,2.4vw,30px)] font-bold leading-none tracking-tight text-gold">
                    {m!.v}
                  </p>
                  <p className="mt-2 text-[13px] text-foreground/60">{m!.l}</p>
                  <p className="mt-0.5 font-mono text-[10px] text-foreground/30">{m!.s}</p>
                </div>
              ))}
          </div>
        </div>
      </section>

      {/* ── KNOWN ENGINE FAULTS ────────────────────────────── */}
      {engines.length > 0 && (
        <section className="relative bg-[#050507] px-5 py-24 lg:px-20">
          <div className="mx-auto w-full max-w-[1100px]">
            <p className="mb-5 text-[11px] uppercase tracking-[0.2em] text-muted-foreground">motores a conhecer</p>
            <h2 className="mb-4 font-display text-[clamp(28px,4vw,48px)] font-extrabold leading-[1.05] tracking-tight">
              Alguns motores têm avarias caras e conhecidas.
            </h2>
            <p className="mb-10 max-w-[620px] text-[15px] leading-relaxed text-foreground/55">
              Em cada análise verificamos se o carro tem um destes motores, no ano em que o problema existe. Cada
              página explica o que verificar, quanto custa e as garantias que ainda cobrem a reparação.
            </p>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {engines.map((e) => (
                <Link
                  key={e.page}
                  href={`/motores/${e.page}`}
                  className="group rounded-lg border border-border bg-surface px-5 py-4 transition-colors hover:border-gold/40"
                >
                  <p
                    className={`font-mono text-[9px] uppercase tracking-[1.5px] ${e.critical ? "text-danger" : "text-warning"}`}
                  >
                    {e.critical ? "problema grave" : "ponto a verificar"} · {e.years}
                  </p>
                  <p className="mt-1.5 text-[15px] font-semibold text-foreground group-hover:text-gold">{e.engine}</p>
                  <p className="mt-0.5 text-[13px] text-foreground/55">{e.problem}</p>
                </Link>
              ))}
            </div>
            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-[13px]">
              <Link href="/carros" className="border-b border-gold/60 pb-px text-gold-dark hover:text-gold">
                Guia de carros usados: preços e motores por modelo
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* ── NOT SURE WHAT TO BUY ───────────────────────────── */}
      <section className="relative grid grid-cols-1 overflow-hidden md:min-h-[70vh] md:grid-cols-2">
        <div className="relative z-10 flex flex-col justify-center px-5 py-20 md:py-0 lg:px-20">
          <p className="mb-5 text-[11px] uppercase tracking-[0.2em] text-muted-foreground">ainda não escolheste?</p>
          <h2 className="font-display text-[clamp(28px,4.5vw,60px)] font-extrabold leading-[0.95] tracking-tight">
            Diz-nos como vives.
            <br />
            <span className="text-gold-dark">Sugerimos o carro.</span>
          </h2>
          <p className="mt-6 max-w-[360px] text-[15px] font-light leading-relaxed text-muted-foreground">
            Cinco perguntas sobre o teu dia a dia, sem especificações técnicas. Recebes cinco modelos com os prós, os
            contras e o preço de mercado.
          </p>
          <div className="mt-7">
            <Link
              href="/escolher"
              className="inline-block rounded-full border border-foreground/20 px-7 py-3.5 text-[13px] font-medium text-foreground/80 transition-colors hover:border-gold/40 hover:text-gold"
            >
              descobrir o meu carro
            </Link>
          </div>
        </div>
        <div className="relative hidden md:block">
          <img
            src="/images/taneli-lahtinen-Mie9wsHfXHc-unsplash.jpg"
            alt=""
            loading="lazy"
            className="absolute inset-0 h-full w-full object-cover saturate-[0.9]"
          />
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-background to-transparent to-[14%]" />
        </div>
      </section>

      {/* ── FINAL CTA ──────────────────────────────────────── */}
      <section className="relative flex min-h-[70vh] flex-col items-center justify-center overflow-hidden">
        <img
          src="/images/jesse-bowser-c0I4ahyGIkA-unsplash.jpg"
          alt=""
          loading="lazy"
          className="absolute inset-0 h-full w-full object-cover saturate-[0.7]"
        />
        <div className="absolute inset-0 bg-[rgba(13,12,10,0.7)]" />
        <div className="relative z-10 px-5 text-center">
          <p className="mb-5 text-[11px] uppercase tracking-[0.25em] text-foreground/40">antes de ligares ao vendedor</p>
          <h2 className="font-display text-[clamp(40px,9vw,112px)] font-extrabold leading-[0.88] tracking-[-0.04em] text-foreground">
            TENS UM
            <br />
            ANÚNCIO?
          </h2>
          <div className="mt-10">
            <Link
              href="/analisar"
              className="rounded-full bg-gold px-10 py-4 text-[14px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
            >
              analisar um anúncio
            </Link>
          </div>
        </div>
        <div className="pointer-events-none absolute bottom-6 left-5 right-5 flex justify-center lg:bottom-8">
          <span className="font-mono text-[9px] uppercase tracking-[2px] text-foreground/20">informar, nunca assustar</span>
        </div>
      </section>
    </div>
  )
}
