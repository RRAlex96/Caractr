"use client";

/**
 * TrustPanel — Caractr data credibility block
 *
 * Shows three sections for a recommended model:
 *   1. Fiabilidade — Bayesian score + 90% CI bar + data_quality badge
 *   2. Preço Justo — p50 + band + sample freshness (when market data exists)
 *   3. Verificação — checklist items the buyer should confirm
 *
 * Honesty principle: all data_quality labels are always shown, never hidden.
 * A wide CI with "Estimativa" is better than a falsely precise number.
 */

import React, { useState } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface ReliabilityData {
  score: number;       // 1–10
  ci_low: number;      // 1–10
  ci_high: number;     // 1–10
  data_quality: "prior_only" | "limited" | "robust";
}

interface MarketBand {
  p10?: number;
  p90?: number;
  sample_count?: number;
}

interface MarketData {
  p50: number;
  band?: MarketBand | null;
  as_of?: string | null;
}

interface TrustPanelProps {
  reliability?: ReliabilityData | null;
  market?: MarketData | null;
  modelName?: string;
  onViewDetails?: () => void;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const DATA_QUALITY_LABELS: Record<string, { label: string; color: string; hint: string }> = {
  robust:     { label: "Dados robustos",  color: "#22c55e", hint: "Múltiplas fontes independentes" },
  limited:    { label: "Dados limitados", color: "#f59e0b", hint: "Poucas fontes disponíveis" },
  prior_only: { label: "Estimativa",      color: "#94a3b8", hint: "Sem dados de incidentes disponíveis — baseado em padrões estatísticos do segmento" },
};

function formatPrice(v: number): string {
  return v.toLocaleString("pt-PT") + " €";
}

function freshnessLabel(asOf: string | null | undefined): string {
  if (!asOf) return "";
  try {
    const d = new Date(asOf);
    const now = new Date();
    const days = Math.round((now.getTime() - d.getTime()) / 86400000);
    if (days <= 35) return `dados de ${days < 7 ? "esta semana" : "este mês"}`;
    const months = Math.round(days / 30);
    return `dados de há ${months} ${months === 1 ? "mês" : "meses"}`;
  } catch {
    return "";
  }
}

// CI bar: maps a score on [1,10] to a percentage [0,100] of the bar width
function toBarPct(v: number): number {
  return Math.round(((v - 1) / 9) * 100);
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ReliabilityBlock({ reliability }: { reliability: ReliabilityData }) {
  const qMeta = DATA_QUALITY_LABELS[reliability.data_quality] ?? DATA_QUALITY_LABELS.prior_only;
  const scorePct  = toBarPct(reliability.score);
  const lowPct    = toBarPct(reliability.ci_low);
  const highPct   = toBarPct(reliability.ci_high);
  const ciWidthPct = highPct - lowPct;

  return (
    <div>
      {/* Score + label row */}
      <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "10px" }}>
        <span style={{
          fontFamily: "var(--font-mono)",
          fontSize: "28px",
          fontWeight: 700,
          color: "var(--fg)",
          letterSpacing: "-0.02em",
        }}>
          {reliability.score.toFixed(1)}
        </span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--muted)", opacity: 0.6 }}>
          / 10
        </span>
        <span style={{
          marginLeft: "auto",
          fontFamily: "var(--font-mono)",
          fontSize: "10px",
          letterSpacing: "0.08em",
          color: qMeta.color,
          textTransform: "uppercase",
          padding: "3px 8px",
          border: `1px solid ${qMeta.color}40`,
          borderRadius: "4px",
        }}>
          {qMeta.label}
        </span>
      </div>

      {/* CI bar */}
      <div style={{ position: "relative", height: "6px", background: "var(--border)", borderRadius: "3px", marginBottom: "6px" }}>
        {/* CI range band */}
        <div style={{
          position: "absolute",
          left: `${lowPct}%`,
          width: `${ciWidthPct}%`,
          height: "100%",
          background: `${qMeta.color}50`,
          borderRadius: "3px",
        }} />
        {/* Point estimate marker */}
        <div style={{
          position: "absolute",
          left: `${scorePct}%`,
          top: "-3px",
          width: "4px",
          height: "12px",
          background: qMeta.color,
          borderRadius: "2px",
          transform: "translateX(-50%)",
        }} />
      </div>

      {/* CI label */}
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", opacity: 0.55 }}>
        <span>IC 90%: {reliability.ci_low.toFixed(1)} — {reliability.ci_high.toFixed(1)}</span>
        <span>{qMeta.hint}</span>
      </div>
    </div>
  );
}

