"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Analytics } from "@/lib/analytics";
import { TrustPanel } from "@/app/components/TrustPanel";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TIER_STYLE: Record<string, { bg: string; color: string; label: string; desc: string }> = {
  forte:    { bg: "rgba(74,163,90,0.10)",   color: "#4aa35a", label: "NEGÓCIO FORTE",  desc: "Preço abaixo do mercado, bom estado geral." },
  razoavel: { bg: "rgba(200,168,130,0.10)", color: "var(--accent)", label: "RAZOÁVEL", desc: "Preço justo, sem red flags evidentes." },
  cuidado:  { bg: "rgba(220,160,40,0.10)",  color: "#dca028", label: "ATENÇÃO",        desc: "Alguns pontos a investigar antes de decidir." },
  evitar:   { bg: "rgba(210,60,60,0.10)",   color: "#d23c3c", label: "EVITAR",         desc: "Preço elevado ou riscos identificados." },
};

const FIT_STYLE: Record<string, { bg: string; color: string }> = {
  excelente: { bg: "rgba(74,163,90,0.10)",   color: "#4aa35a" },
  bom:       { bg: "rgba(200,168,130,0.10)", color: "var(--accent)" },
  parcial:   { bg: "rgba(220,160,40,0.10)",  color: "#dca028" },
  fraco:     { bg: "rgba(210,60,60,0.10)",   color: "#d23c3c" },
};

const VERDICT_EMOTION: Record<string, string> = {
  forte:    "Este tipo de negócio não dura muito.",
  razoavel: "Um negócio justo — avança com confiança.",
  cuidado:  "Há melhores opções no mercado neste momento.",
  evitar:   "Não vale o risco. Continua a procurar.",
};

// Quick profile dims for the inline 3-question form
const QUICK_DIMS = [
  { value: "reliability", label: "Fiabilidade" },
  { value: "comfort",     label: "Conforto" },
  { value: "driving",     label: "Condução" },
  { value: "economy",     label: "Economia" },
];
const QUICK_AVERSIONS = [
  { value: "fiabilidade", label: "Pouca fiabilidade" },
  { value: "conforto",    label: "Pouco conforto" },
  { value: "espaco",      label: "Pouco espaço" },
  { value: "potencia",    label: "Pouca potência" },
];
const QUICK_BUDGETS = [
  { value: "10000", label: "€10k" },
  { value: "15000", label: "€15k" },
  { value: "20000", label: "€20k" },
  { value: "30000", label: "€30k" },
  { value: "40000", label: "€40k+" },
];

const CHECKS = [
  { label: "PREÇO VS. MERCADO", desc: "Comparamos com anúncios reais da mesma marca e modelo." },
  { label: "KM / ANO", desc: "Calculamos se o desgaste é compatível com o ano de matrícula." },
  { label: "VENDEDOR", desc: "Particular ou dealer — cada um tem padrões diferentes." },
  { label: "EXTRAS", desc: "Identificamos equipamentos relevantes que afetam o valor." },
];

const inputStyle: React.CSSProperties = {
  flex: 1,
  padding: "16px 20px",
  borderRadius: "10px",
  border: "1px solid var(--border)",
  background: "var(--surface)",
  color: "var(--fg)",
  fontSize: "14px",
  fontWeight: 300,
  fontFamily: "var(--font-body)",
  outline: "none",
  transition: "border-color 0.2s ease",
  minWidth: 0,
};

/* ── Loading dots ────────────────────────────────────────────────────────── */
const LOADING_STEPS = [
  "A recolher dados do anúncio",
  "A consultar referências de mercado",
  "A calcular km/ano e desgaste",
  "A compor a análise",
];

