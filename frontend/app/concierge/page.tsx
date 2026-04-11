"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const FEEDBACK_TAGS = [
  { id: "wrong_brand",      label: "Não me identifico com a marca" },
  { id: "want_sportier",    label: "Quero algo mais desportivo" },
  { id: "want_comfort",     label: "Quero mais conforto" },
  { id: "want_practical",   label: "Quero algo mais prático" },
  { id: "budget_off",       label: "Orçamento não está certo" },
  { id: "want_premium",     label: "Quero algo mais premium" },
  { id: "want_discreet",    label: "Quero algo mais discreto" },
  { id: "want_bigger",      label: "Preciso de mais espaço" },
];

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "14px 18px",
  borderRadius: "10px",
  border: "1px solid var(--border)",
  background: "var(--surface)",
  color: "var(--fg)",
  fontSize: "14px",
  fontWeight: 300,
  fontFamily: "var(--font-body)",
  outline: "none",
  transition: "border-color 0.2s ease",
  boxSizing: "border-box",
};

function ConciergeContent() {
  const searchParams   = useSearchParams();
  const sessionId      = searchParams.get("session")         || "";
  const modelFromUrl   = searchParams.get("model")           || "";
  const modelsFromUrl  = searchParams.get("models")          || ""; // comma-separated
  const modelIdParam   = searchParams.get("model_id")        || "";
  const modelIdsParam  = searchParams.get("model_ids")       || ""; // comma-separated
  const listingUrl     = searchParams.get("listing_url")     || "";
  const listingVerdict = searchParams.get("listing_verdict") || "";

  const [name,              setName]              = useState("");
  const [email,             setEmail]             = useState("");
  const [modelInterest,     setModelInterest]     = useState("");
  const [budgetMax,         setBudgetMax]         = useState("");
  const [selectedTags,      setSelectedTags]      = useState<string[]>([]);
  const [consentCaractr,    setConsentCaractr]    = useState(false);
  const [consentDealer,     setConsentDealer]     = useState(false);
  const [sending,           setSending]           = useState(false);
  const [submitted,         setSubmitted]         = useState(false);
  const [error,             setError]             = useState("");
  const [profileNarrative,  setProfileNarrative]  = useState<any>(null);
  const [listingModel,      setListingModel]      = useState("");
  const [interestedModels,  setInterestedModels]  = useState<string[]>([]);

  useEffect(() => {
    // Build model interest string from URL params (single or multi-model)
    if (modelsFromUrl) {
      const models = decodeURIComponent(modelsFromUrl).split(",").map(s => s.trim()).filter(Boolean);
      setInterestedModels(models);
      setModelInterest(models.join(", "));
    } else if (modelFromUrl) {
      setModelInterest(decodeURIComponent(modelFromUrl));
      setInterestedModels([decodeURIComponent(modelFromUrl)]);
    }

    const stored = localStorage.getItem("caractr_results");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        // Only pre-fill model from session if URL didn't provide one
        if (!modelFromUrl && !modelsFromUrl && parsed.recommendations?.[0]) {
          setModelInterest(parsed.recommendations[0].full_name);
        }
        if (parsed.answers?.p8_budget_max) {
          setBudgetMax(String(parsed.answers.p8_budget_max));
        }
        if (parsed.profile_narrative) {
          setProfileNarrative(parsed.profile_narrative);
        }
      } catch {}
    }
    // Extract model name from listing URL for context display
    if (listingUrl) {
      const slug = listingUrl.split("/").filter(Boolean).pop() || "";
      setListingModel(slug.replace(/-/g, " ").slice(0, 60));
    }
  }, [modelFromUrl, modelsFromUrl, listingUrl]);

  const toggleTag = (id: string) => {
    setSelectedTags((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  };

  const submit = async () => {
    if (!name.trim() || !email.trim()) {
      setError("Nome e email são obrigatórios.");
      return;
    }
    if (!consentCaractr) {
      setError("É necessário aceitar o contacto pela Caractr para continuar.");
      return;
    }
    setSending(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/concierge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id:       sessionId || null,
          name:             name.trim(),
          email:            email.trim(),
          model_interest:   modelInterest.trim() || null,
          model_ids:        modelIdsParam ? modelIdsParam.split(",").map(Number).filter(Boolean) : [],
          budget_max:       budgetMax ? parseInt(budgetMax) : null,
          feedback_tags:    selectedTags,
          consent_caractr:  consentCaractr,
          consent_dealer:   consentDealer,
          listing_url:      listingUrl || null,
          listing_verdict:  listingVerdict || null,
        }),
      });
      const result = await res.json();
      if (result.status === "ok") {
        setSubmitted(true);
      } else {
        setError(result.error || "Erro ao enviar. Tenta novamente.");
      }
    } catch {
      setError("Erro de ligação. Verifica a internet e tenta novamente.");
    } finally {
      setSending(false);
    }
  };

  if (submitted) {
    const firstName = name.split(" ")[0] || name;
    return (
      <main style={{
        minHeight: "100vh",
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        padding: "0 clamp(24px, 5vw, 64px)",
        background: "var(--bg)", color: "var(--fg)",
        textAlign: "center",
      }}>
        <div style={{ maxWidth: "480px", width: "100%" }}>
          <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "24px" }} />
          <h1 style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(36px, 7vw, 64px)",
            fontWeight: 800, letterSpacing: "-0.02em",
            lineHeight: 0.9, marginBottom: "20px",
          }}>
            RECEBIDO,<br />{firstName.toUpperCase()}.
          </h1>

          {/* What happens next */}
          <div style={{
            padding: "24px 28px", borderRadius: "16px",
            border: "1px solid var(--border)", background: "var(--surface)",
            marginBottom: "32px", textAlign: "left",
          }}>
            <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--accent)", textTransform: "uppercase", marginBottom: "18px" }}>
              O que acontece agora
            </p>
            {[
              "Vemos o teu perfil e os modelos que te interessam.",
              "Pesquisamos anúncios reais que se encaixam nas tuas prioridades.",
              "Entramos em contacto via email com uma shortlist curada.",
            ].map((step, i) => (
              <div key={i} style={{ display: "flex", gap: "16px", alignItems: "flex-start", marginBottom: i < 2 ? "14px" : 0 }}>
                <span style={{
                  fontFamily: "var(--font-mono)", fontSize: "11px",
                  color: "var(--accent)", flexShrink: 0, marginTop: "1px",
                }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <p style={{ fontSize: "14px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.6, fontWeight: 300 }}>
                  {step}
                </p>
              </div>
            ))}
          </div>

          <p style={{
            fontSize: "13px", color: "var(--muted)", opacity: 0.55,
            fontFamily: "var(--font-body)", marginBottom: "32px", lineHeight: 1.6,
          }}>
            Enviámos uma confirmação para <strong style={{ color: "var(--fg)", fontWeight: 400 }}>{email}</strong>.
          </p>

          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", justifyContent: "center" }}>
            <Link href="/resultados" className="pill-btn-ghost">
              ← shortlist
            </Link>
            <Link href="/analisar" className="pill-btn">
              analisar anúncio
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--fg)" }}>

      {/* ── Header ── */}
      <div style={{
        padding: "32px clamp(24px, 5vw, 64px) 24px",
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
        <Link href="/resultados" className="pill-btn-ghost" style={{ padding: "8px 20px", fontSize: "13px" }}>
          ← shortlist
        </Link>
      </div>

      <div style={{ maxWidth: "560px", margin: "0 auto", padding: "clamp(48px, 6vw, 64px) clamp(24px, 5vw, 32px)" }}>

        {/* Title */}
        <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "20px" }} />
        <h1 style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(32px, 5vw, 48px)",
          fontWeight: 800, letterSpacing: "-0.02em",
          lineHeight: 0.95, marginBottom: "14px",
        }}>
          QUERO AJUDA
        </h1>
        <p style={{
          fontSize: "15px", color: "var(--muted)",
          marginBottom: interestedModels.length > 0 ? "24px" : "48px",
          lineHeight: 1.7, fontWeight: 300, fontFamily: "var(--font-body)",
        }}>
          Pesquisamos anúncios reais que se adequam ao teu perfil e enviamos-te uma shortlist curada. Gratuito durante o lançamento.
        </p>

        {/* Interested models chips */}
        {interestedModels.length > 1 && (
          <div style={{ marginBottom: "32px" }}>
            <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "10px", opacity: 0.6 }}>
              Modelos com interesse
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              {interestedModels.map((m, i) => (
                <span key={i} style={{
                  fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--accent)",
                  border: "1px solid var(--accent)", borderRadius: "100px",
                  padding: "5px 14px", opacity: 0.8,
                }}>
                  {m}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── Profile card (Phase 4d) ── */}
        {profileNarrative && (
          <div style={{
            padding: "16px 20px",
            borderRadius: "12px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            marginBottom: "32px",
          }}>
            <p style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--accent)", textTransform: "uppercase", marginBottom: "10px" }}>
              Conhecemos o teu perfil
            </p>
            {profileNarrative.priorities && (
              <p style={{ fontSize: "13px", color: "var(--fg)", fontFamily: "var(--font-body)", lineHeight: 1.6, marginBottom: "4px" }}>
                {profileNarrative.priorities}
              </p>
            )}
            {profileNarrative.aversion && (
              <p style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", lineHeight: 1.5 }}>
                {profileNarrative.aversion}
              </p>
            )}
          </div>
        )}

        {/* ── Listing context banner (Phase 4e) ── */}
        {listingUrl && (
          <div style={{
            padding: "12px 16px",
            borderRadius: "10px",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            marginBottom: "32px",
            display: "flex", alignItems: "center", gap: "12px",
          }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px", color: "var(--muted)", textTransform: "uppercase" }}>
              Anúncio analisado
            </span>
            {listingVerdict && (
              <span style={{
                fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "1px",
                color: listingVerdict === "forte" ? "#4aa35a" : listingVerdict === "evitar" ? "#d23c3c" : "var(--accent)",
                fontWeight: 700, textTransform: "uppercase",
              }}>
                {listingVerdict.toUpperCase()}
              </span>
            )}
            {listingModel && (
              <span style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-body)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {listingModel}
              </span>
            )}
          </div>
        )}

        {/* ── Contact ── */}
        <div style={{ marginBottom: "40px" }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "2px", color: "var(--accent)", textTransform: "uppercase", marginBottom: "16px" }}>
            Os teus dados
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "10px", marginBottom: "10px" }}>
            <div>
              <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px", opacity: 0.6 }}>
                Nome *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="O teu nome"
                style={inputStyle}
                onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
                onBlur={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
              />
            </div>
            <div>
              <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px", opacity: 0.6 }}>
                Email *
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="o-teu@email.pt"
                style={inputStyle}
                onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
                onBlur={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
              />
            </div>
          </div>
        </div>

        {/* ── Model & budget ── */}
        <div style={{ marginBottom: "40px" }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "2px", color: "var(--accent)", textTransform: "uppercase", marginBottom: "16px" }}>
            O que procuras
          </p>
          <div style={{ marginBottom: "10px" }}>
            <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px", opacity: 0.6 }}>
              Modelo de interesse
            </label>
            <input
              type="text"
              value={modelInterest}
              onChange={(e) => setModelInterest(e.target.value)}
              placeholder="ex: BMW Série 3, Mazda CX-5..."
              style={inputStyle}
              onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
              onBlur={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
            />
          </div>
          <div>
            <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1px", color: "var(--muted)", textTransform: "uppercase", marginBottom: "8px", opacity: 0.6 }}>
              Orçamento máximo (EUR)
            </label>
            <input
              type="number"
              value={budgetMax}
              onChange={(e) => setBudgetMax(e.target.value)}
              placeholder="ex: 25000"
              style={inputStyle}
              onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
              onBlur={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
            />
          </div>
        </div>

        {/* ── Feedback chips ── */}
        <div style={{ marginBottom: "40px" }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "2px", color: "var(--accent)", textTransform: "uppercase", marginBottom: "6px" }}>
            A recomendação não está certa? (opcional)
          </p>
          <p style={{ fontSize: "13px", color: "var(--muted)", fontFamily: "var(--font-body)", marginBottom: "16px", opacity: 0.7 }}>
            Seleciona o que não se adequa — ajuda-nos a afinar.
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {FEEDBACK_TAGS.map((tag) => {
              const active = selectedTags.includes(tag.id);
              return (
                <button
                  key={tag.id}
                  onClick={() => toggleTag(tag.id)}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "100px",
                    border: `1px solid ${active ? "var(--accent)" : "var(--border)"}`,
                    background: active ? "rgba(200,168,130,0.08)" : "transparent",
                    color: active ? "var(--accent)" : "var(--muted)",
                    fontSize: "12px",
                    fontFamily: "var(--font-body)",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  {tag.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Consent ── */}
        <div style={{ marginBottom: "40px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "2px", color: "var(--accent)", textTransform: "uppercase", marginBottom: "4px" }}>
            Consentimento (RGPD)
          </p>

          {[
            {
              key: "caractr",
              checked: consentCaractr,
              onChange: setConsentCaractr,
              required: true,
              label: "Aceito ser contactado pela equipa Caractr relativamente ao meu pedido.",
            },
            {
              key: "dealer",
              checked: consentDealer,
              onChange: setConsentDealer,
              required: false,
              label: "Aceito receber propostas de dealers parceiros da Caractr com base no meu perfil de comprador.",
            },
          ].map((c) => (
            <label
              key={c.key}
              style={{
                display: "flex", gap: "12px", alignItems: "flex-start",
                cursor: "pointer",
              }}
            >
              <div
                onClick={() => c.onChange(!c.checked)}
                style={{
                  marginTop: "2px",
                  flexShrink: 0,
                  width: "18px", height: "18px",
                  borderRadius: "4px",
                  border: `1px solid ${c.checked ? "var(--accent)" : "var(--border)"}`,
                  background: c.checked ? "var(--accent)" : "transparent",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "all 0.15s ease",
                  cursor: "pointer",
                }}
              >
                {c.checked && (
                  <span style={{ color: "var(--bg)", fontSize: "11px", lineHeight: 1 }}>✓</span>
                )}
              </div>
              <span style={{
                fontSize: "13px", color: "var(--muted)",
                fontFamily: "var(--font-body)", lineHeight: 1.6,
              }}>
                {c.label}
                {c.required && <span style={{ color: "var(--accent)", marginLeft: "4px" }}>*</span>}
                {c.key === "caractr" && (
                  <> (<a href="/privacidade" target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-dark)", textDecoration: "underline", fontSize: "12px" }}>Política de Privacidade</a>)</>
                )}
              </span>
            </label>
          ))}
        </div>

        {error && (
          <p style={{ marginBottom: "16px", fontSize: "13px", color: "#d23c3c", fontFamily: "var(--font-body)" }}>
            {error}
          </p>
        )}

        <button
          onClick={submit}
          disabled={sending || !consentCaractr}
          className="pill-btn-solid"
          style={{
            opacity: (sending || !consentCaractr) ? 0.4 : 1,
            cursor: (sending || !consentCaractr) ? "not-allowed" : "pointer",
          }}
        >
          {sending ? "A enviar..." : "Enviar pedido"}
        </button>

        <p style={{
          marginTop: "20px", fontSize: "11px",
          color: "var(--muted)", fontFamily: "var(--font-body)",
          lineHeight: 1.6, opacity: 0.4,
        }}>
          Os teus dados são usados exclusivamente para os fins indicados acima.
          Nunca são partilhados sem consentimento explícito.
        </p>
      </div>
    </main>
  );
}

export default function ConciergePage() {
  return (
    <Suspense fallback={
      <main style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
        <p style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)", letterSpacing: "1px" }}>A CARREGAR...</p>
      </main>
    }>
      <ConciergeContent />
    </Suspense>
  );
}
