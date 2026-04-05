"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[Caractr] Unhandled error:", error);
  }, [error]);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg-dark)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "48px 24px",
        textAlign: "center",
        fontFamily: "var(--font-body)",
      }}
    >
      <p style={{ color: "var(--accent)", fontSize: "13px", letterSpacing: "0.12em", marginBottom: "24px" }}>
        ALGO CORREU MAL
      </p>
      <h1
        style={{
          color: "var(--text-light)",
          fontSize: "clamp(28px, 5vw, 48px)",
          fontFamily: "var(--font-display)",
          fontWeight: 900,
          lineHeight: 1,
          marginBottom: "20px",
        }}
      >
        ERRO INESPERADO
      </h1>
      <p
        style={{
          color: "rgba(245,240,230,0.55)",
          fontSize: "16px",
          maxWidth: "400px",
          lineHeight: 1.6,
          marginBottom: "40px",
        }}
      >
        Ocorreu um erro que não conseguimos prever. Tenta novamente — se o problema persistir, contacta-nos.
      </p>
      <button
        onClick={reset}
        style={{
          background: "var(--accent)",
          color: "var(--bg-dark)",
          border: "none",
          borderRadius: "100px",
          padding: "14px 32px",
          fontSize: "14px",
          fontWeight: 700,
          cursor: "pointer",
          letterSpacing: "0.05em",
        }}
      >
        Tentar novamente
      </button>
    </div>
  );
}
