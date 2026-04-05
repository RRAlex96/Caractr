"use client";
import { useEffect } from "react";
export default function AnalisarError({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => { console.error("[Caractr/analisar]", error); }, [error]);
  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-dark)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "48px 24px", textAlign: "center", fontFamily: "var(--font-body)" }}>
      <p style={{ color: "var(--accent)", fontSize: "13px", letterSpacing: "0.12em", marginBottom: "20px" }}>ALGO CORREU MAL</p>
      <h2 style={{ color: "var(--text-light)", fontSize: "clamp(24px, 4vw, 40px)", fontFamily: "var(--font-display)", fontWeight: 900, marginBottom: "16px" }}>ERRO NA ANÁLISE</h2>
      <p style={{ color: "rgba(245,240,230,0.55)", fontSize: "15px", maxWidth: "360px", lineHeight: 1.6, marginBottom: "36px" }}>Não conseguimos analisar o anúncio. Verifica o link e tenta novamente.</p>
      <button onClick={reset} style={{ background: "var(--accent)", color: "var(--bg-dark)", border: "none", borderRadius: "100px", padding: "13px 28px", fontSize: "14px", fontWeight: 700, cursor: "pointer" }}>Tentar novamente</button>
    </div>
  );
}
