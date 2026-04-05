"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Analytics } from "@/lib/analytics";

// ── V4 Questions (P1–P6). Dream car (P7) and Budget (P8) are special steps. ──
const QUESTIONS = [
  {
    id: "p1_context",
    label: "01 — Dia a dia",
    question: "Onde passas mais tempo a conduzir?",
    type: "choice" as const,
    options: [
      { value: "cidade",  label: "Cidade",   desc: "Trânsito, estacionamento, trajetos curtos" },
      { value: "misto",   label: "Misto",    desc: "Um pouco de tudo — cidade e estrada" },
      { value: "estrada", label: "Estrada",  desc: "Autoestrada, viagens longas, muitos km" },
      { value: "familia", label: "Família",  desc: "Escola, compras, logística familiar" },
    ],
  },
  {
    id: "p2_relationship",
    label: "02 — Relação com o carro",
    question: "Como vês o teu carro?",
    type: "slider" as const,
    min: 0, max: 100,
    leftLabel: "É só um meio de transporte",
    rightLabel: "Adoro conduzir",
  },
  {
    id: "p3_driving_style",
    label: "03 — Estilo de condução",
    question: "Como preferes sentir o carro?",
    type: "slider" as const,
    min: 0, max: 100,
    leftLabel: "Conforto e suavidade",
    rightLabel: "Sentir a estrada",
  },
  {
    id: "p4_risk",
    label: "04 — Perfil",
    question: "Segurança total ou um pouco de carácter?",
    type: "slider" as const,
    min: 0, max: 100,
    leftLabel: "Segurança primeiro",
    rightLabel: "Gosto de carácter",
  },
  {
    id: "p5_presence",
    label: "05 — Presença",
    question: "O que queres que o teu carro comunique?",
    type: "slider" as const,
    min: 0, max: 100,
    leftLabel: "Discreto — não preciso de atenção",
    rightLabel: "Com presença — gosto de ser notado",
  },
  {
    id: "p6_aversion",
    label: "06 — O que não toleras",
    question: "O que seria inaceitável no teu próximo carro?",
    type: "choice" as const,
    options: [
      { value: "fiabilidade", label: "Problemas mecânicos", desc: "Avarias, custos inesperados, falta de confiança" },
      { value: "conforto",    label: "Desconforto",         desc: "Barulho, suspensão dura, viagens longas a sofrer" },
      { value: "espaco",      label: "Falta de espaço",     desc: "Pouco espaço para passageiros ou bagagem" },
      { value: "potencia",    label: "Falta de resposta",   desc: "Motor fraco, aceleração lenta, sem dinamismo" },
    ],
  },
];

const DREAM_CARS_FALLBACK = [
  { id: "porsche_911",      name: "Porsche 911" },
  { id: "bmw_m3",           name: "BMW M3" },
  { id: "mercedes_s",       name: "Mercedes Classe S" },
  { id: "tesla_model3",     name: "Tesla Model 3" },
  { id: "volvo_xc60",       name: "Volvo XC60" },
  { id: "mazda_mx5",        name: "Mazda MX-5" },
  { id: "range_rover",      name: "Range Rover" },
  { id: "toyota_landcruiser", name: "Toyota Land Cruiser" },
];

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Default slider values (stored as 0–100, sent as 0.0–1.0)
const SLIDER_DEFAULTS: Record<string, number> = {
  p2_relationship: 50,
  p3_driving_style: 50,
  p4_risk: 50,
  p5_presence: 50,
};

const DIM_LABELS: Record<string, string> = {
  economy: "economia", comfort: "conforto", driving: "condução",
  practical: "praticidade", status: "imagem", reliability: "fiabilidade",
};

