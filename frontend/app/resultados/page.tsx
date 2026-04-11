"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Analytics } from "@/lib/analytics";
import { TrustPanel } from "@/app/components/TrustPanel";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Verdict badge colours ──
const TIER_STYLE: Record<string, { bg: string; color: string; label: string }> = {
  forte:    { bg: "rgba(74,163,90,0.12)",  color: "#4aa35a", label: "FORTE" },
  razoavel: { bg: "rgba(200,168,130,0.12)", color: "var(--accent)", label: "RAZOÁVEL" },
  cuidado:  { bg: "rgba(220,160,40,0.12)", color: "#dca028", label: "CUIDADO" },
  evitar:   { bg: "rgba(210,60,60,0.12)",  color: "#d23c3c", label: "EVITAR" },
};

const VERDICT_EMOTION: Record<string, string> = {
  forte:    "Este tipo de negócio não dura muito.",
  razoavel: "Um negócio justo — avança com confiança.",
  cuidado:  "Há melhores opções no mercado neste momento.",
  evitar:   "Não vale o risco. Continua a procurar.",
};

// ── Micro-feedback component ─────────────────────────────────────────────
const FEEDBACK_REASONS = [
  "Preço parece errado",
  "Informação incompleta",
  "Não concordo com veredicto",
];

function AnalysisMicroFeedback({ sessionId, listingUrl }: { sessionId: string; listingUrl: string }) {
  const [vote, setVote] = useState<"up" | "down" | null>(null);

  const handleVote = (v: "up" | "down") => {
    setVote(v);
    Analytics.analysisFeedback(sessionId, listingUrl, v === "up");
  };

  const handleReason = (reason: string) => {
    Analytics.analysisFeedback(sessionId, listingUrl, false, reason);
  };

  if (vote === "up") {
    return (
      <p style={{ marginTop: "12px", fontSize: "11px", color: "var(--muted)", fontFamily: "var(--font-body)", opacity: 0.5 }}>
        Obrigado pelo feedback.
      </p>
    );
  }

  return (
    <div style={{ marginTop: "12px" }}>
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

// ── Share button ──────────────────────────────────────────────────────────
function ShareButton({ result, listingUrl, sessionId }: { result: any; listingUrl: string; sessionId: string }) {
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

    Analytics.analysisShared(sessionId, listingUrl, "whatsapp");
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
        display: "flex", alignItems: "center", gap: "5px",
        background: "none", border: "none",
        cursor: "pointer",
        fontFamily: "var(--font-mono)", fontSize: "9px",
        letterSpacing: "1px", textTransform: "uppercase",
        color: shared ? "var(--accent)" : "var(--muted)",
        padding: 0,
        transition: "color 0.15s ease",
      }}
    >
      {shared ? "✓ Partilhado" : "↗ Partilhar"}
    </button>
  );
}

