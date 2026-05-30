"use client"

import Link from "next/link"
import { useEffect, useState } from "react"

const STATS = [
  { value: "354", label: "perfis detalhados", sub: "conducao, fiabilidade e versao" },
  { value: "200+", label: "modelos analisados", sub: "desde 2010, em expansao" },
  { value: "tempo real", label: "dados de mercado", sub: "precos de anuncios reais" },
]

const STEPS = [
  {
    n: "01",
    title: "Conta-nos",
    desc: "Sobre a tua vida. O que fazes, onde vais, quem levas. Sem cilindradas, sem especificacoes tecnicas.",
  },
  {
    n: "02",
    title: "Descobre",
    desc: "5 modelos selecionados para o teu perfil. Com argumentos reais, tradeoffs honestos e linguagem humana.",
  },
  {
    n: "03",
    title: "Analisa",
    desc: "Encontraste um anuncio? Cruzamos o preco com o mercado, verificamos quilometros e avaliamos o vendedor.",
    link: { href: "/analisar", label: "analisar anuncio" },
  },
  {
    n: "04",
    title: "Concierge",
    desc: "Preferes que facamos tudo? Pesquisamos, analisamos e entregamos uma selecao curada.",
    link: { href: "/concierge", label: "expressar interesse" },
    badge: "acesso antecipado",
  },
]