// Build a minimal profile narrative from existing response data (fallback for Phase 1)
function buildFallbackNarrative(data: any): { summary: string; lines: string[] } {
  const profile = data.profile || {};
  const sorted = Object.entries(profile).sort((a: any, b: any) => b[1] - a[1]);
  const top2 = sorted.slice(0, 2).map(([k]) => DIM_LABELS[k] || k);
  const summary = top2.length >= 2
    ? `${cap(top2[0])} e ${top2[1]} como prioridades.`
    : top2.length === 1
      ? `${cap(top2[0])} como prioridade principal.`
      : "Perfil equilibrado.";

  const lines: string[] = [];
  if (top2.length >= 2) {
    lines.push(`${cap(top2[0])} e ${top2[1]} estão no topo das tuas prioridades.`);
  }
  if (data.answers?.p6_aversion && data.answers.p6_aversion !== "nenhuma") {
    const aversionMap: Record<string, string> = {
      fiabilidade: "Ficou claro: problemas mecânicos são inaceitáveis para ti.",
      conforto: "Ficou claro: desconforto é inaceitável para ti.",
      espaco: "Ficou claro: falta de espaço é inaceitável para ti.",
      potencia: "Ficou claro: falta de resposta do motor é inaceitável para ti.",
    };
    const line = aversionMap[data.answers.p6_aversion];
    if (line) lines.push(line);
  }
  return { summary, lines };
}

function cap(s: string) { return s.charAt(0).toUpperCase() + s.slice(1); }