function LoadingState() {
  const [step, setStep] = useState(0);
  const [dots, setDots] = useState("");

  useEffect(() => {
    const dotsInterval = setInterval(() => {
      setDots((d) => (d.length >= 3 ? "" : d + "."));
    }, 400);
    const stepInterval = setInterval(() => {
      setStep((s) => (s < LOADING_STEPS.length - 1 ? s + 1 : s));
    }, 2200);
    return () => { clearInterval(dotsInterval); clearInterval(stepInterval); };
  }, []);

  return (
    <div style={{ marginTop: "56px", padding: "40px 0" }}>
      <div style={{ width: "32px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "28px" }} />
      <p style={{
        fontFamily: "var(--font-mono)", fontSize: "11px", letterSpacing: "2px",
        color: "var(--accent)", textTransform: "uppercase", marginBottom: "24px",
      }}>
        {LOADING_STEPS[step]}{dots}
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {LOADING_STEPS.map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{
              width: "6px", height: "6px", borderRadius: "50%",
              background: i < step ? "var(--accent)" : i === step ? "var(--accent)" : "var(--border)",
              opacity: i <= step ? 1 : 0.3,
              transition: "all 0.3s ease",
              flexShrink: 0,
            }} />
            <p style={{
              fontFamily: "var(--font-body)", fontSize: "13px",
              color: i <= step ? "var(--fg)" : "var(--muted)",
              opacity: i <= step ? (i === step ? 1 : 0.5) : 0.25,
              transition: "all 0.3s ease",
            }}>
              {s}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Share button ───────────────────────────────────────────────────────── */
function ShareButton({ result, listingUrl }: { result: any; listingUrl: string }) {
  const [shared, setShared] = useState(false);

  const handleShare = async () => {
    const tier  = result?.deal?.tier || result?.analysis?.verdict || "";
    const brand = result?.listing?.brand_name || "";
    const model = result?.listing?.model_name || "";
    const year  = result?.listing?.year ? ` ${result.listing.year}` : "";
    const delta = result?.deal?.price_delta_pct;
    const dir   = (result?.deal?.price_delta || 0) >= 0 ? "abaixo" : "acima";

    const TIER_LABELS: Record<string, string> = {
      forte: "NEGÓCIO FORTE", razoavel: "RAZOÁVEL", cuidado: "ATENÇÃO", evitar: "EVITAR",
    };
    const verdictLabel = TIER_LABELS[tier] || tier.toUpperCase();

    let text = `Analisei um ${[brand, model, year].filter(Boolean).join(" ").trim() || "carro"} no Caractr — ${verdictLabel}`;
    if (delta != null) text += `, ${Math.abs(delta)}% ${dir} do mercado`;
    text += `. Experimenta: caractr.pt/analisar`;

    Analytics.analysisShared("", listingUrl, "whatsapp");
    setShared(true);
    setTimeout(() => setShared(false), 2000);

    if (navigator.share) {
      try { await navigator.share({ text }); return; } catch {}
    }
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank");
  };

  return (
    <button
      onClick={handleShare}
      style={{
        display: "flex", alignItems: "center", gap: "6px",
        background: "none", border: "1px solid var(--border)",
        borderRadius: "100px", cursor: "pointer",
        padding: "6px 14px",
        fontFamily: "var(--font-mono)", fontSize: "9px",
        letterSpacing: "1px", textTransform: "uppercase",
        color: shared ? "var(--accent)" : "var(--muted)",
        transition: "all 0.15s ease",
        flexShrink: 0,
      }}
    >
      {shared ? "✓ Partilhado" : "↗ Partilhar"}
    </button>
  );
}

/* ── Micro-feedback ──────────────────────────────────────────────────────── */
const FEEDBACK_REASONS = [
  "Preço parece errado",
  "Informação incompleta",
  "Não concordo com veredicto",
];

function AnalysisMicroFeedback({ listingUrl }: { listingUrl: string }) {
  const [vote, setVote] = useState<"up" | "down" | null>(null);

  const handleVote = (v: "up" | "down") => {
    setVote(v);
    Analytics.analysisFeedback("", listingUrl, v === "up");
  };

  const handleReason = (reason: string) => {
    Analytics.analysisFeedback("", listingUrl, false, reason);
  };

  if (vote === "up") {
    return (
      <p style={{ marginTop: "12px", fontSize: "11px", color: "var(--muted)", fontFamily: "var(--font-body)", opacity: 0.5 }}>
        Obrigado pelo feedback.
      </p>
    );
  }

  return (
    <div style={{ marginTop: "16px" }}>
      {vote === null && (
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <p style={{ fontSize: "11px", color: "var(--muted)", fontFamily: "var(--font-body)", opacity: 0.55 }}>
            Esta análise foi útil?
          </p>
          {(["up", "down"] as const).map((v) => (
            <button
              key={v}
              aria-label={v === "up" ? "Análise útil" : "Análise não útil"}
              onClick={() => handleVote(v)}
              style={{
                background: "none", border: "none", cursor: "pointer",
                fontSize: "14px", padding: "2px 4px", opacity: 0.5,
                transition: "opacity 0.15s ease",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.5")}
            >
              {v === "up" ? "👍" : "👎"}
            </button>
          ))}
        </div>
      )}
      {vote === "down" && (
        <div>
          <p style={{ fontSize: "11px", color: "var(--muted)", fontFamily: "var(--font-body)", opacity: 0.55, marginBottom: "8px" }}>
            O que correu mal?
          </p>
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {FEEDBACK_REASONS.map((r) => (
              <button
                key={r}
                onClick={() => handleReason(r)}
                style={{
                  padding: "5px 12px", borderRadius: "100px",
                  border: "1px solid var(--border)", background: "transparent",
                  color: "var(--muted)", fontSize: "11px",
                  fontFamily: "var(--font-body)", cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent)"; e.currentTarget.style.color = "var(--accent)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--muted)"; }}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Result display ──────────────────────────────────────────────────────── */
function AnalysisResult({ result, listingUrl, onReset }: { result: any; listingUrl: string; onReset: () => void }) {
  const tier = result?.deal?.tier || result?.analysis?.verdict;
  const ts = tier ? TIER_STYLE[tier] : null;
  const fit = result?.fit || null;
  const fs = fit?.fit_tier ? FIT_STYLE[fit.fit_tier] : null;
  const listing = result?.listing || {};
  const deal = result?.deal || {};
  const analysis = result?.analysis || {};

  // Fire dual verdict event once on mount when both verdict and fit are present
  useEffect(() => {
    if (tier && fit?.fit_tier) {
      Analytics.dualVerdictShown("", tier, fit.fit_tier);
    }
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ marginTop: "48px" }}>

      {/* ── Verdict block ── */}
      <div style={{
        padding: "28px 28px 24px",
        borderRadius: "16px",
        border: `1px solid ${ts ? ts.color + "40" : "var(--border)"}`,
        background: ts ? ts.bg : "var(--surface)",
        marginBottom: "20px",
      }}>
        {/* Source label */}
        {result.source_label && (
          <div style={{ marginBottom: "12px" }}>
            <span style={{
              fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px",
              color: "var(--muted)", border: "1px solid var(--border)",
              padding: "3px 10px", borderRadius: "100px", textTransform: "uppercase", opacity: 0.6,
            }}>
              {result.source_label}
            </span>
          </div>
        )}

        {/* Verdict pills — dual when fit present, single otherwise */}
        <div style={{ display: "flex", gap: "12px", marginBottom: "10px", flexWrap: "wrap", alignItems: "flex-start" }}>
          {ts && (
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              {fit && (
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "8px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase" }}>
                  Negócio
                </p>
              )}
              <span style={{
                fontFamily: "var(--font-mono)", fontSize: "11px", letterSpacing: "1.5px",
                color: ts.color, fontWeight: 700, textTransform: "uppercase",
              }}>
                ● {ts.label}
              </span>
            </div>
          )}
          {fit && fs && (
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "8px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase" }}>
                Para ti
              </p>
              <span style={{
                fontFamily: "var(--font-mono)", fontSize: "11px", letterSpacing: "1.5px",
                color: fs.color, fontWeight: 700, textTransform: "uppercase",
              }}>
                ● {fit.fit_label || fit.fit_tier.toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {/* Emotional anchoring line */}
        {tier && VERDICT_EMOTION[tier] && (
          <p style={{
            fontSize: "12px", fontFamily: "var(--font-body)", fontWeight: 300,
            color: "var(--muted)", opacity: 0.7, marginBottom: "14px", lineHeight: 1.5,
          }}>
            {VERDICT_EMOTION[tier]}
            {fit?.fit_reason && tier !== fit.fit_tier && (
              <span style={{ marginLeft: "8px", opacity: 0.8 }}>· {fit.fit_reason}</span>
            )}
          </p>
        )}


        {(listing.brand_name || listing.model_name) && (
          <p style={{
            fontFamily: "var(--font-display)", fontSize: "clamp(22px, 4vw, 32px)",
            fontWeight: 800, letterSpacing: "-0.02em", lineHeight: 1, marginBottom: "10px",
          }}>
            {[listing.brand_name, listing.model_name].filter(Boolean).join(" ").toUpperCase()}
          </p>
        )}

        <p style={{
          fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)",
          letterSpacing: "0.5px", marginBottom: "16px",
        }}>
          {[
            listing.year,
            listing.km ? `${listing.km.toLocaleString("pt-PT")} km` : null,
            listing.price ? `${listing.price.toLocaleString("pt-PT")} €` : null,
            listing.seller_type,
          ].filter(Boolean).join("  ·  ")}
        </p>

        {analysis.verdict_reason && (
          <p style={{
            fontSize: "14px", fontFamily: "var(--font-body)",
            color: "var(--fg)", lineHeight: 1.6, fontWeight: 400,
          }}>
            {analysis.verdict_reason}
          </p>
        )}
      </div>

      {/* ── Metrics row ── */}
      {(deal.price_delta_pct != null || deal.km_per_year != null || deal.market_avg_price != null || analysis.spec_tier) && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
          gap: "1px",
          background: "var(--border)",
          borderRadius: "12px",
          overflow: "hidden",
          marginBottom: "20px",
          border: "1px solid var(--border)",
        }}>
          {deal.price_delta_pct != null && (
            <div style={{ background: "var(--surface)", padding: "16px 18px" }}>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px" }}>
                vs. Mercado
              </p>
              <p style={{
                fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700,
                color: (deal.price_delta || 0) >= 0 ? "#4aa35a" : "#d23c3c",
                lineHeight: 1,
              }}>
                {(deal.price_delta || 0) >= 0 ? "−" : "+"}{Math.abs(deal.price_delta_pct)}%
              </p>
            </div>
          )}
          {deal.market_avg_price != null && (
            <div style={{ background: "var(--surface)", padding: "16px 18px" }}>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px" }}>
                Média mercado{deal.market_sample_count ? ` (${deal.market_sample_count})` : ""}
              </p>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700, color: "var(--fg)", lineHeight: 1 }}>
                {Math.round(deal.market_avg_price).toLocaleString("pt-PT")} €
              </p>
            </div>
          )}
          {deal.km_per_year != null && (
            <div style={{ background: "var(--surface)", padding: "16px 18px" }}>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px" }}>
                Km / ano
              </p>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700, color: "var(--fg)", lineHeight: 1 }}>
                {Math.round(deal.km_per_year).toLocaleString("pt-PT")}
              </p>
            </div>
          )}
          {analysis.spec_tier && (
            <div style={{ background: "var(--surface)", padding: "16px 18px" }}>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px" }}>
                Versão
              </p>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700, color: "var(--fg)", lineHeight: 1 }}>
                {(analysis.trim_level || analysis.spec_tier).toUpperCase()}
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── Flags ── */}
      {((analysis.green_flags?.length > 0) || (analysis.red_flags?.length > 0)) && (
        <div style={{
          padding: "20px 20px",
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "var(--surface)",
          marginBottom: "20px",
          display: "flex", flexDirection: "column", gap: "10px",
        }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "4px" }}>
            Pontos de análise
          </p>
          {(analysis.green_flags || []).map((f: string, i: number) => (
            <div key={`g${i}`} style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
              <span style={{ color: "#4aa35a", fontSize: "12px", marginTop: "2px", flexShrink: 0, fontWeight: 700 }}>✓</span>
              <span style={{ fontSize: "13px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.5 }}>{f}</span>
            </div>
          ))}
          {(analysis.red_flags || []).map((f: string, i: number) => (
            <div key={`r${i}`} style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
              <span style={{ color: "#d23c3c", fontSize: "12px", marginTop: "2px", flexShrink: 0, fontWeight: 700 }}>⚠</span>
              <span style={{ fontSize: "13px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.5 }}>{f}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Key extras ── */}
      {analysis.key_extras?.length > 0 && (
        <div style={{ marginBottom: "20px" }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "12px" }}>
            Extras detectados
          </p>
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {analysis.key_extras.map((e: string, i: number) => (
              <span key={i} style={{
                fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "0.5px",
                color: "var(--muted)", border: "1px solid var(--border)",
                padding: "5px 14px", borderRadius: "100px",
              }}>{e}</span>
            ))}
          </div>
        </div>
      )}

      {/* ── Seller analysis ── */}
      {analysis.seller_analysis && (
        <div style={{
          padding: "16px 20px", borderRadius: "12px",
          border: "1px solid var(--border)",
          marginBottom: "20px",
        }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px" }}>
            Análise do vendedor
          </p>
          <p style={{ fontSize: "13px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.6 }}>
            {analysis.seller_analysis}
          </p>
        </div>
      )}

      {/* ── Verdict narrative (LLM) ── */}
      {analysis.verdict_narrative && (
        <div style={{
          padding: "20px 24px", borderRadius: "12px",
          border: "1px solid var(--border)", background: "var(--surface)",
          marginBottom: "20px",
        }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--accent)", textTransform: "uppercase", marginBottom: "10px" }}>
            Veredicto
          </p>
          <p style={{ fontSize: "14px", color: "var(--fg)", fontFamily: "var(--font-body)", lineHeight: 1.7, fontWeight: 300 }}>
            {analysis.verdict_narrative}
          </p>
        </div>
      )}

      {/* ── Extras analysis (LLM) ── */}
      {analysis.extras_analysis && (
        <div style={{
          padding: "16px 20px", borderRadius: "12px",
          border: "1px solid var(--border)",
          marginBottom: "20px",
        }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px" }}>
            Equipamento & valor
          </p>
          <p style={{ fontSize: "13px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.6 }}>
            {analysis.extras_analysis}
          </p>
        </div>
      )}

      {/* ── Seller read (LLM) ── */}
      {analysis.seller_read && (
        <div style={{
          padding: "16px 20px", borderRadius: "12px",
          border: "1px solid var(--border)",
          marginBottom: "20px",
        }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px" }}>
            Leitura do vendedor
          </p>
          <p style={{ fontSize: "13px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.6 }}>
            {analysis.seller_read}
          </p>
        </div>
      )}

      {/* ── Inspection checklist ── */}
      {result.inspection_checklist?.length > 0 && (
        <div style={{
          padding: "20px 20px", borderRadius: "12px",
          border: "1px solid var(--border)", background: "var(--surface)",
          marginBottom: "20px",
        }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "14px" }}>
            O que verificar
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {result.inspection_checklist.map((item: string, i: number) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--accent)", marginTop: "2px", flexShrink: 0 }}>{String(i + 1).padStart(2, "0")}</span>
                <span style={{ fontSize: "13px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.5 }}>{item}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Negotiation tips ── */}
      {(result.negotiation_tips?.length > 0 || analysis.negotiation_script) && (
        <div style={{
          padding: "20px 20px", borderRadius: "12px",
          border: "1px solid var(--border)",
          marginBottom: "20px",
        }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "14px" }}>
            Como negociar
          </p>
          {analysis.negotiation_script && (
            <p style={{ fontSize: "13px", color: "var(--fg)", fontFamily: "var(--font-body)", lineHeight: 1.6, marginBottom: result.negotiation_tips?.length > 0 ? "14px" : "0" }}>
              {analysis.negotiation_script}
            </p>
          )}
          {result.negotiation_tips?.length > 0 && !analysis.negotiation_script && (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {result.negotiation_tips.map((tip: string, i: number) => (
                <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
                  <span style={{ color: "var(--accent)", fontSize: "12px", marginTop: "2px", flexShrink: 0 }}>→</span>
                  <span style={{ fontSize: "13px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.5 }}>{tip}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Maintenance estimate ── */}
      {result.maintenance_estimate && (
        <div style={{
          padding: "14px 20px", borderRadius: "12px",
          border: "1px solid var(--border)",
          marginBottom: "20px",
          display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px",
        }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase" }}>
            Manutenção estimada / ano
          </p>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "16px", fontWeight: 700, color: "var(--fg)" }}>
            ~{Math.round(result.maintenance_estimate).toLocaleString("pt-PT")} €
          </p>
        </div>
      )}

      {/* ── Trust Panel ── */}
      <TrustPanel
        reliability={result.reliability}
        modelName={result.listing ? `${result.listing.brand_name || ""} ${result.listing.model_name || ""}`.trim() : undefined}
      />

      {/* ── Share + Micro-feedback ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px", marginTop: "16px" }}>
        <AnalysisMicroFeedback listingUrl={listingUrl} />
        <ShareButton result={result} listingUrl={listingUrl} />
      </div>

      {/* ── Caveat ── */}
      {result.caveat && (
        <p style={{
          fontSize: "11px", color: "var(--muted)", fontFamily: "var(--font-body)",
          opacity: 0.35, lineHeight: 1.5,
          borderTop: "1px solid var(--border)", paddingTop: "16px",
          marginBottom: "48px",
        }}>
          {result.caveat}
        </p>
      )}

      {/* ── Wizard bridge ── */}
      <div style={{
        padding: "36px 32px",
        borderRadius: "16px",
        background: "var(--fg)",
        marginBottom: "24px",
      }}>
        <div style={{ width: "32px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "20px" }} />
        <h2 style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(22px, 3.5vw, 32px)",
          fontWeight: 800, letterSpacing: "-0.02em",
          color: "var(--bg)",
          lineHeight: 1, marginBottom: "12px",
        }}>
          QUERES A SHORTLIST CERTA?
        </h2>
        <p style={{
          fontSize: "14px", color: "var(--bg)", opacity: 0.6,
          fontFamily: "var(--font-body)", lineHeight: 1.7,
          fontWeight: 300, marginBottom: "24px",
          maxWidth: "400px",
        }}>
          Responde a algumas perguntas sobre o teu estilo de vida. Encontramos os modelos que se adequam a ti — com análise detalhada de cada opção.
        </p>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <Link href="/escolher" className="pill-btn-inv">
            descobrir o meu carro
          </Link>
          <Link
            href={listingUrl
              ? `/concierge?listing_url=${encodeURIComponent(listingUrl)}${tier ? `&listing_verdict=${tier}` : ""}`
              : "/concierge"
            }
            style={{
              padding: "12px 24px", borderRadius: "100px",
              border: "1px solid rgba(255,255,255,0.2)",
              color: "rgba(255,255,255,0.7)", fontSize: "13px",
              fontFamily: "var(--font-body)", fontWeight: 500,
              textDecoration: "none", transition: "all 0.15s ease",
              whiteSpace: "nowrap",
            }}
          >
            quero ajuda pessoal
          </Link>
        </div>
      </div>

      {/* Analyse another */}
      <button
        onClick={onReset}
        style={{
          background: "none", border: "none", cursor: "pointer",
          fontFamily: "var(--font-mono)", fontSize: "10px",
          letterSpacing: "1.5px", textTransform: "uppercase",
          color: "var(--muted)", padding: 0, opacity: 0.45,
        }}
      >
        ↩ Analisar outro anúncio
      </button>
    </div>
  );
}

/* ── Quick Profile component ─────────────────────────────────────────────── */
function QuickProfile({ onComplete }: { onComplete: (profile: Record<string, number>) => void }) {
  const [topDim,   setTopDim]   = useState("");
  const [aversion, setAversion] = useState("");
  const [budget,   setBudget]   = useState("");

  const canComplete = topDim && aversion && budget;

  const buildQuickProfile = () => {
    const profile: Record<string, number> = {
      economy: 0.09, comfort: 0.09, driving: 0.09,
      practical: 0.09, status: 0.09, reliability: 0.09,
    };
    // Top dim gets 0.35, add 0.20 to second best based on aversion context
    profile[topDim] = 0.35;
    // Secondary boost — pick from remaining dims
    const secondDimMap: Record<string, string> = {
      reliability: "economy", economy: "reliability",
      comfort: "practical", practical: "comfort",
      driving: "comfort", status: "driving",
    };
    const second = secondDimMap[topDim] || "comfort";
    profile[second] = 0.20;
    // Normalize
    const total = Object.values(profile).reduce((a, b) => a + b, 0);
    Object.keys(profile).forEach(k => { profile[k] = Math.round(profile[k] / total * 10000) / 10000; });
    localStorage.setItem("caractr_quick_profile", JSON.stringify({ profile, topDim, aversion, budget }));
    Analytics.quickProfileCompleted("", topDim, aversion, budget);
    onComplete(profile);
  };

  const chipStyle = (selected: boolean): React.CSSProperties => ({
    padding: "8px 16px", borderRadius: "100px", cursor: "pointer",
    fontFamily: "var(--font-body)", fontSize: "13px",
    border: `1px solid ${selected ? "var(--accent)" : "var(--border)"}`,
    background: selected ? "rgba(200,168,130,0.1)" : "transparent",
    color: selected ? "var(--accent)" : "var(--muted)",
    transition: "all 0.15s ease",
  });

  return (
    <div style={{
      marginTop: "32px", padding: "28px",
      borderRadius: "16px", border: "1px solid var(--border)",
      background: "var(--surface)",
    }}>
      <div style={{ width: "32px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "16px" }} />
      <p style={{ fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "2px", color: "var(--accent)", textTransform: "uppercase", marginBottom: "8px" }}>
        Para ti
      </p>
      <p style={{ fontSize: "15px", fontFamily: "var(--font-display)", fontWeight: 700, marginBottom: "20px", lineHeight: 1.2 }}>
        Este carro é bom negócio.<br />Mas é bom <em>para ti</em>?
      </p>

      <div style={{ marginBottom: "20px" }}>
        <p style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", marginBottom: "10px" }}>O que mais importa?</p>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {QUICK_DIMS.map(d => (
            <button key={d.value} onClick={() => setTopDim(d.value)} style={chipStyle(topDim === d.value)}>{d.label}</button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: "20px" }}>
        <p style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", marginBottom: "10px" }}>O que é inaceitável?</p>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {QUICK_AVERSIONS.map(a => (
            <button key={a.value} onClick={() => setAversion(a.value)} style={chipStyle(aversion === a.value)}>{a.label}</button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: "24px" }}>
        <p style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", marginBottom: "10px" }}>Orçamento máximo?</p>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {QUICK_BUDGETS.map(b => (
            <button key={b.value} onClick={() => setBudget(b.value)} style={chipStyle(budget === b.value)}>{b.label}</button>
          ))}
        </div>
      </div>

      <button
        onClick={buildQuickProfile}
        disabled={!canComplete}
        style={{
          padding: "10px 24px", borderRadius: "100px",
          border: "1px solid var(--accent)",
          background: canComplete ? "var(--accent)" : "transparent",
          color: canComplete ? "var(--bg)" : "var(--accent)",
          fontSize: "13px", fontWeight: 600, fontFamily: "var(--font-body)",
          cursor: canComplete ? "pointer" : "not-allowed",
          opacity: canComplete ? 1 : 0.4,
          transition: "all 0.2s ease",
        }}
      >
        Ver o meu veredicto pessoal
      </button>
    </div>
  );
}


/* ── Main page ───────────────────────────────────────────────────────────── */
function AnalisarContent() {
  const searchParams = useSearchParams();
  const [url,          setUrl]          = useState(searchParams.get("url") || "");
  const [loading,      setLoading]      = useState(false);
  const [result,       setResult]       = useState<any>(null);
  const [error,        setError]        = useState("");
  const [userProfile,  setUserProfile]  = useState<Record<string,number> | null>(null);
  const [showQuick,    setShowQuick]    = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load profile from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("caractr_results");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.profile) setUserProfile(parsed.profile);
      } catch {}
    }
    // Also check quick profile
    const quick = localStorage.getItem("caractr_quick_profile");
    if (quick) {
      try {
        const parsed = JSON.parse(quick);
        if (parsed.profile && !userProfile) setUserProfile(parsed.profile);
      } catch {}
    }
  }, []);

  useEffect(() => {
    const preUrl = searchParams.get("url");
    if (preUrl && preUrl.startsWith("http")) {
      setUrl(preUrl);
      triggerAnalysis(preUrl);
    }
  }, []);

  const triggerAnalysis = async (targetUrl: string, profileOverride?: Record<string,number>) => {
    if (!targetUrl.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    const profile = profileOverride || userProfile;
    try {
      const res = await fetch(`${API}/api/listings/analyse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          listing_url: targetUrl.trim(),
          user_profile: profile || undefined,
        }),
      });
      const data = await res.json();
      if (data.error) setError(data.error);
      else setResult(data);
    } catch {
      setError("Erro ao analisar. Verifica a ligação e tenta novamente.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickProfileComplete = (profile: Record<string, number>) => {
    setUserProfile(profile);
    setShowQuick(false);
    if (url.trim() && result) {
      // Re-analyse with the new profile
      triggerAnalysis(url, profile);
    }
  };

  const handleReset = () => {
    setResult(null);
    setUrl("");
    setError("");
    setShowQuick(false);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  return (
    <main style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--fg)" }}>

      {/* ── Header ── */}
      <div style={{
        padding: "28px clamp(24px, 5vw, 64px)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        borderBottom: "1px solid var(--border)",
      }}>
        <Link href="/" style={{
          fontFamily: "var(--font-display)", fontSize: "14px",
          fontWeight: 700, letterSpacing: "0.12em",
          color: "var(--fg)", textDecoration: "none",
        }}>
          CARACTR
        </Link>
        <Link href="/escolher" className="pill-btn-ghost" style={{ padding: "8px 20px", fontSize: "13px" }}>
          descobrir o meu carro →
        </Link>
      </div>

      <div style={{ maxWidth: "680px", margin: "0 auto", padding: "clamp(48px, 6vw, 72px) clamp(24px, 5vw, 32px)" }}>

        {/* ── Intro ── */}
        <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "20px" }} />
        <h1 style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(36px, 6vw, 64px)",
          fontWeight: 800, letterSpacing: "-0.03em",
          lineHeight: 0.92, marginBottom: "20px",
        }}>
          ANALISAR<br />ANÚNCIO
        </h1>
        <p style={{
          fontSize: "15px", color: "var(--muted)",
          lineHeight: 1.7, fontWeight: 300, fontFamily: "var(--font-body)",
          maxWidth: "460px", marginBottom: "40px",
        }}>
          Cola o link de qualquer anúncio — Standvirtual, OLX ou qualquer dealer.
          Dizemos-te se o preço é justo, o que preocupa e o que valoriza.
        </p>

        {/* ── What we check ── */}
        {!result && !loading && (
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: "1px", background: "var(--border)", borderRadius: "12px",
            overflow: "hidden", border: "1px solid var(--border)", marginBottom: "36px",
          }}>
            {CHECKS.map((c) => (
              <div key={c.label} style={{ background: "var(--surface)", padding: "16px 16px" }}>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--accent)", textTransform: "uppercase", marginBottom: "6px" }}>
                  {c.label}
                </p>
                <p style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.5 }}>
                  {c.desc}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* ── URL input ── */}
        <div style={{ display: "flex", gap: "10px", marginBottom: "12px", flexWrap: "wrap" }}>
          <input
            ref={inputRef}
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && triggerAnalysis(url)}
            placeholder="https://www.standvirtual.com/...  ·  olx.pt/..."
            style={inputStyle}
            onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
            onBlur={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
            disabled={loading}
          />
          <button
            onClick={() => triggerAnalysis(url)}
            disabled={loading || !url.trim()}
            style={{
              padding: "14px 28px",
              borderRadius: "10px",
              border: "1px solid var(--accent)",
              background: loading ? "transparent" : "var(--accent)",
              color: loading ? "var(--accent)" : "var(--bg)",
              fontSize: "13px", fontWeight: 600,
              fontFamily: "var(--font-body)",
              cursor: (loading || !url.trim()) ? "not-allowed" : "pointer",
              whiteSpace: "nowrap",
              transition: "all 0.2s ease",
              opacity: (!url.trim() && !loading) ? 0.35 : 1,
              flexShrink: 0,
            }}
          >
            {loading ? "A analisar..." : "Analisar"}
          </button>
        </div>
        <p style={{
          fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px",
          color: "var(--muted)", textTransform: "uppercase", opacity: 0.35,
        }}>
          Standvirtual · OLX · Autosapo · Autoscout24 · Qualquer dealer
        </p>

        {/* ── Error ── */}
        {error && !loading && (
          <div style={{
            marginTop: "20px", padding: "20px 24px",
            borderRadius: "12px",
            border: "1px solid rgba(210,60,60,0.25)",
            background: "rgba(210,60,60,0.05)",
          }}>
            <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "#d23c3c", textTransform: "uppercase", marginBottom: "8px" }}>
              {error.toLowerCase().includes("aceder") || error.toLowerCase().includes("anúncio")
                ? "Anúncio inacessível"
                : error.toLowerCase().includes("modelo")
                ? "Modelo não registado"
                : error.toLowerCase().includes("dados")
                ? "Dados de mercado limitados"
                : "Erro na análise"}
            </p>
            <p style={{ fontSize: "13px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.6 }}>
              {error}
            </p>
            {(error.toLowerCase().includes("aceder") || error.toLowerCase().includes("anúncio")) && (
              <p style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", marginTop: "8px", opacity: 0.6 }}>
                Tenta outro URL ou verifica se o anúncio ainda está publicado.
              </p>
            )}
          </div>
        )}

        {/* ── Loading ── */}
        {loading && <LoadingState />}

        {/* ── Result ── */}
        {result && !loading && (
          <>
            <AnalysisResult result={result} listingUrl={url} onReset={handleReset} />

            {/* Quick Profile — shown when no wizard profile */}
            {!userProfile && (
              showQuick
                ? <QuickProfile onComplete={handleQuickProfileComplete} />
                : (
                  <div style={{
                    marginTop: "12px", marginBottom: "12px",
                    padding: "16px 20px", borderRadius: "12px",
                    border: "1px solid var(--border)",
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    flexWrap: "wrap", gap: "12px",
                  }}>
                    <p style={{
                      fontSize: "13px", fontFamily: "var(--font-body)",
                      color: "var(--muted)", fontWeight: 300,
                    }}>
                      Queres saber se este carro é mesmo para ti?
                    </p>
                    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                      <button
                        onClick={() => setShowQuick(true)}
                        style={{
                          padding: "7px 18px", borderRadius: "100px",
                          border: "1px solid var(--accent)",
                          background: "transparent", color: "var(--accent)",
                          fontSize: "12px", fontWeight: 500,
                          fontFamily: "var(--font-body)", cursor: "pointer",
                        }}
                      >
                        Resposta rápida
                      </button>
                      <Link href="/escolher" style={{
                        padding: "7px 18px", borderRadius: "100px",
                        border: "1px solid var(--border)",
                        color: "var(--muted)", fontSize: "12px",
                        fontFamily: "var(--font-body)", fontWeight: 400,
                        textDecoration: "none",
                        whiteSpace: "nowrap",
                      }}>
                        Perfil completo →
                      </Link>
                    </div>
                  </div>
                )
            )}
          </>
        )}

        {/* ── Pre-analysis wizard bridge ── */}
        {!result && !loading && (
          <div style={{
            marginTop: "72px", paddingTop: "40px",
            borderTop: "1px solid var(--border)",
          }}>
            <p style={{
              fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "2px",
              color: "var(--muted)", textTransform: "uppercase",
              marginBottom: "16px", opacity: 0.5,
            }}>
              Ainda não tens um anúncio?
            </p>
            <p style={{
              fontSize: "14px", color: "var(--muted)", fontFamily: "var(--font-body)",
              lineHeight: 1.7, fontWeight: 300, maxWidth: "400px", marginBottom: "20px",
            }}>
              Responde a algumas perguntas sobre o teu estilo de vida e encontramos os modelos que melhor se adequam a ti.
            </p>
            <Link href="/escolher" className="pill-btn-ghost">
              descobrir o meu carro →
            </Link>
          </div>
        )}
      </div>
    </main>
  );
}

export default function AnalisarPage() {
  return (
    <Suspense fallback={
      <main style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
        <p style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)", letterSpacing: "1px" }}>A CARREGAR...</p>
      </main>
    }>
      <AnalisarContent />
    </Suspense>
  );
}