// ── Ad Analysis panel component ──────────────────────────────────────────
function AdAnalysisPanel({
  modelId,
  sessionId,
  userProfile,
  rank = 0,
}: {
  modelId: number;
  sessionId: string;
  userProfile: Record<string, number>;
  rank?: number;
}) {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const analyse = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    Analytics.adAnalysisRequested(sessionId, modelId, url.trim());
    try {
      const res = await fetch(`${API}/api/listings/analyse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          listing_url: url.trim(),
          model_id: modelId,
          user_profile: userProfile,
        }),
      });
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
      }
    } catch {
      setError("Erro ao analisar. Verifica a ligação e tenta novamente.");
    } finally {
      setLoading(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => { setOpen(true); Analytics.modelExpanded(sessionId, modelId, rank); }}
        style={{
          marginTop: "20px",
          display: "flex", alignItems: "center", gap: "8px",
          background: "none", border: "none", cursor: "pointer",
          fontFamily: "var(--font-mono)", fontSize: "10px",
          letterSpacing: "1.5px", color: "var(--muted)",
          padding: 0, textTransform: "uppercase",
          transition: "color 0.2s ease",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = "var(--accent)")}
        onMouseLeave={(e) => (e.currentTarget.style.color = "var(--muted)")}
      >
        <span style={{ fontSize: "14px" }}>↗</span> Analisar anúncio
      </button>
    );
  }

  const tier = result?.deal?.tier || result?.analysis?.verdict;
  const tierStyle = tier ? TIER_STYLE[tier] : null;

  return (
    <div style={{
      marginTop: "20px",
      borderTop: "1px solid var(--border)",
      paddingTop: "20px",
    }}>
      <p style={{
        fontFamily: "var(--font-mono)", fontSize: "10px",
        letterSpacing: "1.5px", textTransform: "uppercase",
        color: "var(--accent)", marginBottom: "12px",
      }}>
        Colar URL do anúncio
        <span style={{ marginLeft: "10px", letterSpacing: "0.5px", opacity: 0.5, fontWeight: 400 }}>
          Standvirtual · OLX · qualquer dealer
        </span>
      </p>

      <div style={{ display: "flex", gap: "8px" }}>
        <input
          type="url"
          placeholder="https://www.standvirtual.com/... · olx.pt/... · autosapo.pt/..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && analyse()}
          style={{
            flex: 1, padding: "10px 14px",
            borderRadius: "8px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            color: "var(--fg)",
            fontSize: "12px",
            fontFamily: "var(--font-body)",
            outline: "none",
            transition: "border-color 0.2s ease",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
        />
        <button
          onClick={analyse}
          disabled={loading || !url.trim()}
          style={{
            padding: "10px 18px",
            borderRadius: "8px",
            border: "1px solid var(--accent)",
            background: loading ? "transparent" : "var(--accent)",
            color: loading ? "var(--accent)" : "var(--bg)",
            fontSize: "12px", fontWeight: 600,
            fontFamily: "var(--font-body)",
            cursor: loading ? "wait" : "pointer",
            whiteSpace: "nowrap",
            transition: "all 0.2s ease",
            opacity: !url.trim() ? 0.4 : 1,
          }}
        >
          {loading ? "A analisar..." : "Analisar"}
        </button>
      </div>

      {error && (
        <p style={{ marginTop: "10px", fontSize: "12px", color: "#d23c3c", fontFamily: "var(--font-body)" }}>
          {error}
        </p>
      )}

      {result && (
        <div style={{ marginTop: "20px" }}>
          {/* Source badge + Dual Verdict */}
          <div style={{ marginBottom: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px", flexWrap: "wrap" }}>
              {result.source_label && (
                <span style={{
                  fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px",
                  color: "var(--muted)", border: "1px solid var(--border)",
                  padding: "3px 10px", borderRadius: "100px", textTransform: "uppercase",
                  opacity: 0.6,
                }}>
                  {result.source_label}
                </span>
              )}
              {tierStyle && (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "8px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "3px", opacity: 0.5 }}>Negócio</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "1px", color: tierStyle.color, background: tierStyle.bg, padding: "5px 14px", borderRadius: "100px", fontWeight: 600 }}>
                    {tierStyle.label}
                  </span>
                </div>
              )}
              {result.fit && (() => {
                const FIT_STYLE: Record<string, {bg: string; color: string}> = {
                  excelente: { bg: "rgba(74,163,90,0.12)",   color: "#4aa35a" },
                  bom:       { bg: "rgba(200,168,130,0.12)", color: "var(--accent)" },
                  parcial:   { bg: "rgba(220,160,40,0.12)",  color: "#dca028" },
                  fraco:     { bg: "rgba(210,60,60,0.12)",   color: "#d23c3c" },
                };
                const fs = FIT_STYLE[result.fit.fit_tier] || FIT_STYLE.parcial;
                return (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "8px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "3px", opacity: 0.5 }}>Para ti</span>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "1px", color: fs.color, background: fs.bg, padding: "5px 14px", borderRadius: "100px", fontWeight: 600 }}>
                      {result.fit.fit_label}
                    </span>
                  </div>
                );
              })()}
            </div>
            <p style={{ fontSize: "14px", fontWeight: 500, fontFamily: "var(--font-body)", color: "var(--fg)", lineHeight: 1.4, marginBottom: "6px" }}>
              {result.analysis?.verdict_reason}
            </p>
            {tier && VERDICT_EMOTION[tier] && (
              <p style={{ fontSize: "12px", fontFamily: "var(--font-body)", fontWeight: 300, color: "var(--muted)", fontStyle: "italic", opacity: 0.7, marginBottom: "4px" }}>
                {VERDICT_EMOTION[tier]}
              </p>
            )}
            {result.fit?.fit_reason && (
              <p style={{ fontSize: "12px", fontFamily: "var(--font-body)", fontWeight: 300, color: "var(--muted)", opacity: 0.7 }}>
                {result.fit.fit_reason}
              </p>
            )}
          </div>

          {/* Deal metrics row */}
          <div style={{
            display: "flex", gap: "20px", flexWrap: "wrap",
            marginBottom: "16px",
            padding: "12px 16px",
            background: "var(--surface)",
            borderRadius: "8px",
            border: "1px solid var(--border)",
          }}>
            {result.deal?.price_delta_pct != null && (
              <div>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "3px" }}>Preço vs. mercado</p>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: (result.deal.price_delta || 0) >= 0 ? "#4aa35a" : "#d23c3c", fontWeight: 600 }}>
                  {(result.deal.price_delta || 0) >= 0 ? "−" : "+"}{result.deal.price_delta_pct}%
                </p>
              </div>
            )}
            {result.deal?.km_per_year != null && (
              <div>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "3px" }}>Km/ano</p>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--fg)", fontWeight: 600 }}>
                  {Math.round(result.deal.km_per_year).toLocaleString("pt-PT")}
                </p>
              </div>
            )}
            {result.deal?.market_avg_price != null && (
              <div>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "3px" }}>
                  Referência mercado
                  <span style={{ opacity: 0.4, marginLeft: "6px", textTransform: "none", fontSize: "8px" }}>
                    {result.deal.market_data_source === "live" ? "tempo real" : "histórico"}
                  </span>
                </p>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--fg)", fontWeight: 600 }}>
                  {Math.round(result.deal.market_avg_price).toLocaleString("pt-PT")} €
                </p>
              </div>
            )}
            {result.analysis?.spec_tier && (
              <div>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "3px" }}>Versão</p>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--fg)", fontWeight: 600 }}>
                  {result.analysis.trim_level || result.analysis.spec_tier.toUpperCase()}
                </p>
              </div>
            )}
          </div>

          {/* Flags */}
          <div style={{ display: "flex", gap: "12px", marginBottom: "14px", flexWrap: "wrap" }}>
            {(result.analysis?.green_flags || []).map((f: string, i: number) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ color: "#4aa35a", fontSize: "12px" }}>✓</span>
                <span style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)" }}>{f}</span>
              </div>
            ))}
            {(result.analysis?.red_flags || []).map((f: string, i: number) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ color: "#d23c3c", fontSize: "12px" }}>⚠</span>
                <span style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)" }}>{f}</span>
              </div>
            ))}
          </div>

          {/* Key extras */}
          {result.analysis?.key_extras?.length > 0 && (
            <div style={{ marginBottom: "14px" }}>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px" }}>Extras detetados</p>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {result.analysis.key_extras.map((e: string, i: number) => (
                  <span key={i} style={{
                    fontFamily: "var(--font-mono)", fontSize: "10px",
                    color: "var(--muted)", border: "1px solid var(--border)",
                    padding: "3px 10px", borderRadius: "100px",
                  }}>{e}</span>
                ))}
              </div>
            </div>
          )}

          {/* Profile fit */}
          {result.analysis?.profile_fit && (
            <p style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.6, marginBottom: "12px" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", textTransform: "uppercase", opacity: 0.5, marginRight: "8px" }}>Para ti</span>
              {result.analysis.profile_fit}
            </p>
          )}

          {/* Verdict narrative (LLM) */}
          {result.analysis?.verdict_narrative && (
            <div style={{ padding: "12px 16px", borderRadius: "8px", background: "var(--surface)", border: "1px solid var(--border)", marginBottom: "12px" }}>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "8px", letterSpacing: "1.5px", color: "var(--accent)", textTransform: "uppercase", marginBottom: "6px" }}>Veredicto</p>
              <p style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.6 }}>{result.analysis.verdict_narrative}</p>
            </div>
          )}

          {/* Negotiation (LLM script or rule tips) */}
          {(result.analysis?.negotiation_script || result.negotiation_tips?.length > 0) && (
            <div style={{ marginBottom: "12px" }}>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "8px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px" }}>Como negociar</p>
              {result.analysis?.negotiation_script ? (
                <p style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.6 }}>{result.analysis.negotiation_script}</p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {result.negotiation_tips.map((tip: string, i: number) => (
                    <div key={i} style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}>
                      <span style={{ color: "var(--accent)", fontSize: "11px", flexShrink: 0, marginTop: "1px" }}>→</span>
                      <span style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.5 }}>{tip}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Inspection checklist */}
          {result.inspection_checklist?.length > 0 && (
            <div style={{ marginBottom: "12px" }}>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "8px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px" }}>O que verificar</p>
              <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
                {result.inspection_checklist.map((item: string, i: number) => (
                  <div key={i} style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--accent)", flexShrink: 0, marginTop: "2px" }}>{String(i + 1).padStart(2, "0")}</span>
                    <span style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.5 }}>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Caveat */}
          <p style={{
            fontSize: "10px", color: "var(--muted)", fontFamily: "var(--font-body)",
            opacity: 0.4, lineHeight: 1.5,
            borderTop: "1px solid var(--border)", paddingTop: "10px",
          }}>
            {result.caveat}
          </p>

          {/* Micro-feedback + Share */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "10px", marginTop: "4px" }}>
            <AnalysisMicroFeedback
              sessionId={sessionId}
              listingUrl={url}
            />
            <ShareButton result={result} listingUrl={url} sessionId={sessionId} />
          </div>

          {/* Reset */}
          <button
            onClick={() => { setResult(null); setUrl(""); }}
            style={{
              marginTop: "12px", background: "none", border: "none",
              cursor: "pointer", fontFamily: "var(--font-mono)", fontSize: "9px",
              letterSpacing: "1px", textTransform: "uppercase", color: "var(--muted)",
              padding: 0,
            }}
          >
            Analisar outro anúncio ↩
          </button>
        </div>
      )}
    </div>
  );
}

const DISMISS_REASONS = [
  "Não gosto da marca",
  "Quero algo mais desportivo",
  "Quero algo mais luxuoso",
  "Quero algo mais prático",
  "Acima do meu orçamento",
  "Não é o estilo certo",
];

export default function ResultadosPage() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [interests, setInterests] = useState<number[]>([]);
  const [dismissed, setDismissed] = useState<Record<number, string>>({});
  const [showReasons, setShowReasons] = useState<number | null>(null);
  const [alternatives, setAlternatives] = useState<any[]>([]);
  const [alternativesLoading, setAlternativesLoading] = useState(false);
  const [alternativesFetched, setAlternativesFetched] = useState(false);
  const [alternativesError, setAlternativesError] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("caractr_results");
    if (stored) {
      const parsed = JSON.parse(stored);
      setData(parsed);
      // Track results viewed
      const recs = parsed.recommendations || [];
      Analytics.resultsViewed(
        parsed.session_id || "",
        recs.length,
        recs.some((r: any) => r.is_wildcard),
        recs.some((r: any) => r.is_stretch),
      );
    } else {
      router.push("/escolher");
    }
  }, []);

  if (!data) {
    return (
      <main style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
        <p style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)", letterSpacing: "1px" }}>A CARREGAR...</p>
      </main>
    );
  }

  const recs = data.recommendations || [];
  const first = recs[0];
  const rest = recs.slice(1);

  const allModels = [...recs, ...alternatives];
  const interestedRecs = allModels.filter((r: any) => interests.includes(r.model_id));
  const allDismissed = recs.length > 0 && recs.every((r: any) => dismissed[r.model_id]);

  const handleInterest = (modelId: number) => {
    setInterests(prev => prev.includes(modelId) ? prev.filter(id => id !== modelId) : [...prev, modelId]);
    setDismissed(prev => { const n = { ...prev }; delete n[modelId]; return n; });
    setShowReasons(null);
  };
  const handleDismiss = (modelId: number, reason: string) => {
    setDismissed(prev => ({ ...prev, [modelId]: reason }));
    setInterests(prev => prev.filter(id => id !== modelId));
    setShowReasons(null);
    Analytics.feedbackSubmitted(data.session_id || "", "dismissed", modelId);
  };

  const fetchAlternatives = async () => {
    const dismissedIds = Object.keys(dismissed).map(Number);
    const dismissReasons = Object.values(dismissed);
    setAlternativesLoading(true);
    setAlternativesError(false);
    try {
      const res = await fetch(`${API}/api/recommend/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: data.session_id,
          dismissed_model_ids: dismissedIds,
          dismiss_reasons: dismissReasons,
          count: 3,
        }),
      });
      const json = await res.json();
      if (json.recommendations?.length > 0) {
        setAlternatives(json.recommendations);
      } else {
        setAlternativesError(true);
      }
    } catch {
      setAlternativesError(true);
    } finally {
      setAlternativesLoading(false);
      setAlternativesFetched(true);
    }
  };

  // Interest row — sits at the bottom of each recommendation card
  const InterestRow = ({ modelId }: { modelId: number }) => {
    const isInterested = interests.includes(modelId);
    const dismissReason = dismissed[modelId];
    const showingReasons = showReasons === modelId;
    return (
      <div style={{ marginTop: "20px", paddingTop: "16px", borderTop: "1px solid var(--border)" }}>
        {isInterested ? (
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "1px", color: "#4aa35a", display: "flex", alignItems: "center", gap: "6px" }}>
              <span>✓</span> Com interesse
            </span>
            <button onClick={() => handleInterest(modelId)} style={{ background: "none", border: "none", cursor: "pointer", fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)", letterSpacing: "0.5px", padding: 0, opacity: 0.5 }}>
              desfazer
            </button>
          </div>
        ) : dismissReason ? (
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "11px", color: "var(--muted)", fontFamily: "var(--font-body)", opacity: 0.5 }}>{dismissReason}</span>
            <button onClick={() => { setDismissed(prev => { const n = { ...prev }; delete n[modelId]; return n; }); }} style={{ background: "none", border: "none", cursor: "pointer", fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)", letterSpacing: "0.5px", padding: 0, opacity: 0.5 }}>
              desfazer
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <button
              onClick={() => handleInterest(modelId)}
              style={{ background: "none", border: "1px solid #4aa35a", borderRadius: "100px", padding: "5px 14px", cursor: "pointer", fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "0.5px", color: "#4aa35a", transition: "all 0.15s ease" }}
              onMouseEnter={e => { e.currentTarget.style.background = "rgba(74,163,90,0.08)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "none"; }}
            >
              Tenho interesse
            </button>
            <button
              onClick={() => setShowReasons(showingReasons ? null : modelId)}
              style={{ background: "none", border: "none", cursor: "pointer", fontFamily: "var(--font-body)", fontSize: "12px", color: "var(--muted)", padding: 0, opacity: 0.5, transition: "opacity 0.15s ease" }}
              onMouseEnter={e => { e.currentTarget.style.opacity = "1"; }}
              onMouseLeave={e => { e.currentTarget.style.opacity = "0.5"; }}
            >
              Não é para mim
            </button>
          </div>
        )}
        {showingReasons && (
          <div style={{ marginTop: "10px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {DISMISS_REASONS.map(reason => (
              <button
                key={reason}
                onClick={() => handleDismiss(modelId, reason)}
                style={{ background: "none", border: "1px solid var(--border)", borderRadius: "100px", padding: "4px 12px", cursor: "pointer", fontFamily: "var(--font-body)", fontSize: "11px", color: "var(--muted)", transition: "all 0.15s ease" }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--accent)"; e.currentTarget.style.color = "var(--fg)"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--muted)"; }}
              >
                {reason}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  const profileLabels: Record<string, string> = {
    economy: "Economia", comfort: "Conforto", driving: "Condução",
    practical: "Praticidade", status: "Imagem", reliability: "Fiabilidade",
  };

  const Badge = ({ label }: { label: string }) => (
    <span style={{
      fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "1px",
      color: "var(--accent)", background: "rgba(200,168,130,0.1)",
      padding: "4px 14px", borderRadius: "100px",
    }}>
      {label}
    </span>
  );

  return (
    <main style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--fg)" }}>

      {/* ════════════════════════════════════
          DARK HERO HEADER
      ════════════════════════════════════ */}
      <section style={{
        background: "var(--bg-dark)",
        padding: "clamp(32px, 5vw, 48px) clamp(24px, 5vw, 80px) clamp(48px, 6vw, 80px)",
      }}>
        {/* Nav row */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "clamp(48px, 6vw, 80px)" }}>
          <Link
            href="/"
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "14px",
              fontWeight: 700,
              letterSpacing: "0.12em",
              color: "var(--fg-inv)",
              textDecoration: "none",
            }}
          >
            CARACTR
          </Link>
          <Link href="/escolher" className="pill-btn-inv" style={{ padding: "8px 20px", fontSize: "13px" }}>
            nova pesquisa
          </Link>
        </div>

        {/* Title */}
        <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "20px" }} />
        <h1 style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(36px, 6vw, 80px)",
          fontWeight: 800,
          lineHeight: 0.9,
          letterSpacing: "-0.03em",
          color: "var(--fg-inv)",
          marginBottom: "24px",
        }}>
          A TUA SHORTLIST
        </h1>

        {/* Profile narrative — summary pill + story card */}
        {(data.profile_narrative?.summary || data.profile_summary) && (
          <div style={{ marginBottom: "clamp(32px, 4vw, 48px)" }}>
            {/* Summary pill */}
            <div style={{
              display: "inline-flex", alignItems: "center", gap: "16px",
              padding: "8px 18px",
              borderRadius: "100px",
              border: "1px solid rgba(200,168,130,0.2)",
              background: "rgba(200,168,130,0.06)",
              marginBottom: "20px",
            }}>
              <p style={{ fontSize: "13px", color: "rgba(242,239,233,0.6)", fontWeight: 300, fontFamily: "var(--font-body)" }}>
                {data.profile_narrative?.summary || data.profile_summary}
              </p>
              <Link href="/escolher" style={{
                fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px",
                color: "var(--accent)", textDecoration: "none", opacity: 0.7,
                whiteSpace: "nowrap", textTransform: "uppercase",
              }}>
                Alterar
              </Link>
            </div>

            {/* Profile story lines */}
            {data.profile_narrative && (() => {
              const n = data.profile_narrative;
              const lines = [n.priorities, n.tension, n.aversion, n.identity, n.context].filter(Boolean);
              if (lines.length === 0) return null;
              return (
                <div style={{
                  padding: "20px 24px",
                  borderRadius: "12px",
                  border: "1px solid rgba(200,168,130,0.12)",
                  background: "rgba(255,255,255,0.03)",
                  display: "flex", flexDirection: "column", gap: "12px",
                  maxWidth: "600px",
                }}>
                  {lines.map((line, i) => (
                    <div key={i} style={{ display: "flex", gap: "14px", alignItems: "flex-start" }}>
                      <div style={{ width: "3px", height: "3px", borderRadius: "50%", background: "var(--accent)", marginTop: "9px", flexShrink: 0 }} />
                      <p style={{ fontSize: "13px", color: "rgba(242,239,233,0.5)", fontWeight: 300, lineHeight: 1.65, fontFamily: "var(--font-body)" }}>
                        {line}
                      </p>
                    </div>
                  ))}
                </div>
              );
            })()}
          </div>
        )}

        {/* Profile attribute bars */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: "20px" }}>
          {Object.entries(data.profile || {}).map(([key, val]: [string, any]) => (
            <div key={key}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "8px" }}>
                <span style={{ fontSize: "10px", letterSpacing: "1px", color: "rgba(242,239,233,0.3)", textTransform: "uppercase", fontFamily: "var(--font-body)" }}>
                  {profileLabels[key] || key}
                </span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--accent)" }}>
                  {Math.round(val * 100)}
                </span>
              </div>
              <div style={{ height: "2px", borderRadius: "1px", background: "rgba(242,239,233,0.08)" }}>
                <div style={{
                  height: "100%",
                  borderRadius: "1px",
                  width: `${Math.round(val * 100)}%`,
                  background: "var(--accent)",
                  transition: "width 1s ease-out",
                }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ════════════════════════════════════
          FEATURED RECOMMENDATION #1
      ════════════════════════════════════ */}
      {first && (
        <section
          style={{ padding: "clamp(48px, 6vw, 80px) clamp(24px, 5vw, 80px)", cursor: "default" }}
          onClick={() => Analytics.modelClicked(data.session_id || "", first.model_id, 1, !!first.is_wildcard)}
        >
          <div style={{ maxWidth: "800px", opacity: dismissed[first.model_id] ? 0.42 : 1, transition: "opacity 0.3s ease" }}>
            <p style={{
              fontFamily: "var(--font-mono)", fontSize: "10px",
              letterSpacing: "1.5px", color: "var(--accent)",
              textTransform: "uppercase", marginBottom: "16px", opacity: 0.8,
            }}>
              A tua melhor correspondência
            </p>
          <div style={{ display: "flex", alignItems: "baseline", gap: "20px", marginBottom: "24px" }}>
              <span style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(48px, 8vw, 96px)",
                fontWeight: 800,
                color: "var(--border)",
                opacity: 0.3,
                lineHeight: 0.75,
              }}>
                01
              </span>
              <div>
                <h2 style={{
                  fontFamily: "var(--font-display)",
                  fontSize: "clamp(22px, 3vw, 32px)",
                  fontWeight: 700,
                  letterSpacing: "-0.02em",
                  lineHeight: 1.1,
                }}>
                  {first.full_name}
                </h2>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--accent)" }}>
                  {first.price_range?.min?.toLocaleString("pt-PT")} — {first.price_range?.max?.toLocaleString("pt-PT")} EUR
                </span>
              </div>
            </div>

            <p style={{
              fontFamily: "var(--font-display)",
              fontSize: "clamp(20px, 2.5vw, 28px)",
              fontWeight: 400,
              lineHeight: 1.2,
              letterSpacing: "-0.01em",
              maxWidth: "560px",
              marginBottom: "28px",
            }}>
              {first.headline}
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "32px" }}>
              {first.reasons?.map((r: string, i: number) => (
                <div key={i} style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
                  <div style={{ marginTop: "8px", flexShrink: 0, width: "4px", height: "4px", borderRadius: "50%", background: "var(--accent)" }} />
                  <p style={{ fontSize: "14px", color: "var(--muted)", lineHeight: 1.7, fontWeight: 300, fontFamily: "var(--font-body)" }}>{r}</p>
                </div>
              ))}
            </div>

            {first.tradeoff && (
              <div style={{ borderLeft: "2px solid var(--border)", paddingLeft: "20px", marginBottom: "20px" }}>
                <p style={{ fontSize: "13px", color: "var(--muted)", lineHeight: 1.6, fontWeight: 300, fontFamily: "var(--font-body)" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", letterSpacing: "1px", marginRight: "8px", opacity: 0.5 }}>TRADEOFF</span>
                  {first.tradeoff}
                </p>
              </div>
            )}

            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "4px" }}>
              {first.is_stretch && <Badge label="STRETCH" />}
              {first.is_wildcard && <Badge label="WILDCARD" />}
            </div>

            <InterestRow modelId={first.model_id} />
            <AdAnalysisPanel
              modelId={first.model_id}
              sessionId={data.session_id || ""}
              userProfile={data.profile || {}}
              rank={1}
            />
            <TrustPanel
              reliability={first.reliability}
              market={first.market}
              modelName={first.full_name}
            />
          </div>
        </section>
      )}

      {/* ════════════════════════════════════
          REMAINING #2–#5 GRID
      ════════════════════════════════════ */}
      <section style={{ padding: "0 clamp(24px, 5vw, 80px) clamp(48px, 6vw, 64px)" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))", gap: "12px" }}>
          {rest.map((rec: any, i: number) => (
            <div
              key={rec.model_id || i}
              style={{
                padding: "28px",
                borderRadius: "16px",
                border: "1px solid var(--border)",
                background: "var(--surface)",
                transition: "border-color 0.2s ease, opacity 0.3s ease",
                cursor: "default",
                opacity: dismissed[rec.model_id] ? 0.42 : 1,
              }}
              onMouseEnter={(e) => { if (!dismissed[rec.model_id]) e.currentTarget.style.borderColor = "var(--accent)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border)"; }}
              onClick={() => Analytics.modelClicked(data.session_id || "", rec.model_id, i + 2, !!rec.is_wildcard)}
            >
              {(rec.is_stretch || rec.is_wildcard) && (
                <p style={{
                  fontFamily: "var(--font-mono)", fontSize: "9px",
                  letterSpacing: "1.5px", textTransform: "uppercase",
                  color: rec.is_stretch ? "var(--accent)" : "var(--muted)",
                  marginBottom: "12px", opacity: 0.8,
                }}>
                  {rec.is_stretch ? "Acima do orçamento — mas vale considerar" : "Fora do esperado — mas ouve-nos"}
                </p>
              )}
              <div style={{ display: "flex", alignItems: "baseline", gap: "12px", marginBottom: "20px" }}>
                <span style={{
                  fontFamily: "var(--font-display)",
                  fontSize: "clamp(28px, 4vw, 48px)",
                  fontWeight: 800,
                  color: "var(--border)",
                  opacity: 0.4,
                  lineHeight: 0.75,
                }}>
                  {String(i + 2).padStart(2, "0")}
                </span>
                <div>
                  <h3 style={{
                    fontFamily: "var(--font-display)",
                    fontSize: "17px",
                    fontWeight: 700,
                    letterSpacing: "-0.01em",
                  }}>
                    {rec.full_name}
                  </h3>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--accent)" }}>
                    {rec.price_range?.min?.toLocaleString("pt-PT")} — {rec.price_range?.max?.toLocaleString("pt-PT")} EUR
                  </span>
                </div>
              </div>

              <p style={{
                fontFamily: "var(--font-display)",
                fontSize: "16px",
                fontWeight: 400,
                lineHeight: 1.2,
                marginBottom: "14px",
                letterSpacing: "-0.01em",
              }}>
                {rec.headline}
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: rec.tradeoff ? "12px" : "20px" }}>
                {rec.reasons?.slice(0, 2).map((r: string, j: number) => (
                  <div key={j} style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}>
                    <div style={{ marginTop: "7px", flexShrink: 0, width: "3px", height: "3px", borderRadius: "50%", background: "var(--accent)" }} />
                    <p style={{ fontSize: "13px", color: "var(--muted)", lineHeight: 1.6, fontWeight: 300, fontFamily: "var(--font-body)" }}>{r}</p>
                  </div>
                ))}
              </div>

              {rec.tradeoff && (
                <div style={{ borderLeft: "2px solid var(--border)", paddingLeft: "14px", marginBottom: "20px" }}>
                  <p style={{ fontSize: "12px", color: "var(--muted)", lineHeight: 1.6, fontWeight: 300, fontFamily: "var(--font-body)", opacity: 0.7 }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)", letterSpacing: "1px", marginRight: "6px", opacity: 0.5, textTransform: "uppercase" }}>Tradeoff</span>
                    {rec.tradeoff}
                  </p>
                </div>
              )}

              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "4px" }}>
                {rec.is_wildcard && <Badge label="WILDCARD" />}
                {rec.is_stretch && <Badge label="STRETCH" />}
                {rec.body_type && !rec.is_wildcard && !rec.is_stretch && (
                  <span style={{
                    fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)",
                    border: "1px solid var(--border)", padding: "3px 12px", borderRadius: "100px",
                  }}>
                    {rec.body_type.toUpperCase()}
                  </span>
                )}
              </div>

              <InterestRow modelId={rec.model_id} />
              <AdAnalysisPanel
                modelId={rec.model_id}
                sessionId={data.session_id || ""}
                userProfile={data.profile || {}}
                rank={i + 2}
              />
              <TrustPanel
                reliability={rec.reliability}
                market={rec.market}
                modelName={rec.full_name}
              />
            </div>
          ))}
        </div>
      </section>

      {/* ════════════════════════════════════
          ALTERNATIVES — appears after dismissals
      ════════════════════════════════════ */}
      {Object.keys(dismissed).length > 0 && (
        <section style={{ padding: "0 clamp(24px, 5vw, 80px) clamp(40px, 5vw, 56px)" }}>

          {/* CTA to fetch alternatives */}
          {!alternativesFetched && !alternativesLoading && (
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "20px 24px",
              borderRadius: "12px",
              border: "1px dashed var(--border)",
              gap: "16px", flexWrap: "wrap",
            }}>
              <p style={{ fontSize: "13px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.5 }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", color: "var(--accent)", textTransform: "uppercase", marginRight: "10px" }}>
                  {Object.keys(dismissed).length === 1 ? "1 descartado" : `${Object.keys(dismissed).length} descartados`}
                </span>
                Usámos o teu feedback para ajustar o perfil. Queres ver alternativas?
              </p>
              <button
                onClick={fetchAlternatives}
                style={{
                  padding: "9px 22px",
                  borderRadius: "100px",
                  border: "1px solid var(--accent)",
                  background: "transparent",
                  color: "var(--accent)",
                  fontFamily: "var(--font-mono)", fontSize: "10px",
                  letterSpacing: "1px", textTransform: "uppercase",
                  cursor: "pointer", whiteSpace: "nowrap",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(200,168,130,0.08)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
              >
                Ver alternativas →
              </button>
            </div>
          )}

          {/* Loading */}
          {alternativesLoading && (
            <div style={{ textAlign: "center", padding: "40px 0" }}>
              <p style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", letterSpacing: "2px", textTransform: "uppercase", opacity: 0.6 }}>
                A ajustar o perfil e procurar alternativas...
              </p>
            </div>
          )}

          {/* Error */}
          {alternativesFetched && alternativesError && (
            <p style={{ fontFamily: "var(--font-body)", fontSize: "13px", color: "var(--muted)", textAlign: "center", padding: "24px 0", opacity: 0.5 }}>
              Não encontrámos alternativas suficientemente diferentes. Tenta refinar o perfil.
            </p>
          )}

          {/* Alternative cards */}
          {alternatives.length > 0 && (
            <>
              <div style={{ marginBottom: "20px", display: "flex", alignItems: "center", gap: "16px" }}>
                <div style={{ width: "32px", height: "1px", background: "var(--accent)", opacity: 0.4 }} />
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "2px", color: "var(--accent)", textTransform: "uppercase", opacity: 0.7 }}>
                  Alternativas — baseadas no teu feedback
                </p>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))", gap: "12px" }}>
                {alternatives.map((rec: any, i: number) => (
                  <div
                    key={`alt-${rec.model_id || i}`}
                    style={{
                      padding: "28px",
                      borderRadius: "16px",
                      border: "1px solid var(--border)",
                      background: "var(--surface)",
                      transition: "border-color 0.2s ease",
                      cursor: "default",
                      position: "relative",
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border)"; }}
                    onClick={() => Analytics.modelClicked(data.session_id || "", rec.model_id, 10 + i, !!rec.is_wildcard)}
                  >
                    {/* "Alternativa" tag */}
                    <p style={{
                      fontFamily: "var(--font-mono)", fontSize: "9px",
                      letterSpacing: "1.5px", textTransform: "uppercase",
                      color: "var(--muted)", marginBottom: "12px", opacity: 0.5,
                    }}>
                      Alternativa
                    </p>

                    <div style={{ display: "flex", alignItems: "baseline", gap: "12px", marginBottom: "20px" }}>
                      <div>
                        <h3 style={{
                          fontFamily: "var(--font-display)",
                          fontSize: "17px", fontWeight: 700, letterSpacing: "-0.01em",
                        }}>
                          {rec.full_name}
                        </h3>
                        <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--accent)" }}>
                          {rec.price_range?.min?.toLocaleString("pt-PT")} — {rec.price_range?.max?.toLocaleString("pt-PT")} EUR
                        </span>
                      </div>
                    </div>

                    <p style={{
                      fontFamily: "var(--font-display)",
                      fontSize: "16px", fontWeight: 400,
                      lineHeight: 1.2, marginBottom: "14px",
                      letterSpacing: "-0.01em",
                    }}>
                      {rec.headline}
                    </p>

                    <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: rec.tradeoff ? "12px" : "20px" }}>
                      {rec.reasons?.slice(0, 2).map((r: string, j: number) => (
                        <div key={j} style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}>
                          <div style={{ marginTop: "7px", flexShrink: 0, width: "3px", height: "3px", borderRadius: "50%", background: "var(--accent)" }} />
                          <p style={{ fontSize: "13px", color: "var(--muted)", lineHeight: 1.6, fontWeight: 300, fontFamily: "var(--font-body)" }}>{r}</p>
                        </div>
                      ))}
                    </div>

                    {rec.tradeoff && (
                      <div style={{ borderLeft: "2px solid var(--border)", paddingLeft: "14px", marginBottom: "20px" }}>
                        <p style={{ fontSize: "12px", color: "var(--muted)", lineHeight: 1.6, fontWeight: 300, fontFamily: "var(--font-body)", opacity: 0.7 }}>
                          <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)", letterSpacing: "1px", marginRight: "6px", opacity: 0.5, textTransform: "uppercase" }}>Tradeoff</span>
                          {rec.tradeoff}
                        </p>
                      </div>
                    )}

                    {rec.body_type && (
                      <div style={{ marginBottom: "4px" }}>
                        <span style={{
                          fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)",
                          border: "1px solid var(--border)", padding: "3px 12px", borderRadius: "100px",
                        }}>
                          {rec.body_type.toUpperCase()}
                        </span>
                      </div>
                    )}

                    <InterestRow modelId={rec.model_id} />
                    <AdAnalysisPanel
                      modelId={rec.model_id}
                      sessionId={data.session_id || ""}
                      userProfile={data.profile || {}}
                      rank={10 + i}
                    />
                    <TrustPanel
                      reliability={rec.reliability}
                      market={rec.market}
                      modelName={rec.full_name}
                    />
                  </div>
                ))}
              </div>
            </>
          )}
        </section>
      )}

      {/* Suggestions */}
      {data.suggestions && (
        <section style={{
          padding: "clamp(24px, 4vw, 32px) clamp(24px, 5vw, 80px)",
          background: "var(--surface)",
          margin: "0 clamp(24px, 5vw, 80px)",
          borderRadius: "12px",
        }}>
          <p style={{ fontSize: "14px", color: "var(--muted)", lineHeight: 1.7, fontWeight: 300, fontFamily: "var(--font-body)" }}>
            Encontrámos {data.suggestions.models_available} opções no teu orçamento. Se alargares até{" "}
            <span style={{ color: "var(--accent)" }}>{data.suggestions.stretch_budget?.toLocaleString("pt-PT")} EUR</span>, tens mais opções.
          </p>
        </section>
      )}

      {/* ════════════════════════════════════
          CONCIERGE CTA — Reactive
      ════════════════════════════════════ */}
      <section style={{
        padding: "clamp(48px, 6vw, 72px) clamp(24px, 5vw, 80px)",
        borderTop: "1px solid var(--border)",
        marginTop: "clamp(32px, 4vw, 56px)",
        display: "flex", flexDirection: "column", alignItems: "center",
        textAlign: "center",
      }}>
        <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "20px" }} />

        {interestedRecs.length > 0 ? (
          // User expressed interest in specific models
          <>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(24px, 3.5vw, 40px)", fontWeight: 800, letterSpacing: "-0.02em", marginBottom: "12px" }}>
              Ótimo.{" "}
              <span style={{ color: "var(--accent-dark)" }}>
                {interestedRecs.length === 1
                  ? `Quer que encontremos um ${interestedRecs[0].full_name} para ti?`
                  : `Quer ajuda a encontrar uma destas opções?`}
              </span>
            </h2>
            <p style={{ fontSize: "15px", fontWeight: 300, color: "var(--muted)", fontFamily: "var(--font-body)", maxWidth: "480px", lineHeight: 1.7, marginBottom: "8px" }}>
              Durante o lançamento, a pesquisa é gratuita para um número limitado de utilizadores.
              Deixa o teu contacto e tratamos do resto.
            </p>
            {interestedRecs.length > 1 && (
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "center", marginBottom: "16px" }}>
                {interestedRecs.map((r: any) => (
                  <span key={r.model_id} style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--accent)", border: "1px solid var(--accent)", borderRadius: "100px", padding: "4px 12px", opacity: 0.8 }}>
                    {r.full_name}
                  </span>
                ))}
              </div>
            )}
            <Link
              href={`/concierge?session=${data.session_id}&models=${encodeURIComponent(interestedRecs.map((r: any) => r.full_name).join(","))}&model_ids=${interestedRecs.map((r: any) => r.model_id).join(",")}&model=${encodeURIComponent(interestedRecs[0]?.full_name || "")}&model_id=${interestedRecs[0]?.model_id || ""}`}
              className="pill-btn-solid"
              style={{ marginTop: "12px" }}
            >
              Sim, quero ajuda
            </Link>
          </>
        ) : allDismissed ? (
          // User dismissed every recommendation
          <>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(24px, 3.5vw, 40px)", fontWeight: 800, letterSpacing: "-0.02em", marginBottom: "12px" }}>
              Nenhuma sugestão acertou.
            </h2>
            <p style={{ fontSize: "15px", fontWeight: 300, color: "var(--muted)", fontFamily: "var(--font-body)", maxWidth: "480px", lineHeight: 1.7, marginBottom: "28px" }}>
              O teu feedback já foi registado — vamos usar para melhorar.
              Podes refinar o teu perfil e tentar de novo, ou pedir-nos que façamos a pesquisa por ti.
            </p>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", justifyContent: "center" }}>
              <Link href="/escolher" className="pill-btn">
                Refinar o meu perfil
              </Link>
              <Link href={`/concierge?session=${data.session_id}`} className="pill-btn-solid">
                Peço que façam por mim
              </Link>
            </div>
          </>
        ) : (
          // Default — no interaction yet
          <>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(24px, 3.5vw, 40px)", fontWeight: 800, letterSpacing: "-0.02em", marginBottom: "12px" }}>
              Queres uma shortlist de anúncios reais?
            </h2>
            <p style={{ fontSize: "15px", fontWeight: 300, color: "var(--muted)", fontFamily: "var(--font-body)", maxWidth: "480px", lineHeight: 1.7, marginBottom: "28px" }}>
              Pesquisamos o mercado com base no teu perfil e enviamos-te os melhores anúncios encontrados.
              Gratuito durante o lançamento.
            </p>
            <Link href={`/concierge?session=${data.session_id}`} className="pill-btn-solid">
              reservar o meu lugar
            </Link>
          </>
        )}
      </section>

      {/* ════════════════════════════════════
          FEEDBACK CTA — Dark section
      ════════════════════════════════════ */}
      <section style={{
        background: "var(--bg-dark)",
        padding: "clamp(48px, 8vw, 96px) clamp(24px, 5vw, 80px)",
        textAlign: "center",
      }}>
        <h2 style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(28px, 4vw, 48px)",
          fontWeight: 800,
          color: "var(--fg-inv)",
          marginBottom: "12px",
          letterSpacing: "-0.02em",
        }}>
          Gostaste?
        </h2>
        <p style={{
          fontSize: "15px",
          fontWeight: 300,
          color: "rgba(242,239,233,0.4)",
          fontFamily: "var(--font-body)",
          marginBottom: "32px",
        }}>
          Ajuda-nos a melhorar em 30 segundos.
        </p>
        <Link href={`/feedback?session=${data.session_id}`} className="pill-btn-inv">
          dar feedback
        </Link>
      </section>

      {/* ── Footer ── */}
      <footer style={{
        padding: "20px clamp(24px, 5vw, 80px)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        borderTop: "1px solid var(--border)",
      }}>
        <span style={{ fontFamily: "var(--font-display)", fontSize: "11px", fontWeight: 700, letterSpacing: "0.12em", color: "var(--muted)", opacity: 0.4 }}>CARACTR</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)", letterSpacing: "2px", textTransform: "uppercase", opacity: 0.4 }}>informar nunca assustar</span>
        <span style={{ fontFamily: "var(--font-body)", fontSize: "11px", color: "var(--muted)", opacity: 0.4 }}>2026</span>
      </footer>
    </main>
  );
}