function MarketBlock({ market }: { market: MarketData }) {
  const freshness = freshnessLabel(market.as_of);
  const p10 = market.band?.p10;
  const p90 = market.band?.p90;
  const sampleCount = market.band?.sample_count;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "10px" }}>
        <span style={{
          fontFamily: "var(--font-mono)",
          fontSize: "22px",
          fontWeight: 700,
          color: "var(--fg)",
        }}>
          {formatPrice(market.p50)}
        </span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", opacity: 0.6 }}>
          mediana
        </span>
        {sampleCount && (
          <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--accent)" }}>
            {sampleCount} anúncios
          </span>
        )}
      </div>

      {p10 && p90 && (
        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)", opacity: 0.7 }}>
            {formatPrice(p10)}
          </span>
          <div style={{ flex: 1, height: "4px", background: "var(--border)", borderRadius: "2px", position: "relative" }}>
            <div style={{
              position: "absolute",
              left: "10%",
              right: "10%",
              height: "100%",
              background: "var(--accent)",
              opacity: 0.4,
              borderRadius: "2px",
            }} />
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)", opacity: 0.7 }}>
            {formatPrice(p90)}
          </span>
        </div>
      )}

      {freshness && (
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", opacity: 0.5 }}>
          {freshness}
        </span>
      )}
    </div>
  );
}

function VerificationBlock({ modelName }: { modelName?: string }) {
  const items = [
    { id: "recalls", label: "Verificar recalls ativos (VIN check)" },
    { id: "inspection", label: "Inspeção independente por mecânico" },
    { id: "history", label: "Histórico de manutenção documentado" },
    { id: "vin", label: "Verificação de VIN (roubo / acidente)" },
  ];

  const [checked, setChecked] = useState<Set<string>>(new Set());

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      {items.map((item) => (
        <label
          key={item.id}
          style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer" }}
          onClick={() => setChecked(prev => {
            const next = new Set(prev);
            next.has(item.id) ? next.delete(item.id) : next.add(item.id);
            return next;
          })}
        >
          <div style={{
            width: "16px",
            height: "16px",
            borderRadius: "3px",
            border: `1px solid ${checked.has(item.id) ? "var(--accent)" : "var(--border)"}`,
            background: checked.has(item.id) ? "var(--accent)" : "transparent",
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.15s ease",
          }}>
            {checked.has(item.id) && (
              <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                <path d="M1 4L3.5 6.5L9 1" stroke="var(--bg)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </div>
          <span style={{
            fontFamily: "var(--font-body)",
            fontSize: "13px",
            color: checked.has(item.id) ? "var(--muted)" : "var(--fg)",
            textDecoration: checked.has(item.id) ? "line-through" : "none",
            transition: "all 0.15s ease",
            fontWeight: 300,
          }}>
            {item.label}
          </span>
        </label>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function TrustPanel({ reliability, market, modelName }: TrustPanelProps) {
  const hasAnyData = reliability || market;
  if (!hasAnyData) return null;

  const sectionStyle: React.CSSProperties = {
    borderTop: "1px solid var(--border)",
    paddingTop: "16px",
    marginTop: "16px",
  };

  const labelStyle: React.CSSProperties = {
    fontFamily: "var(--font-mono)",
    fontSize: "10px",
    letterSpacing: "0.12em",
    color: "var(--muted)",
    opacity: 0.55,
    textTransform: "uppercase",
    marginBottom: "12px",
    display: "block",
  };

  return (
    <div style={{
      borderTop: "1px solid var(--border)",
      paddingTop: "20px",
      marginTop: "20px",
    }}>
      {/* Header */}
      <span style={{
        fontFamily: "var(--font-mono)",
        fontSize: "10px",
        letterSpacing: "0.15em",
        color: "var(--accent)",
        textTransform: "uppercase",
        display: "block",
        marginBottom: "16px",
        opacity: 0.8,
      }}>
        Dados de confiança
      </span>

      {/* Reliability */}
      {reliability && (
        <div style={sectionStyle}>
          <span style={labelStyle}>Fiabilidade</span>
          <ReliabilityBlock reliability={reliability} />
        </div>
      )}

      {/* Market price */}
      {market && (
        <div style={sectionStyle}>
          <span style={labelStyle}>Preço de mercado</span>
          <MarketBlock market={market} />
        </div>
      )}

      {/* Verification checklist */}
      <div style={sectionStyle}>
        <span style={labelStyle}>Verificação antes de comprar</span>
        <VerificationBlock modelName={modelName} />
      </div>
    </div>
  );
}
