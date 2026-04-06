"use client";

import Link from "next/link";
import { useEffect, useState, useRef, useCallback } from "react";

/* ── helpers ── */
function lerp(a: number, b: number, t: number) {
  return a + (b - a) * Math.min(Math.max(t, 0), 1);
}
function easeInOut(t: number) {
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}


export default function LandingPage() {
  const [mounted, setMounted] = useState(false);
  const [visibleSections, setVisibleSections] = useState<Set<string>>(new Set());
  const [showStickyNav, setShowStickyNav] = useState(false);
  const [navVisible, setNavVisible] = useState(false);
  const [navOnDark, setNavOnDark] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const caractrRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef(0);
  const scrollProgressRef = useRef(0);

  /* ── Scroll-driven CARACTR animation (direct DOM, no re-render) ── */
  const updateCaractr = useCallback(() => {
    const el = caractrRef.current;
    if (!el) return;

    const p = scrollProgressRef.current;
    const e = easeInOut(p);
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    const startFont = Math.min(Math.max(0.11 * vw, 36), 160);
    const endFont = 15;
    const scale = lerp(startFont, endFont, e) / startFont;

    const navLeft = Math.min(Math.max(0.05 * vw, 32), 80);
    const navTop = 32 + endFont / 2;
    const left = lerp(vw / 2, navLeft, e);
    const top = lerp(vh / 2, navTop, e);

    const opacity = p > 0.9 ? 0 : p > 0.7 ? lerp(1, 0, (p - 0.7) / 0.2) : 1;

    el.style.fontSize = `${startFont}px`;
    el.style.left = `${left}px`;
    el.style.top = `${top}px`;
    el.style.transform = `translate(-50%, -50%) scale(${scale})`;
    el.style.opacity = `${opacity}`;
  }, []);

  useEffect(() => {
    setMounted(true);
    const container = scrollRef.current;
    if (!container) return;

    // Intersection observer for section reveals
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisibleSections((prev) => new Set([...prev, entry.target.id]));
          }
        });
      },
      { threshold: 0.2, root: container }
    );
    container.querySelectorAll("[data-reveal]").forEach((el) => observer.observe(el));

    // Scroll handler — RAF for performance
    const handleScroll = () => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        const scrollTop = container.scrollTop;
        const sectionH = window.innerHeight;
        const p = Math.min(scrollTop / sectionH, 1);
        scrollProgressRef.current = p;

        updateCaractr();

        // Threshold-based state updates (infrequent)
        const pastBrand = p > 0.75;
        const pastHero = scrollTop > sectionH * 1.9;
        // Dark sections: statement (2–3 × vh) and final (4 × vh+)
        const onDark = (scrollTop > sectionH * 1.9 && scrollTop < sectionH * 3) || scrollTop >= sectionH * 4;
        setNavVisible(pastBrand);
        setShowStickyNav(pastHero);
        setNavOnDark(onDark);
      });
    };
    container.addEventListener("scroll", handleScroll, { passive: true });

    // Initial position
    updateCaractr();

    return () => {
      observer.disconnect();
      container.removeEventListener("scroll", handleScroll);
      cancelAnimationFrame(rafRef.current);
    };
  }, [updateCaractr]);

  const visible = (id: string) => visibleSections.has(id);
  const reveal = (id: string, delay = 0): React.CSSProperties => ({
    transform: visible(id) ? "translateY(0)" : "translateY(32px)",
    opacity: visible(id) ? 1 : 0,
    transition: `transform 0.8s cubic-bezier(0.16,1,0.3,1) ${delay}s, opacity 0.8s ease ${delay}s`,
  });

  return (
    <>
      {/* ── Fixed scroll-driven CARACTR ── */}
      <div
        ref={caractrRef}
        aria-hidden
        style={{
          position: "fixed",
          zIndex: 100,
          fontFamily: "var(--font-display)",
          fontWeight: 800,
          letterSpacing: "-0.04em",
          lineHeight: 0.88,
          color: "var(--fg-inv)",
          pointerEvents: "none",
          willChange: "transform, opacity",
          opacity: 0,
        }}
      >
        CARACTR
      </div>

      {/* ── Sticky nav (appears after hero) ── */}
      <nav className={`sticky-nav ${showStickyNav ? "is-visible" : ""} ${navOnDark ? "nav-dark" : ""}`}>
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "14px",
            fontWeight: 700,
            letterSpacing: "0.12em",
            color: navOnDark ? "var(--fg-inv)" : "var(--fg)",
            transition: "color 0.3s ease",
          }}
        >
          CARACTR
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Link href="/analisar" className="pill-btn-accent">analisar anúncio</Link>
          <Link href="/escolher" className={navOnDark ? "pill-btn-inv" : "pill-btn"}>começar</Link>
        </div>
      </nav>

      <div
        ref={scrollRef}
        style={{
          height: "100vh",
          overflowY: "auto",
          scrollSnapType: "y mandatory",
          overscrollBehavior: "contain",
        }}
      >

        {/* ════════════════════════════════════
            SECTION 0 — BRAND INTRO
        ════════════════════════════════════ */}
        <section
          style={{
            minHeight: "100vh",
            scrollSnapAlign: "start", scrollSnapStop: "always",
            background: "var(--bg-dark)",
            position: "relative",
            overflow: "hidden",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {/* Road through forest — subtle bg */}
          <img
            src="/images/john-towner-3Kv48NS4WUU-unsplash.jpg"
            alt=""
            style={{
              position: "absolute",
              inset: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "center",
              opacity: 0.12,
              filter: "saturate(0.4)",
              pointerEvents: "none",
            }}
          />

          {/* Editorial grid overlay */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundImage: `
                linear-gradient(rgba(242,239,233,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(242,239,233,0.03) 1px, transparent 1px)
              `,
              backgroundSize: "80px 80px",
              pointerEvents: "none",
            }}
          />

          {/* Warm glow — top right */}
          <div
            style={{
              position: "absolute",
              top: "-15%",
              right: "-10%",
              width: "55vw",
              height: "55vw",
              maxWidth: "700px",
              maxHeight: "700px",
              borderRadius: "50%",
              background: "radial-gradient(circle, rgba(200,168,130,0.10) 0%, transparent 65%)",
              pointerEvents: "none",
            }}
          />

          {/* Cool glow — bottom left */}
          <div
            style={{
              position: "absolute",
              bottom: "-10%",
              left: "-8%",
              width: "40vw",
              height: "40vw",
              maxWidth: "500px",
              maxHeight: "500px",
              borderRadius: "50%",
              background: "radial-gradient(circle, rgba(100,130,180,0.07) 0%, transparent 65%)",
              pointerEvents: "none",
            }}
          />

          {/* Top decoration */}
          <div
            style={{
              position: "absolute",
              top: "clamp(32px, 5vh, 64px)",
              left: "clamp(32px, 5vw, 80px)",
              right: "clamp(32px, 5vw, 80px)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              pointerEvents: "none",
            }}
          >
            <div style={{ width: "40px", height: "1px", background: "rgba(242,239,233,0.15)" }} />
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(242,239,233,0.2)" }}>
              motor de recomendação
            </span>
            <div style={{ width: "40px", height: "1px", background: "rgba(242,239,233,0.15)" }} />
          </div>

          {/* Invisible spacer for the fixed CARACTR */}
          <div style={{ height: "0.88em", fontSize: "clamp(36px, 11vw, 160px)", visibility: "hidden" }} aria-hidden>CARACTR</div>

          {/* Tagline */}
          <div
            className={mounted ? "animate-fadeUp-d2" : ""}
            style={{ opacity: mounted ? undefined : 0, marginTop: "clamp(32px, 5vh, 64px)", display: "flex", alignItems: "center", gap: "24px", position: "relative", zIndex: 2 }}
          >
            <div style={{ width: "36px", height: "1px", background: "var(--accent)", flexShrink: 0 }} />
            <p style={{ fontFamily: "var(--font-body)", fontSize: "clamp(13px, 1.1vw, 15px)", fontWeight: 300, color: "rgba(242,239,233,0.40)", letterSpacing: "0.04em" }}>
              O motor de recomendação que te conhece a ti.
            </p>
          </div>

          {/* Bottom row */}
          <div
            className={mounted ? "animate-fadeUp-d3" : ""}
            style={{ opacity: mounted ? undefined : 0, position: "absolute", bottom: "clamp(24px, 4vh, 48px)", left: "clamp(32px, 5vw, 80px)", right: "clamp(32px, 5vw, 80px)", display: "flex", justifyContent: "space-between", alignItems: "flex-end", pointerEvents: "none" }}
          >
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "0.18em", textTransform: "uppercase", color: "rgba(242,239,233,0.15)" }}>2026</span>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "0.15em", textTransform: "uppercase", color: "rgba(242,239,233,0.2)" }}>scroll</span>
              <div style={{ width: "28px", height: "1px", background: "rgba(242,239,233,0.15)" }} />
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════
            SECTION 1 — HERO
        ════════════════════════════════════ */}
        <section
          className="hero-grid"
          style={{
            minHeight: "100vh",
            scrollSnapAlign: "start", scrollSnapStop: "always",
            background: "var(--bg)",
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gridTemplateRows: "auto 1fr",
            position: "relative",
            overflow: "hidden",
          }}
        >
          {/* Nav */}
          <nav style={{ gridColumn: "1 / -1", padding: "32px clamp(32px, 5vw, 80px)", display: "flex", alignItems: "center", justifyContent: "space-between", position: "relative", zIndex: 10 }}>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "15px",
                fontWeight: 700,
                letterSpacing: "0.12em",
                color: "var(--fg)",
                opacity: navVisible ? 1 : 0,
                transition: "opacity 0.3s ease",
              }}
            >
              CARACTR
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <Link href="/analisar" className="pill-btn-accent">analisar anúncio</Link>
              <Link href="/escolher" className="pill-btn">começar</Link>
            </div>
          </nav>

          {/* Left — headline */}
          <div
            className="hero-text-col"
            style={{ gridColumn: "1", padding: "0 clamp(32px, 5vw, 80px) clamp(56px, 7vw, 96px)", display: "flex", flexDirection: "column", justifyContent: "flex-end", position: "relative", zIndex: 10 }}
          >
            <div className={mounted ? "animate-fadeUp" : ""} style={{ opacity: mounted ? undefined : 0 }}>
              <p style={{ fontFamily: "var(--font-body)", fontSize: "11px", fontWeight: 400, letterSpacing: "0.2em", textTransform: "uppercase", color: "var(--muted)", marginBottom: "20px" }}>
                encontra o teu carro
              </p>
              <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(32px, 5vw, 72px)", fontWeight: 800, lineHeight: 0.92, letterSpacing: "-0.03em", color: "var(--fg)" }}>
                O teu próximo
                <br />
                carro já sabe
                <br />
                <span style={{ color: "var(--accent-dark)" }}>quem és.</span>
              </h2>
            </div>

            <div className={mounted ? "animate-fadeUp-d2" : ""} style={{ opacity: mounted ? undefined : 0, marginTop: "32px" }}>
              <p style={{ fontFamily: "var(--font-body)", fontSize: "clamp(14px, 1.1vw, 16px)", fontWeight: 300, color: "var(--muted)", lineHeight: 1.75, maxWidth: "320px" }}>
                5 perguntas sobre a tua vida.
                <br />
                Zero especificações técnicas.
              </p>
              <div style={{ marginTop: "28px" }}>
                <Link href="/escolher" className="pill-btn-solid">começar a experiência</Link>
              </div>
              <div style={{ marginTop: "40px", paddingTop: "24px", borderTop: "1px solid var(--border)" }}>
                <p style={{ fontSize: "14px", fontFamily: "var(--font-body)", color: "var(--muted)", fontWeight: 400 }}>
                  Tens um anúncio?{" "}
                  <Link
                    href="/analisar"
                    style={{
                      color: "var(--accent-dark)",
                      textDecoration: "none",
                      fontWeight: 600,
                      borderBottom: "1.5px solid var(--accent)",
                      paddingBottom: "1px",
                    }}
                  >
                    Analisa aqui →
                  </Link>
                </p>
              </div>
            </div>
          </div>

          {/* Right — aerial road image */}
          <div className="hero-image-col" style={{ gridColumn: "2", position: "relative", overflow: "hidden" }}>
            <img
              src="/images/taneli-lahtinen-Mie9wsHfXHc-unsplash.jpg"
              alt=""
              style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", opacity: mounted ? 1 : 0, transition: "opacity 1.2s ease", filter: "saturate(0.9)" }}
            />
            <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to right, var(--bg) 0%, transparent 14%)", pointerEvents: "none" }} />
          </div>
        </section>

        {/* ════════════════════════════════════
            SECTION 2 — STATEMENT
        ════════════════════════════════════ */}
        <section
          id="statement"
          data-reveal
          style={{ minHeight: "100vh", scrollSnapAlign: "start", scrollSnapStop: "always", background: "var(--bg-dark)", display: "flex", flexDirection: "column", alignItems: "center", paddingTop: "clamp(120px, 14vh, 160px)", paddingBottom: "clamp(56px, 7vh, 100px)", paddingLeft: "clamp(32px, 5vw, 80px)", paddingRight: "clamp(32px, 5vw, 80px)", position: "relative", overflow: "hidden", textAlign: "center" }}
        >
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", position: "relative", zIndex: 10, maxWidth: "800px", width: "100%" }}>
            <div style={reveal("statement", 0.05)}>
              <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(40px, 8vw, 108px)", fontWeight: 800, lineHeight: 1.1, letterSpacing: "-0.04em", color: "var(--fg-inv)" }}>
                NÃO PRECISAS
              </h2>
            </div>
            <div style={{ ...reveal("statement", 0.15), marginTop: "-0.06em" }}>
              <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(40px, 8vw, 108px)", fontWeight: 400, lineHeight: 0.88, letterSpacing: "-0.04em", color: "var(--fg-inv)", opacity: 0.2 }}>
                de saber nada.
              </h2>
            </div>
            <div style={{ ...reveal("statement", 0.28), marginTop: "clamp(28px, 3.5vw, 52px)" }}>
              <h3 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(20px, 3vw, 40px)", fontWeight: 700, letterSpacing: "-0.02em", color: "var(--accent)" }}>
                Só precisas de te conhecer.
              </h3>
            </div>
            <div style={{ ...reveal("statement", 0.4), marginTop: "28px" }}>
              <p style={{ fontFamily: "var(--font-body)", fontSize: "clamp(14px, 1.2vw, 17px)", fontWeight: 300, color: "rgba(242,239,233,0.4)", lineHeight: 1.85, maxWidth: "460px", margin: "0 auto" }}>
                Descreve-nos o teu estilo de vida e os teus hábitos ao volante.
                O algoritmo faz o resto — sem tabelas de cilindradas, sem confusão.
              </p>
            </div>

            {/* ── Stats ── */}
            <div style={{
              ...reveal("statement", 0.55),
              marginTop: "clamp(48px, 6vw, 72px)",
              paddingTop: "clamp(24px, 3vw, 36px)",
              borderTop: "1px solid rgba(242,239,233,0.08)",
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: "clamp(16px, 3vw, 48px)",
            }}>
              {[
                { value: "354",        label: "perfis detalhados",  sub: "condução, fiabilidade e nuances de versão" },
                { value: "200+",       label: "modelos analisados", sub: "desde 2010, em expansão contínua" },
                { value: "tempo real", label: "dados de mercado",   sub: "preços a partir de anúncios reais" },
              ].map((m, i) => (
                <div key={i} style={{ textAlign: "center" }}>
                  <p style={{ fontFamily: "var(--font-mono)", fontSize: "clamp(18px, 2vw, 26px)", fontWeight: 700, color: "var(--accent)", letterSpacing: "-0.01em", lineHeight: 1, marginBottom: "6px", whiteSpace: "nowrap" }}>
                    {m.value}
                  </p>
                  <p style={{ fontFamily: "var(--font-body)", fontSize: "12px", color: "rgba(242,239,233,0.45)", marginBottom: "2px" }}>
                    {m.label}
                  </p>
                  <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "0.5px", color: "rgba(242,239,233,0.18)", lineHeight: 1.4 }}>
                    {m.sub}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════
            SECTION 3 — PROCESS
        ════════════════════════════════════ */}
        <section
          id="process"
          data-reveal
          style={{ minHeight: "100vh", scrollSnapAlign: "start", scrollSnapStop: "always", background: "var(--bg)", display: "flex", flexDirection: "column", justifyContent: "center", padding: "clamp(40px, 5vw, 72px) clamp(32px, 5vw, 80px)", position: "relative", overflow: "hidden" }}
        >
          <div style={{ position: "relative", zIndex: 10, maxWidth: "1100px", margin: "0 auto", width: "100%" }}>
            <div style={reveal("process", 0)}>
              <p style={{ fontFamily: "var(--font-body)", fontSize: "11px", fontWeight: 400, letterSpacing: "0.2em", textTransform: "uppercase", color: "var(--muted)", marginBottom: "20px" }}>
                como funciona
              </p>
              <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(28px, 4vw, 52px)", fontWeight: 800, letterSpacing: "-0.03em", color: "var(--fg)", lineHeight: 1.05, marginBottom: "36px" }}>
                Simples para ti.<br />
                <span style={{ color: "var(--accent-dark)" }}>Inteligente por dentro.</span>
              </h2>
            </div>

            <div className="process-cols" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "clamp(16px, 3vw, 48px)" }}>
              {[
                {
                  n: "01",
                  title: "Conta-nos",
                  desc: "Sobre a tua vida. O que fazes, onde vais, quem levas. Sem cilindradas, sem especificações técnicas.",
                  link: null,
                  badge: null,
                },
                {
                  n: "02",
                  title: "Descobre",
                  desc: "5 modelos selecionados para o teu perfil. Com argumentos reais, tradeoffs honestos e linguagem humana.",
                  link: null,
                  badge: null,
                },
                {
                  n: "03",
                  title: "Analisa",
                  desc: "Encontraste um anúncio? Cruzamos o preço com anúncios reais do mercado, verificamos quilómetros, detetamos equipamento e avaliamos o vendedor.",
                  link: { href: "/analisar", label: "analisar anúncio →" },
                  badge: null,
                },
                {
                  n: "04",
                  title: "Concierge",
                  desc: "Preferes que façamos tudo? Pesquisamos, analisamos e entregamos uma seleção curada. Em fase de lançamento — gratuito para os primeiros.",
                  link: { href: "/concierge", label: "expressar interesse →" },
                  badge: "acesso antecipado",
                },
              ].map((step, i) => (
                <div key={i} style={{ ...reveal("process", 0.1 + i * 0.12), paddingTop: "clamp(20px, 3vw, 36px)", borderTop: "2px solid var(--border)" }}>
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "20px" }}>
                    <span style={{ fontFamily: "var(--font-display)", fontSize: "clamp(32px, 4vw, 56px)", fontWeight: 800, color: "var(--accent)", opacity: 0.55, lineHeight: 1 }}>
                      {step.n}
                    </span>
                    {step.badge && (
                      <span style={{
                        fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.2px",
                        textTransform: "uppercase", color: "var(--accent-dark)", border: "1px solid var(--accent)",
                        borderRadius: "100px", padding: "4px 10px", whiteSpace: "nowrap", marginTop: "4px",
                      }}>
                        {step.badge}
                      </span>
                    )}
                  </div>
                  <h3 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(20px, 2vw, 28px)", fontWeight: 800, color: "var(--fg)", marginBottom: "14px", letterSpacing: "-0.025em" }}>
                    {step.title}
                  </h3>
                  <p style={{ fontFamily: "var(--font-body)", fontSize: "14px", fontWeight: 400, color: "var(--fg)", opacity: 0.55, lineHeight: 1.75, marginBottom: step.link ? "16px" : 0 }}>
                    {step.desc}
                  </p>
                  {step.link && (
                    <Link href={step.link.href} style={{
                      fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "0.5px",
                      color: "var(--accent-dark)", textDecoration: "none",
                      borderBottom: "1px solid var(--accent)", paddingBottom: "1px",
                      transition: "opacity 0.2s ease",
                    }}>
                      {step.link.label}
                    </Link>
                  )}
                </div>
              ))}
            </div>

          </div>
        </section>

        {/* ════════════════════════════════════
            SECTION 4 — CTA FINAL
        ════════════════════════════════════ */}
        <section
          id="final"
          data-reveal
          style={{ minHeight: "100vh", scrollSnapAlign: "start", scrollSnapStop: "always", position: "relative", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", overflow: "hidden" }}
        >
          <img
            src="/images/jesse-bowser-c0I4ahyGIkA-unsplash.jpg"
            alt=""
            loading="lazy"
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", filter: "saturate(0.7)" }}
          />
          <div style={{ position: "absolute", inset: 0, background: "rgba(13,12,10,0.65)" }} />

          <div style={{ position: "relative", zIndex: 10, textAlign: "center", padding: "0 clamp(32px, 5vw, 80px)" }}>
            <div style={reveal("final", 0)}>
              <p style={{ fontFamily: "var(--font-body)", fontSize: "11px", fontWeight: 400, letterSpacing: "0.25em", textTransform: "uppercase", color: "rgba(242,239,233,0.3)", marginBottom: "20px" }}>
                2 minutos · zero pressão
              </p>
              <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(48px, 10vw, 128px)", fontWeight: 800, letterSpacing: "-0.04em", lineHeight: 0.85, color: "var(--fg-inv)" }}>
                PRONTO?
              </h2>
            </div>
            <div style={{ ...reveal("final", 0.2), marginTop: "44px" }}>
              <Link href="/escolher" className="pill-btn-inv">começar a experiência</Link>
            </div>
          </div>

          <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, padding: "20px clamp(32px, 5vw, 80px)", display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid rgba(242,239,233,0.06)", zIndex: 10 }}>
            <span style={{ fontFamily: "var(--font-display)", fontSize: "11px", fontWeight: 700, letterSpacing: "0.12em", color: "rgba(242,239,233,0.2)" }}>CARACTR</span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "rgba(242,239,233,0.15)", letterSpacing: "2px", textTransform: "uppercase" }}>informar nunca assustar</span>
            <span style={{ fontFamily: "var(--font-body)", fontSize: "11px", color: "rgba(242,239,233,0.2)" }}>2026</span>
          </div>
        </section>
      </div>
    </>
  );
}
