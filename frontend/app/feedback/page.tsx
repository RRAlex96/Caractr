"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Analytics } from "@/lib/analytics";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function FeedbackContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session") || "";
  const [data, setData] = useState<any>(null);
  const [satisfaction, setSatisfaction] = useState<string | null>(null);
  const [preferredModel, setPreferredModel] = useState<number | null>(null);
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("caractr_results");
    if (stored) setData(JSON.parse(stored));
  }, []);

  const submit = async () => {
    setSending(true);
    try {
      await fetch(`${API}/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, satisfaction, preferred_model_id: preferredModel, email: email || null }),
      });
      // Track feedback submitted
      Analytics.feedbackSubmitted(
        sessionId,
        satisfaction || "",
        preferredModel ?? undefined,
        !!email,
      );
      setSubmitted(true);
    } catch (err) {
      console.error("Feedback error:", err);
    } finally {
      setSending(false);
    }
  };

  const recs = data?.recommendations || [];

  if (submitted) {
    return (
      <main style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 clamp(24px, 5vw, 64px)",
        background: "var(--bg)",
        color: "var(--fg)",
      }}>
        <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "24px" }} />
        <h1 style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(36px, 7vw, 72px)",
          fontWeight: 800,
          letterSpacing: "-0.02em",
          lineHeight: 0.88,
          textAlign: "center",
          marginBottom: "24px",
        }}>
          OBRIGADO
        </h1>
        <p style={{
          fontSize: "15px",
          color: "var(--muted)",
          textAlign: "center",
          maxWidth: "400px",
          lineHeight: 1.7,
          fontWeight: 300,
          fontFamily: "var(--font-body)",
        }}>
          O teu feedback ajuda-nos a melhorar o Caractr para ti e para todos.
          {email && " Avisamos-te quando estivermos prontos."}
        </p>
        <div style={{ marginTop: "48px" }}>
          <Link href="/" className="pill-btn-ghost">voltar ao início</Link>
        </div>
      </main>
    );
  }

  return (
    <main style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--fg)" }}>
      {/* ── Header ── */}
      <div style={{
        padding: "32px clamp(24px, 5vw, 64px) 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid var(--border)",
      }}>
        <Link
          href="/"
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "14px",
            fontWeight: 700,
            letterSpacing: "0.12em",
            color: "var(--fg)",
            textDecoration: "none",
          }}
        >
          CARACTR
        </Link>
        <Link href="/resultados" className="pill-btn-ghost" style={{ padding: "8px 20px", fontSize: "13px" }}>
          voltar aos resultados
        </Link>
      </div>

      {/* ── Form content ── */}
      <div style={{ maxWidth: "540px", margin: "0 auto", padding: "clamp(48px, 6vw, 64px) clamp(24px, 5vw, 32px)" }}>
        {/* Accent line + title */}
        <div style={{ width: "48px", height: "2px", background: "var(--accent)", borderRadius: "1px", marginBottom: "20px" }} />
        <h1 style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(32px, 5vw, 56px)",
          fontWeight: 800,
          letterSpacing: "-0.02em",
          lineHeight: 0.95,
          marginBottom: "14px",
        }}>
          O QUE ACHASTE?
        </h1>
        <p style={{
          fontSize: "15px",
          color: "var(--muted)",
          marginBottom: "52px",
          lineHeight: 1.7,
          fontWeight: 300,
          fontFamily: "var(--font-body)",
        }}>
          Tudo opcional. Demora 30 segundos. Ajuda-nos a melhorar.
        </p>

        {/* ── Satisfaction ── */}
        <div style={{ marginBottom: "56px" }}>
          <p style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            letterSpacing: "2px",
            color: "var(--accent)",
            textTransform: "uppercase",
            marginBottom: "16px",
          }}>
            Isto fez sentido para ti?
          </p>
          <div style={{ display: "flex", gap: "10px" }}>
            {[
              { value: "sim", label: "Sim" },
              { value: "mais_ou_menos", label: "Mais ou menos" },
              { value: "nao", label: "Não" },
            ].map((opt) => {
              const selected = satisfaction === opt.value;
              return (
                <button
                  key={opt.value}
                  onClick={() => setSatisfaction(opt.value)}
                  style={{
                    flex: 1,
                    padding: "14px 0",
                    borderRadius: "100px",
                    border: "1px solid",
                    fontSize: "14px",
                    fontWeight: 500,
                    fontFamily: "var(--font-body)",
                    borderColor: selected ? "var(--accent)" : "var(--border)",
                    background: selected ? "rgba(200,168,130,0.08)" : "transparent",
                    color: selected ? "var(--accent)" : "var(--muted)",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    textAlign: "center",
                  }}
                  onMouseEnter={(e) => {
                    if (!selected) {
                      e.currentTarget.style.borderColor = "var(--fg)";
                      e.currentTarget.style.color = "var(--fg)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!selected) {
                      e.currentTarget.style.borderColor = "var(--border)";
                      e.currentTarget.style.color = "var(--muted)";
                    }
                  }}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Preferred model ── */}
        <div style={{ marginBottom: "56px" }}>
          <p style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            letterSpacing: "2px",
            color: "var(--accent)",
            textTransform: "uppercase",
            marginBottom: "16px",
          }}>
            Qual te interessou mais?
          </p>
          <div style={{ borderTop: "1px solid var(--border)" }}>
            {[...recs, { model_id: -1, rank: "—", full_name: "Nenhum me interessou" }].map((rec: any, idx: number) => {
              const selected = preferredModel === rec.model_id;
              return (
                <button
                  key={rec.model_id}
                  onClick={() => setPreferredModel(rec.model_id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "16px",
                    width: "100%",
                    textAlign: "left",
                    padding: "16px 0",
                    background: "none",
                    border: "none",
                    borderBottom: "1px solid var(--border)",
                    cursor: "pointer",
                  }}
                  onMouseEnter={(e) => {
                    if (!selected) {
                      const label = e.currentTarget.querySelector('[data-label]') as HTMLElement;
                      if (label) label.style.transform = "translateX(6px)";
                      const line = e.currentTarget.querySelector('[data-line]') as HTMLElement;
                      if (line) line.style.width = "20px";
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
                    fontFamily: "var(--font-mono)",
                    fontSize: "10px",
                    color: selected ? "var(--accent)" : "var(--muted)",
                    flexShrink: 0,
                    width: "16px",
                    transition: "color 0.2s ease",
                  }}>
                    {rec.model_id === -1 ? "—" : `#${rec.rank || idx + 1}`}
                  </span>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1 }}>
                    <div
                      data-line
                      style={{
                        width: selected ? "20px" : "0px",
                        height: "2px",
                        background: "var(--accent)",
                        borderRadius: "1px",
                        transition: "width 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
                        flexShrink: 0,
                      }}
                    />
                    <span
                      data-label
                      style={{
                        fontFamily: "var(--font-body)",
                        fontSize: "15px",
                        fontWeight: rec.model_id === -1 ? 300 : 500,
                        color: rec.model_id === -1 ? "var(--muted)" : "var(--fg)",
                        transition: "transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
                      }}
                    >
                      {rec.full_name}
                    </span>
                  </div>
                  <div style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    background: selected ? "var(--accent)" : "transparent",
                    border: selected ? "none" : "1px solid var(--border)",
                    flexShrink: 0,
                    transition: "all 0.2s ease",
                  }} />
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Email ── */}
        <div style={{ marginBottom: "56px" }}>
          <p style={{
            fontFamily: "var(--font-mono)",
            fontSize: "10px",
            letterSpacing: "2px",
            color: "var(--accent)",
            textTransform: "uppercase",
            marginBottom: "16px",
          }}>
            Queres que te avisemos?
          </p>
          <input
            type="email"
            placeholder="o-teu@email.pt"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{
              width: "100%",
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
              boxSizing: "border-box",
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
            onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
          />
          <p style={{ fontSize: "12px", color: "var(--muted)", opacity: 0.5, marginTop: "8px", fontWeight: 300, fontFamily: "var(--font-body)" }}>
            Sem spam. Só um aviso quando lançarmos.
          </p>
        </div>

        {/* Submit */}
        <button
          onClick={submit}
          disabled={sending}
          className="pill-btn-solid"
          style={{ opacity: sending ? 0.5 : 1, cursor: sending ? "wait" : "pointer" }}
        >
          {sending ? "a enviar..." : "enviar feedback"}
        </button>
      </div>
    </main>
  );
}

export default function FeedbackPage() {
  return (
    <Suspense fallback={
      <main style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
        <p style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)", letterSpacing: "1px" }}>A CARREGAR...</p>
      </main>
    }>
      <FeedbackContent />
    </Suspense>
  );
}