export default function LandingPage() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <div className="relative">
      {/* ════════════════════════════════════
          HERO
      ════════════════════════════════════ */}
      <section className="relative flex min-h-[100vh] flex-col overflow-hidden">
        {/* Background image */}
        <img
          src="/images/john-towner-3Kv48NS4WUU-unsplash.jpg"
          alt=""
          className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-[0.08] saturate-[0.4]"
        />

        {/* Warm glow */}
        <div className="pointer-events-none absolute -right-[10%] -top-[15%] h-[55vw] max-h-[700px] w-[55vw] max-w-[700px] rounded-full bg-[radial-gradient(circle,rgba(200,168,130,0.10)_0%,transparent_65%)]" />

        {/* Cool glow */}
        <div className="pointer-events-none absolute -bottom-[10%] -left-[8%] h-[40vw] max-h-[500px] w-[40vw] max-w-[500px] rounded-full bg-[radial-gradient(circle,rgba(100,130,180,0.07)_0%,transparent_65%)]" />

        {/* Grid overlay */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(rgba(250,250,249,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(250,250,249,0.02) 1px, transparent 1px)",
            backgroundSize: "80px 80px",
          }}
        />

        {/* Top decoration */}
        <div className="pointer-events-none absolute left-6 right-6 top-20 flex items-center justify-between lg:left-20 lg:right-20">
          <div className="h-px w-10 bg-foreground/15" />
          <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-foreground/20">
            motor de recomendacao
          </span>
          <div className="h-px w-10 bg-foreground/15" />
        </div>

        {/* Center content */}
        <div className="relative z-10 flex flex-1 flex-col items-center justify-center px-6">
          {/* CARACTR wordmark */}
          <h1
            className={`font-display text-[clamp(48px,12vw,180px)] font-extrabold leading-[0.88] tracking-[-0.04em] ${
              mounted ? "animate-fadeUp" : "opacity-0"
            }`}
          >
            CARACTR
          </h1>

          {/* Tagline */}
          <div
            className={`mt-8 flex items-center gap-6 md:mt-12 ${
              mounted ? "animate-fadeUp-d2" : "opacity-0"
            }`}
          >
            <div className="hidden h-px w-9 shrink-0 bg-gold sm:block" />
            <p className="text-center text-[clamp(13px,1.1vw,15px)] font-light tracking-wide text-foreground/40">
              O motor de recomendacao que te conhece a ti.
            </p>
          </div>

          {/* CTAs */}
          <div
            className={`mt-10 flex flex-wrap items-center justify-center gap-3 ${
              mounted ? "animate-fadeUp-d3" : "opacity-0"
            }`}
          >
            <Link
              href="/escolher"
              className="rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
            >
              comecar a experiencia
            </Link>
            <Link
              href="/analisar"
              className="rounded-full border border-foreground/20 px-6 py-3.5 text-[13px] font-medium text-foreground/70 transition-colors hover:border-gold/40 hover:text-gold"
            >
              analisar anuncio
            </Link>
          </div>
          <p className="mt-4 font-mono text-[10px] tracking-[1px] text-muted-foreground/30">
            Gratuito durante o lancamento
          </p>
        </div>

        {/* Bottom decoration */}
        <div className="pointer-events-none absolute bottom-6 left-6 right-6 flex items-end justify-between lg:bottom-8 lg:left-20 lg:right-20">
          <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-foreground/15">
            2026
          </span>
          <div className="flex items-center gap-2.5">
            <span className="font-mono text-[9px] uppercase tracking-[0.15em] text-foreground/20">
              scroll
            </span>
            <div className="h-px w-7 bg-foreground/15" />
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════
          HERO SPLIT — Headline + Image
      ════════════════════════════════════ */}
      <section className="relative grid min-h-[100vh] grid-cols-1 overflow-hidden md:grid-cols-2">
        {/* Left — headline */}
        <div className="relative z-10 flex flex-col justify-center px-6 py-20 md:py-0 lg:px-20">
          <p className="mb-5 text-[11px] font-normal uppercase tracking-[0.2em] text-muted-foreground">
            encontra o teu carro
          </p>
          <h2 className="font-display text-[clamp(32px,5vw,72px)] font-extrabold leading-[0.92] tracking-tight">
            O teu proximo
            <br />
            carro ja sabe
            <br />
            <span className="text-gold-dark">quem es.</span>
          </h2>

          <p className="mt-8 max-w-[320px] text-[clamp(14px,1.1vw,16px)] font-light leading-relaxed text-muted-foreground">
            5 perguntas sobre a tua vida.
            <br />
            Zero especificacoes tecnicas.
          </p>
          <div className="mt-7">
            <Link
              href="/escolher"
              className="inline-block rounded-full bg-gold px-8 py-3.5 text-[13px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
            >
              comecar a experiencia
            </Link>
          </div>
          <div className="mt-10 border-t border-border pt-6">
            <p className="text-sm text-muted-foreground">
              Tens um anuncio?{" "}
              <Link
                href="/analisar"
                className="border-b border-gold pb-px font-semibold text-gold-dark transition-colors hover:text-gold"
              >
                Analisa aqui
              </Link>
            </p>
          </div>
        </div>

        {/* Right — image */}
        <div className="relative hidden md:block">
          <img
            src="/images/taneli-lahtinen-Mie9wsHfXHc-unsplash.jpg"
            alt=""
            className="absolute inset-0 h-full w-full object-cover saturate-[0.9]"
          />
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-background to-transparent to-[14%]" />
        </div>
      </section>

      {/* ════════════════════════════════════
          STATEMENT
      ════════════════════════════════════ */}
      <section className="relative flex min-h-[100vh] flex-col items-center justify-center overflow-hidden bg-background px-6 py-20 text-center">
        {/* Subtle dark layer */}
        <div className="absolute inset-0 bg-[#050507]" />

        <div className="relative z-10 flex max-w-[860px] flex-col items-center">
          <h2 className="font-display text-[clamp(40px,8vw,108px)] font-extrabold leading-[1.05] tracking-[-0.04em] text-foreground">
            NAO PRECISAS
          </h2>
          <h2 className="font-display text-[clamp(40px,8vw,108px)] font-normal leading-[0.88] tracking-[-0.04em] text-foreground/20">
            de saber nada.
          </h2>
          <h3 className="mt-6 font-display text-[clamp(18px,2.2vw,32px)] font-bold tracking-tight text-gold">
            So precisas de te conhecer.
          </h3>
          <p className="mx-auto mt-5 max-w-[440px] text-[clamp(13px,1.1vw,16px)] font-light leading-relaxed text-foreground/40">
            Descreve-nos o teu estilo de vida e os teus habitos ao volante.
            O algoritmo faz o resto — sem tabelas de cilindradas, sem confusao.
          </p>

          {/* Stats */}
          <div className="mt-10 grid w-full grid-cols-3 gap-4 border-t border-foreground/[0.08] pt-8 md:gap-12">
            {STATS.map((m, i) => (
              <div key={i} className="text-center">
                <p className="font-mono text-[clamp(18px,2vw,26px)] font-bold leading-none tracking-tight text-gold">
                  {m.value}
                </p>
                <p className="mt-1.5 text-xs text-foreground/45">{m.label}</p>
                <p className="mt-0.5 font-mono text-[9px] tracking-[0.5px] text-foreground/[0.18]">
                  {m.sub}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════
          PROCESS
      ════════════════════════════════════ */}
      <section className="relative flex min-h-[100vh] flex-col justify-center overflow-hidden px-6 py-20 lg:px-20">
        <div className="relative z-10 mx-auto w-full max-w-[1100px]">
          <p className="mb-5 text-[11px] font-normal uppercase tracking-[0.2em] text-muted-foreground">
            como funciona
          </p>
          <h2 className="mb-9 font-display text-[clamp(28px,4vw,52px)] font-extrabold leading-[1.05] tracking-tight">
            Simples para ti.
            <br />
            <span className="text-gold-dark">Inteligente por dentro.</span>
          </h2>

          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4 lg:gap-12">
            {STEPS.map((step, i) => (
              <div
                key={i}
                className="border-t-2 border-border pt-6"
              >
                <div className="mb-5 flex items-start justify-between">
                  <span className="font-display text-[clamp(32px,4vw,56px)] font-extrabold leading-none text-gold/55">
                    {step.n}
                  </span>
                  {step.badge && (
                    <span className="mt-1 whitespace-nowrap rounded-full border border-gold px-2.5 py-1 font-mono text-[9px] uppercase tracking-[1.2px] text-gold-dark">
                      {step.badge}
                    </span>
                  )}
                </div>
                <h3 className="mb-3.5 font-display text-[clamp(20px,2vw,28px)] font-extrabold tracking-tight">
                  {step.title}
                </h3>
                <p className="text-sm font-normal leading-relaxed text-foreground/55">
                  {step.desc}
                </p>
                {step.link && (
                  <Link
                    href={step.link.href}
                    className="mt-4 inline-block border-b border-gold pb-px font-mono text-[10px] tracking-[0.5px] text-gold-dark transition-opacity hover:opacity-70"
                  >
                    {step.link.label}
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════
          FINAL CTA
      ════════════════════════════════════ */}
      <section className="relative flex min-h-[100vh] flex-col items-center justify-center overflow-hidden">
        <img
          src="/images/jesse-bowser-c0I4ahyGIkA-unsplash.jpg"
          alt=""
          loading="lazy"
          className="absolute inset-0 h-full w-full object-cover saturate-[0.7]"
        />
        <div className="absolute inset-0 bg-[rgba(13,12,10,0.65)]" />

        <div className="relative z-10 px-6 text-center">
          <p className="mb-5 text-[11px] font-normal uppercase tracking-[0.25em] text-foreground/30">
            2 minutos · zero pressao
          </p>
          <h2 className="font-display text-[clamp(48px,10vw,128px)] font-extrabold leading-[0.85] tracking-[-0.04em] text-foreground">
            PRONTO?
          </h2>
          <div className="mt-11">
            <Link
              href="/escolher"
              className="rounded-full bg-gold px-10 py-4 text-[14px] font-semibold tracking-wide text-background transition-colors hover:bg-gold-dark"
            >
              comecar a experiencia
            </Link>
          </div>
        </div>

        {/* Bottom decoration */}
        <div className="pointer-events-none absolute bottom-6 left-6 right-6 flex items-center justify-center lg:bottom-8">
          <span className="font-mono text-[9px] uppercase tracking-[2px] text-foreground/15">
            informar nunca assustar
          </span>
        </div>
      </section>
    </div>
  )
}