export default function EscolherPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({
    ...SLIDER_DEFAULTS,
    p8_budget_min: 10000,
    p8_budget_max: 25000,
  });
  const [dreamCars, setDreamCars] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [transitioning, setTransitioning] = useState(false);

  // Return visit state
  const [existingProfileAge, setExistingProfileAge] = useState<number | null>(null);

  // Profile screen state: "wizard" | "interpreting" | "narrative"
  const [profileStage, setProfileStage] = useState<"wizard" | "interpreting" | "narrative">("wizard");
  const [narrativeData, setNarrativeData] = useState<any>(null);
  const [narrativeVisible, setNarrativeVisible] = useState(false);

  const startTimeRef = useRef<number>(Date.now());

  // Check for existing profile on mount
  useEffect(() => {
    Analytics.selectorStarted();
    startTimeRef.current = Date.now();

    const timestamp = localStorage.getItem("caractr_profile_timestamp");
    if (timestamp) {
      const ageDays = Math.floor((Date.now() - new Date(timestamp).getTime()) / (1000 * 60 * 60 * 24));
      setExistingProfileAge(ageDays);
      // Fire return visit event
      const stored = localStorage.getItem("caractr_results");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          Analytics.returnVisit(parsed.session_id || "", ageDays);
        } catch {}
      }
    }
  }, []);

  // Step layout: 0–5 = QUESTIONS, 6 = dream car, 7 = budget
  const totalSteps = QUESTIONS.length + 2; // 8
  const isDreamStep = step === QUESTIONS.length;       // step 6
  const isBudgetStep = step === QUESTIONS.length + 1;  // step 7
  const current = step < QUESTIONS.length ? QUESTIONS[step] : null;
  const progress = ((step + 1) / totalSteps) * 100;

  useEffect(() => {
    if (isDreamStep) fetchDreamCars();
  }, [step]);

  const fetchDreamCars = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/dream-cars`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          p1_context:       answers.p1_context || "misto",
          p2_relationship:  (answers.p2_relationship ?? 50) / 100,
          p3_driving_style: (answers.p3_driving_style ?? 50) / 100,
          p4_risk:          (answers.p4_risk ?? 50) / 100,
          p5_presence:      (answers.p5_presence ?? 50) / 100,
          p6_aversion:      answers.p6_aversion || "nenhuma",
          p8_budget_min:    answers.p8_budget_min || 10000,
          p8_budget_max:    answers.p8_budget_max || 25000,
        }),
      });
      const data = await res.json();
      setDreamCars(data.dream_cars || DREAM_CARS_FALLBACK);
    } catch {
      setDreamCars(DREAM_CARS_FALLBACK);
    } finally {
      setLoading(false);
    }
  };

  const goToStep = (next: number) => {
    setTransitioning(true);
    setTimeout(() => {
      setStep(next);
      setTransitioning(false);
    }, 250);
  };

  const selectChoice = (field: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [field]: value }));
    Analytics.stepCompleted(step + 1, field, value);
    setTimeout(() => goToStep(Math.min(step + 1, totalSteps - 1)), 300);
  };

  const submit = async () => {
    setSubmitting(true);
    Analytics.selectorCompleted(
      Date.now() - startTimeRef.current,
      answers.p8_budget_max || 25000
    );
    try {
      const payload = {
        p1_context:       answers.p1_context || "misto",
        p2_relationship:  (answers.p2_relationship ?? 50) / 100,
        p3_driving_style: (answers.p3_driving_style ?? 50) / 100,
        p4_risk:          (answers.p4_risk ?? 50) / 100,
        p5_presence:      (answers.p5_presence ?? 50) / 100,
        p6_aversion:      answers.p6_aversion || "nenhuma",
        p7_dream_car:     answers.p7_dream_car || null,
        p8_budget_min:    answers.p8_budget_min || 10000,
        p8_budget_max:    answers.p8_budget_max || 25000,
      };
      const res = await fetch(`${API}/api/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      // Store in localStorage with timestamp
      localStorage.setItem("caractr_results", JSON.stringify(data));
      localStorage.setItem("caractr_profile_timestamp", new Date().toISOString());
      setNarrativeData(data);
      // Enter profile interpretation screen
      setProfileStage("interpreting");
      Analytics.profileShown(data.session_id || "");
      // After 1.5s, transition to narrative card
      setTimeout(() => {
        setProfileStage("narrative");
        setTimeout(() => setNarrativeVisible(true), 80);
      }, 1500);
    } catch (err) {
      console.error("Submit error:", err);
      setSubmitError("Erro ao calcular o perfil. Verifica a ligação e tenta novamente.");
      setSubmitting(false);
    }
  };

  const goToResults = () => {
    router.push("/resultados");
  };

  // ── Slider value for the current step ──
  const sliderVal = current?.type === "slider"
    ? (answers[current.id] ?? SLIDER_DEFAULTS[current.id] ?? 50)
    : 50;

  // ── Profile interpretation screens ──────────────────────────────────────
  if (profileStage === "interpreting") {
    return (
      <main style={{
        minHeight: "100vh",
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        background: "var(--bg)", color: "var(--fg)",
        padding: "0 clamp(24px, 5vw, 64px)",
      }}>
        <div style={{ textAlign: "center" }}>
          <div style={{
            width: "32px", height: "2px", background: "var(--accent)",
            borderRadius: "1px", margin: "0 auto 28px",
            animation: "pulse 1s ease-in-out infinite",
          }} />
          <p style={{
            fontFamily: "var(--font-mono)", fontSize: "11px",
            letterSpacing: "2px", color: "var(--accent)",
            textTransform: "uppercase",
          }}>
            A analisar o teu perfil...
          </p>
        </div>
      </main>
    );
  }

  if (profileStage === "narrative" && narrativeData) {
    const narrative = narrativeData.profile_narrative;
    const fallback = buildFallbackNarrative(narrativeData);
    const lines: string[] = narrative
      ? [narrative.priorities, narrative.tension, narrative.aversion, narrative.identity, narrative.context].filter(Boolean) as string[]
      : fallback.lines;
    const summary = narrative?.summary || fallback.summary;

    return (
      <main style={{
        minHeight: "100vh",
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        background: "var(--bg)", color: "var(--fg)",
        padding: "0 clamp(24px, 5vw, 64px)",
      }}>
        <div style={{
          maxWidth: "580px", width: "100%",
          opacity: narrativeVisible ? 1 : 0,
          transform: narrativeVisible ? "translateY(0)" : "translateY(20px)",
          transition: "opacity 0.5s ease, transform 0.5s ease",
        }}>
          {/* Header */}
          <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "20px" }} />
          <p style={{
            fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--accent)",
            marginBottom: "20px", textTransform: "uppercase", letterSpacing: "2px",
          }}>
            O TEU PERFIL CARACTR
          </p>
          <h2 style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 800,
            lineHeight: 0.95, letterSpacing: "-0.02em", marginBottom: "32px",
          }}>
            {summary.toUpperCase().replace(".", "")}
          </h2>

          {/* Narrative card */}
          <div style={{
            padding: "28px 32px",
            borderRadius: "16px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            marginBottom: "36px",
            display: "flex", flexDirection: "column", gap: "14px",
          }}>
            {lines.length > 0 ? lines.map((line, i) => (
              <div key={i} style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
                <div style={{
                  width: "4px", height: "4px", borderRadius: "50%",
                  background: "var(--accent)", marginTop: "9px", flexShrink: 0,
                }} />
                <p style={{
                  fontSize: "15px", fontFamily: "var(--font-body)",
                  fontWeight: 300, lineHeight: 1.65, color: "var(--fg)",
                }}>
                  {line}
                </p>
              </div>
            )) : (
              <p style={{ fontSize: "15px", fontFamily: "var(--font-body)", fontWeight: 300, lineHeight: 1.65, color: "var(--muted)" }}>
                Perfil calculado com base nas tuas respostas.
              </p>
            )}
          </div>

          {/* CTA */}
          <button onClick={goToResults} className="pill-btn-solid">
            Ver as tuas recomendações →
          </button>
        </div>
      </main>
    );
  }

  // ── Wizard ──────────────────────────────────────────────────────────────
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "var(--bg)",
        color: "var(--fg)",
      }}
    >
      {/* ── Top bar ── */}
      <div style={{ padding: "32px clamp(24px, 5vw, 64px) 24px" }}>
        <div style={{
          maxWidth: "640px", margin: "0 auto",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: "24px",
        }}>
          <Link
            href="/"
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "14px", fontWeight: 700,
              letterSpacing: "0.12em",
              color: "var(--fg)", textDecoration: "none",
            }}
          >
            CARACTR
          </Link>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)" }}>
            {step + 1}/{totalSteps}
          </span>
        </div>
        {/* Progress bar */}
        <div style={{ maxWidth: "640px", margin: "0 auto", height: "2px", borderRadius: "1px", background: "var(--border)" }}>
          <div style={{
            height: "100%", borderRadius: "1px",
            width: `${progress}%`, background: "var(--accent)",
            transition: "width 0.5s ease-out",
          }} />
        </div>
        <div style={{ maxWidth: "640px", margin: "0 auto", height: "1px", background: "var(--border)", marginTop: "24px" }} />
      </div>

      {/* ── Return visit banner ── */}
      {existingProfileAge !== null && step === 0 && (
        <div style={{ maxWidth: "640px", margin: "0 auto 0", padding: "0 clamp(24px, 5vw, 64px)", width: "100%" }}>
          <div style={{
            padding: "14px 20px",
            borderRadius: "10px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            display: "flex", alignItems: "center",
            justifyContent: "space-between", gap: "16px",
            flexWrap: "wrap",
          }}>
            <p style={{
              fontSize: "13px", color: "var(--muted)",
              fontFamily: "var(--font-body)", lineHeight: 1.5,
            }}>
              {existingProfileAge < 7
                ? `Tens um perfil guardado. Continuar para os teus resultados?`
                : existingProfileAge <= 30
                  ? `O teu perfil tem ${existingProfileAge} dias. Continuar ou refazer?`
                  : `O teu perfil tem ${existingProfileAge} dias — recomendamos refazer o questionário.`
              }
            </p>
            <Link href="/resultados" style={{
              fontFamily: "var(--font-mono)", fontSize: "10px",
              letterSpacing: "1px", color: "var(--accent)",
              textDecoration: "none", whiteSpace: "nowrap",
              textTransform: "uppercase",
            }}>
              Ver resultados →
            </Link>
          </div>
        </div>
      )}

      {/* ── Content area ── */}
      <div style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        padding: "0 clamp(24px, 5vw, 64px) clamp(48px, 6vw, 80px)",
      }}>
        <div style={{
          maxWidth: "640px", width: "100%",
          opacity: transitioning ? 0 : 1,
          transform: transitioning ? "translateY(12px)" : "translateY(0)",
          transition: "opacity 0.25s ease, transform 0.25s ease",
        }}>

          {/* Back button */}
          {step > 0 && (
            <button
              aria-label="Voltar à pergunta anterior"
              onClick={() => goToStep(step - 1)}
              style={{
                marginBottom: "40px", fontSize: "13px",
                color: "var(--muted)", background: "none", border: "none",
                cursor: "pointer", padding: 0,
                fontFamily: "var(--font-body)", fontWeight: 400,
                transition: "color 0.2s ease",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--fg)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--muted)")}
            >
              ← voltar
            </button>
          )}

          {/* ── Questions P1–P6 ── */}
          {current && !isDreamStep && !isBudgetStep && (
            <>
              <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "20px" }} />
              <p style={{
                fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--accent)",
                marginBottom: "16px", textTransform: "uppercase", letterSpacing: "2px",
              }}>
                {current.label}
              </p>
              <h2 style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 800,
                lineHeight: 0.95, letterSpacing: "-0.02em", marginBottom: "40px",
              }}>
                {current.question}
              </h2>

              {/* ── Choice type ── */}
              {current.type === "choice" && (
                <div style={{ borderTop: "1px solid var(--border)" }}>
                  {current.options!.map((opt, idx) => {
                    const selected = answers[current.id] === opt.value;
                    const letter = String.fromCharCode(65 + idx);
                    return (
                      <button
                        key={opt.value}
                        aria-label={opt.label}
                        onClick={() => selectChoice(current.id, opt.value)}
                        style={{
                          display: "flex", alignItems: "flex-start", gap: "20px",
                          width: "100%", textAlign: "left",
                          padding: "clamp(18px, 3vw, 28px) 0",
                          background: "none", border: "none",
                          borderBottom: "1px solid var(--border)",
                          cursor: "pointer", position: "relative",
                        }}
                        onMouseEnter={(e) => {
                          if (!selected) {
                            const label = e.currentTarget.querySelector('[data-label]') as HTMLElement;
                            if (label) label.style.transform = "translateX(8px)";
                            const line = e.currentTarget.querySelector('[data-line]') as HTMLElement;
                            if (line) line.style.width = "24px";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!selected) {
                            const label = e.currentTarget.querySelector('[data-label]') as HTMLElement;
                            if (label) label.style.transform = "translateX(0)";
                            const line = e.currentTarget.querySelector('[data-line]') as HTMLElement;
                            if (line) line.style.width = "0px";
                          }
                        }}
                      >
                        <span style={{
                          fontFamily: "var(--font-mono)", fontSize: "11px",
                          color: selected ? "var(--accent)" : "var(--muted)",
                          letterSpacing: "0.05em", marginTop: "3px",
                          flexShrink: 0, width: "20px", transition: "color 0.2s ease",
                        }}>
                          {letter}
                        </span>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                            <div
                              data-line
                              style={{
                                width: selected ? "24px" : "0px", height: "2px",
                                background: "var(--accent)", borderRadius: "1px",
                                transition: "width 0.3s cubic-bezier(0.16, 1, 0.3, 1)", flexShrink: 0,
                              }}
                            />
                            <span
                              data-label
                              style={{
                                fontFamily: "var(--font-display)",
                                fontSize: "clamp(18px, 2.5vw, 24px)", fontWeight: 700,
                                color: "var(--fg)", letterSpacing: "-0.01em",
                                transition: "transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
                              }}
                            >
                              {opt.label}
                            </span>
                          </div>
                          <p style={{
                            fontSize: "13px", color: "var(--muted)", fontWeight: 300,
                            fontFamily: "var(--font-body)", marginTop: "4px",
                            marginLeft: selected ? "36px" : "0px",
                            transition: "margin-left 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
                          }}>
                            {opt.desc}
                          </p>
                        </div>
                        <div style={{
                          width: "8px", height: "8px", borderRadius: "50%",
                          background: selected ? "var(--accent)" : "transparent",
                          border: selected ? "none" : "1px solid var(--border)",
                          marginTop: "8px", flexShrink: 0, transition: "all 0.2s ease",
                        }} />
                      </button>
                    );
                  })}
                </div>
              )}

              {/* ── Slider type (generic — works for all 4 sliders) ── */}
              {current.type === "slider" && (
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "clamp(16px, 3vw, 32px)", marginBottom: "32px" }}>
                    <span style={{
                      fontFamily: "var(--font-display)",
                      fontSize: "clamp(36px, 5vw, 48px)", fontWeight: 800,
                      color: "var(--accent)", opacity: 0.3, lineHeight: 1, minWidth: "64px",
                    }}>
                      {sliderVal}
                    </span>
                    <input
                      type="range"
                      min={current.min} max={current.max} step={1}
                      value={sliderVal}
                      onChange={(e) =>
                        setAnswers((p) => ({ ...p, [current.id]: Number(e.target.value) }))
                      }
                      className="w-full"
                    />
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "12px", color: "var(--muted)", fontWeight: 300, fontFamily: "var(--font-body)", maxWidth: "45%" }}>
                      {current.leftLabel}
                    </span>
                    <span style={{ fontSize: "12px", color: "var(--muted)", fontWeight: 300, fontFamily: "var(--font-body)", maxWidth: "45%", textAlign: "right" }}>
                      {current.rightLabel}
                    </span>
                  </div>
                  <div style={{ marginTop: "48px" }}>
                    <button onClick={() => {
                      Analytics.stepCompleted(step + 1, current.id, sliderVal);
                      goToStep(step + 1);
                    }} className="pill-btn">
                      continuar
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* ── P7: Dream Car ── */}
          {isDreamStep && (
            <>
              <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "20px" }} />
              <p style={{
                fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--accent)",
                marginBottom: "16px", textTransform: "uppercase", letterSpacing: "2px",
              }}>
                07 — Opcional
              </p>
              <h2 style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 800,
                lineHeight: 0.95, letterSpacing: "-0.02em", marginBottom: "12px",
              }}>
                Se dinheiro não fosse problema?
              </h2>
              <p style={{
                fontSize: "14px", color: "var(--muted)", marginBottom: "36px",
                fontWeight: 300, lineHeight: 1.6, fontFamily: "var(--font-body)",
              }}>
                O carro de sonho diz muito sobre ti. Escolhe um — ou salta este passo.
              </p>

              {loading ? (
                <div style={{
                  padding: "48px 0", fontFamily: "var(--font-mono)",
                  fontSize: "11px", color: "var(--muted)", letterSpacing: "1px",
                }}>
                  A personalizar opções...
                </div>
              ) : (
                <div style={{ borderTop: "1px solid var(--border)" }}>
                  {dreamCars.slice(0, 8).map((car, idx) => {
                    const selected = answers.p7_dream_car === car.id;
                    return (
                      <button
                        key={car.id}
                        aria-label={`Selecionar ${car.display_name || car.id} como carro de sonho`}
                        onClick={() => setAnswers((p) => ({ ...p, p7_dream_car: car.id }))}
                        style={{
                          display: "flex", alignItems: "center", gap: "20px",
                          width: "100%", textAlign: "left",
                          padding: "clamp(14px, 2vw, 20px) 0",
                          background: "none", border: "none",
                          borderBottom: "1px solid var(--border)", cursor: "pointer",
                        }}
                        onMouseEnter={(e) => {
                          if (!selected) {
                            const label = e.currentTarget.querySelector('[data-label]') as HTMLElement;
                            if (label) label.style.transform = "translateX(8px)";
                            const line = e.currentTarget.querySelector('[data-line]') as HTMLElement;
                            if (line) line.style.width = "24px";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!selected) {
                            const label = e.currentTarget.querySelector('[data-label]') as HTMLElement;
                            if (label) label.style.transform = "translateX(0)";
                            const line = e.currentTarget.querySelector('[data-line]') as HTMLElement;
                            if (line) line.style.width = "0px";
                          }
                        }}
                      >
                        <span style={{
                          fontFamily: "var(--font-mono)", fontSize: "10px",
                          color: selected ? "var(--accent)" : "var(--muted)",
                          letterSpacing: "0.05em", flexShrink: 0, width: "20px",
                          transition: "color 0.2s ease",
                        }}>
                          {String(idx + 1).padStart(2, "0")}
                        </span>
                        <div style={{ display: "flex", alignItems: "center", gap: "12px", flex: 1 }}>
                          <div
                            data-line
                            style={{
                              width: selected ? "24px" : "0px", height: "2px",
                              background: "var(--accent)", borderRadius: "1px",
                              transition: "width 0.3s cubic-bezier(0.16, 1, 0.3, 1)", flexShrink: 0,
                            }}
                          />
                          <span
                            data-label
                            style={{
                              fontFamily: "var(--font-display)",
                              fontSize: "clamp(16px, 2vw, 20px)", fontWeight: 700,
                              color: "var(--fg)", letterSpacing: "-0.01em",
                              transition: "transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
                            }}
                          >
                            {car.name}
                          </span>
                        </div>
                        <div style={{
                          width: "8px", height: "8px", borderRadius: "50%",
                          background: selected ? "var(--accent)" : "transparent",
                          border: selected ? "none" : "1px solid var(--border)",
                          flexShrink: 0, transition: "all 0.2s ease",
                        }} />
                      </button>
                    );
                  })}
                </div>
              )}

              <div style={{ display: "flex", gap: "16px", marginTop: "40px", flexWrap: "wrap" }}>
                <button onClick={() => goToStep(step + 1)} className="pill-btn">
                  {answers.p7_dream_car ? "continuar" : "saltar"}
                </button>
              </div>
            </>
          )}

          {/* ── P8: Budget (last step) ── */}
          {isBudgetStep && (
            <>
              <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "20px" }} />
              <p style={{
                fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--accent)",
                marginBottom: "16px", textTransform: "uppercase", letterSpacing: "2px",
              }}>
                08 — Orçamento
              </p>
              <h2 style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 800,
                lineHeight: 0.95, letterSpacing: "-0.02em", marginBottom: "12px",
              }}>
                Quanto queres investir?
              </h2>
              <p style={{
                fontSize: "14px", color: "var(--muted)", marginBottom: "40px",
                fontWeight: 300, lineHeight: 1.6, fontFamily: "var(--font-body)",
              }}>
                O orçamento é o último filtro — não o ponto de partida.
              </p>

              <div style={{ marginBottom: "40px" }}>
                <div style={{
                  display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "16px",
                }}>
                  <span style={{
                    fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)",
                    textTransform: "uppercase", letterSpacing: "2px",
                  }}>mínimo</span>
                  <span style={{
                    fontFamily: "var(--font-display)",
                    fontSize: "clamp(28px, 4vw, 40px)", fontWeight: 700, color: "var(--accent)",
                  }}>
                    {(answers.p8_budget_min || 10000).toLocaleString("pt-PT")}€
                  </span>
                </div>
                <input
                  aria-label="Orçamento mínimo"
                  type="range" min={3000} max={60000} step={1000}
                  value={answers.p8_budget_min || 10000}
                  onChange={(e) => setAnswers((p) => ({ ...p, p8_budget_min: Number(e.target.value) }))}
                  className="w-full"
                />
              </div>

              <div style={{ marginBottom: "48px" }}>
                <div style={{
                  display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "16px",
                }}>
                  <span style={{
                    fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)",
                    textTransform: "uppercase", letterSpacing: "2px",
                  }}>máximo</span>
                  <span style={{
                    fontFamily: "var(--font-display)",
                    fontSize: "clamp(28px, 4vw, 40px)", fontWeight: 700, color: "var(--accent)",
                  }}>
                    {(answers.p8_budget_max || 25000).toLocaleString("pt-PT")}€
                  </span>
                </div>
                <input
                  aria-label="Orçamento máximo"
                  type="range" min={5000} max={80000} step={1000}
                  value={answers.p8_budget_max || 25000}
                  onChange={(e) => setAnswers((p) => ({ ...p, p8_budget_max: Number(e.target.value) }))}
                  className="w-full"
                />
              </div>

              <button
                aria-label="Ver as minhas recomendações"
                onClick={submit}
                disabled={submitting}
                className="pill-btn-solid"
                style={{ opacity: submitting ? 0.5 : 1, cursor: submitting ? "wait" : "pointer" }}
              >
                {submitting ? "a analisar..." : "ver resultados"}
              </button>
              {submitError && (
                <p style={{
                  marginTop: "16px", fontSize: "13px",
                  color: "#d23c3c", fontFamily: "var(--font-body)", lineHeight: 1.5,
                }}>
                  {submitError}
                </p>
              )}
            </>
          )}

        </div>
      </div>
    </main>
  );
}
