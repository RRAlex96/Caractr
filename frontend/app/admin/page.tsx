"use client";

import { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TIER_COLORS: Record<string, string> = {
  forte: "#4aa35a",
  razoavel: "var(--accent)",
  cuidado: "#dca028",
  evitar: "#d23c3c",
};

// ── Reusable styles ──────────────────────────────────────────────────────────

const sectionLabel: React.CSSProperties = {
  fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "2px",
  color: "var(--accent)", textTransform: "uppercase", marginBottom: "16px",
};

const cardStyle: React.CSSProperties = {
  padding: "20px 24px", borderRadius: "14px",
  border: "1px solid var(--border)", background: "var(--surface)",
};

const statNumber: React.CSSProperties = {
  fontFamily: "var(--font-display)", fontSize: "28px", fontWeight: 700,
  color: "var(--fg)", lineHeight: 1,
};

const statLabel: React.CSSProperties = {
  fontFamily: "var(--font-mono)", fontSize: "9px", letterSpacing: "1.5px",
  color: "var(--muted)", textTransform: "uppercase", marginTop: "6px",
};

// ── Components ───────────────────────────────────────────────────────────────

function OverviewCards({ data }: { data: any }) {
  const cards = [
    { value: data.unique_users, label: "Utilizadores" },
    { value: data.sessions_started, label: "Wizards iniciados" },
    { value: data.sessions_completed, label: "Wizards completos" },
    { value: data.analyses_requested, label: "Analises pedidas" },
    { value: data.concierge_submissions, label: "Concierge" },
  ];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "12px", marginBottom: "32px" }}>
      {cards.map((c, i) => (
        <div key={i} style={cardStyle}>
          <div style={statNumber}>{(c.value ?? 0).toLocaleString()}</div>
          <div style={statLabel}>{c.label}</div>
        </div>
      ))}
    </div>
  );
}

function FunnelChart({ steps }: { steps: any[] }) {
  const maxCount = steps[0]?.count || 1;
  return (
    <div style={{ ...cardStyle, marginBottom: "32px" }}>
      <div style={sectionLabel}>Funil de conversao</div>
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {steps.map((step: any, i: number) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", width: "140px", flexShrink: 0, textAlign: "right" }}>
              {step.label}
            </div>
            <div style={{ flex: 1, height: "24px", background: "var(--border)", borderRadius: "4px", overflow: "hidden", position: "relative" }}>
              <div style={{
                width: `${Math.max(2, (step.count / maxCount) * 100)}%`,
                height: "100%",
                background: "var(--accent)",
                opacity: 1 - (i * 0.1),
                borderRadius: "4px",
                transition: "width 0.5s ease",
              }} />
            </div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--fg)", width: "50px", textAlign: "right", flexShrink: 0 }}>
              {step.count}
            </div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", width: "50px", flexShrink: 0 }}>
              {step.pct_of_start}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DailyTrend({ data }: { data: any[] }) {
  if (!data || data.length < 2) return null;
  const W = 500, H = 140, PAD = 30;
  const maxEvents = Math.max(...data.map(d => d.events), 1);
  const maxUsers = Math.max(...data.map(d => d.users), 1);

  const eventsPoints = data.map((d, i) => {
    const x = PAD + (i / (data.length - 1)) * (W - PAD * 2);
    const y = H - PAD - ((d.events / maxEvents) * (H - PAD * 2));
    return `${x},${y}`;
  }).join(" ");

  const usersPoints = data.map((d, i) => {
    const x = PAD + (i / (data.length - 1)) * (W - PAD * 2);
    const y = H - PAD - ((d.users / maxUsers) * (H - PAD * 2));
    return `${x},${y}`;
  }).join(" ");

  return (
    <div style={{ ...cardStyle, marginBottom: "32px" }}>
      <div style={sectionLabel}>Tendencia diaria</div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", maxWidth: "600px" }}>
        <polyline points={eventsPoints} fill="none" stroke="var(--accent)" strokeWidth="2" opacity="0.8" />
        <polyline points={usersPoints} fill="none" stroke="#4aa35a" strokeWidth="2" opacity="0.6" />
        {/* X axis labels */}
        <text x={PAD} y={H - 5} fill="var(--muted)" fontSize="9" fontFamily="var(--font-mono)">{data[0]?.day?.slice(5)}</text>
        <text x={W - PAD} y={H - 5} fill="var(--muted)" fontSize="9" fontFamily="var(--font-mono)" textAnchor="end">{data[data.length - 1]?.day?.slice(5)}</text>
        {/* Legend */}
        <line x1={PAD} y1="12" x2={PAD + 20} y2="12" stroke="var(--accent)" strokeWidth="2" />
        <text x={PAD + 25} y="15" fill="var(--muted)" fontSize="9" fontFamily="var(--font-mono)">eventos</text>
        <line x1={PAD + 85} y1="12" x2={PAD + 105} y2="12" stroke="#4aa35a" strokeWidth="2" />
        <text x={PAD + 110} y="15" fill="var(--muted)" fontSize="9" fontFamily="var(--font-mono)">utilizadores</text>
      </svg>
    </div>
  );
}

function TopModels({ recommended, analysed }: { recommended: any[]; analysed: any[] }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "32px" }}>
      <div style={cardStyle}>
        <div style={sectionLabel}>Top recomendados</div>
        {(recommended || []).slice(0, 8).map((m: any, i: number) => (
          <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: i < 7 ? "1px solid var(--border)" : "none" }}>
            <span style={{ fontFamily: "var(--font-body)", fontSize: "13px", color: "var(--fg)" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", marginRight: "8px" }}>{i + 1}.</span>
              {m.name}
            </span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)" }}>{m.count}x</span>
          </div>
        ))}
        {(!recommended || recommended.length === 0) && <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)" }}>Sem dados</div>}
      </div>
      <div style={cardStyle}>
        <div style={sectionLabel}>Top analisados</div>
        {(analysed || []).slice(0, 8).map((m: any, i: number) => (
          <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: i < 7 ? "1px solid var(--border)" : "none" }}>
            <span style={{ fontFamily: "var(--font-body)", fontSize: "13px", color: "var(--fg)" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", marginRight: "8px" }}>{i + 1}.</span>
              {m.name}
            </span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)" }}>{m.count}x</span>
          </div>
        ))}
        {(!analysed || analysed.length === 0) && <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)" }}>Sem dados</div>}
      </div>
    </div>
  );
}

function AnalysisStats({ stats }: { stats: any }) {
  const tiers = stats?.tiers || {};
  const total = Object.values(tiers).reduce((a: number, b: any) => a + (b || 0), 0) as number;
  return (
    <div style={cardStyle}>
      <div style={sectionLabel}>Analises</div>
      <div style={{ display: "flex", gap: "24px", marginBottom: "16px" }}>
        <div>
          <div style={{ ...statNumber, fontSize: "22px" }}>{stats?.total ?? 0}</div>
          <div style={statLabel}>Total</div>
        </div>
        <div>
          <div style={{ ...statNumber, fontSize: "22px" }}>{stats?.avg_deal_score ?? 0}</div>
          <div style={statLabel}>Score medio</div>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        {(["forte", "razoavel", "cuidado", "evitar"] as const).map(tier => (
          <div key={tier} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: TIER_COLORS[tier], width: "70px" }}>
              {tier.toUpperCase()}
            </div>
            <div style={{ flex: 1, height: "14px", background: "var(--border)", borderRadius: "3px", overflow: "hidden" }}>
              <div style={{
                width: `${total > 0 ? ((tiers[tier] || 0) / total) * 100 : 0}%`,
                height: "100%", background: TIER_COLORS[tier], borderRadius: "3px", opacity: 0.7,
              }} />
            </div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", width: "30px", textAlign: "right" }}>
              {tiers[tier] || 0}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function BudgetDist({ data }: { data: any[] }) {
  const max = Math.max(...(data || []).map(d => d.count), 1);
  return (
    <div style={cardStyle}>
      <div style={sectionLabel}>Orcamento</div>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {(data || []).map((b: any, i: number) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", width: "50px", textAlign: "right" }}>{b.bucket}</div>
            <div style={{ flex: 1, height: "16px", background: "var(--border)", borderRadius: "3px", overflow: "hidden" }}>
              <div style={{ width: `${(b.count / max) * 100}%`, height: "100%", background: "var(--accent)", borderRadius: "3px", opacity: 0.6 }} />
            </div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", width: "30px", textAlign: "right" }}>{b.count}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FeedbackSection({ data }: { data: any }) {
  const sat = data?.satisfaction || {};
  const totalSat = Object.values(sat).reduce((a: number, b: any) => a + (b || 0), 0) as number;
  const helpful = data?.analysis_helpful ?? 0;
  const notHelpful = data?.analysis_not_helpful ?? 0;
  const totalHelp = helpful + notHelpful;
  return (
    <div style={cardStyle}>
      <div style={sectionLabel}>Feedback</div>
      {totalSat > 0 && (
        <div style={{ marginBottom: "16px" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "8px" }}>
            Satisfacao ({totalSat})
          </div>
          {Object.entries(sat).map(([key, count]: [string, any]) => (
            <div key={key} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", width: "80px" }}>{key}</div>
              <div style={{ flex: 1, height: "12px", background: "var(--border)", borderRadius: "3px", overflow: "hidden" }}>
                <div style={{ width: `${(count / totalSat) * 100}%`, height: "100%", background: "var(--accent)", borderRadius: "3px", opacity: 0.5 }} />
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", width: "25px", textAlign: "right" }}>{count}</div>
            </div>
          ))}
        </div>
      )}
      {totalHelp > 0 && (
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "8px" }}>
            Analise util? ({totalHelp})
          </div>
          <div style={{ display: "flex", gap: "16px" }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: "var(--font-display)", fontSize: "20px", color: "#4aa35a" }}>{helpful}</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)" }}>SIM</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: "var(--font-display)", fontSize: "20px", color: "#d23c3c" }}>{notHelpful}</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)" }}>NAO</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: "var(--font-display)", fontSize: "20px", color: "var(--accent)" }}>
                {totalHelp > 0 ? Math.round((helpful / totalHelp) * 100) : 0}%
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)" }}>TAXA</div>
            </div>
          </div>
        </div>
      )}
      {totalSat === 0 && totalHelp === 0 && (
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)" }}>Sem feedback no periodo</div>
      )}
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function AdminDashboard() {
  const [token, setToken] = useState("");
  const [tokenInput, setTokenInput] = useState("");
  const [period, setPeriod] = useState("30d");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load token from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("caractr_admin_token");
    if (saved) setToken(saved);
  }, []);

  // Fetch dashboard data
  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError("");
    fetch(`${API}/api/admin/dashboard?period=${period}`, {
      headers: { "X-Admin-Token": token },
    })
      .then(r => {
        if (r.status === 403) throw new Error("Token invalido");
        if (!r.ok) throw new Error(`Erro ${r.status}`);
        return r.json();
      })
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [token, period]);

  const handleTokenSubmit = () => {
    if (tokenInput.trim()) {
      localStorage.setItem("caractr_admin_token", tokenInput.trim());
      setToken(tokenInput.trim());
    }
  };

  // ── Token gate ──
  if (!token) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
        <div style={{ ...cardStyle, width: "360px", textAlign: "center" }}>
          <div style={{ fontFamily: "var(--font-display)", fontSize: "14px", fontWeight: 700, letterSpacing: "0.12em", color: "var(--fg)", marginBottom: "24px" }}>
            CARACTR ADMIN
          </div>
          <input
            type="password"
            placeholder="Admin token"
            value={tokenInput}
            onChange={e => setTokenInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleTokenSubmit()}
            style={{
              width: "100%", padding: "12px 16px", borderRadius: "8px",
              border: "1px solid var(--border)", background: "var(--bg)",
              color: "var(--fg)", fontFamily: "var(--font-mono)", fontSize: "13px",
              outline: "none", marginBottom: "12px", boxSizing: "border-box",
            }}
          />
          <button
            onClick={handleTokenSubmit}
            style={{
              width: "100%", padding: "12px", borderRadius: "8px",
              border: "none", background: "var(--fg)", color: "var(--bg)",
              fontFamily: "var(--font-mono)", fontSize: "11px", letterSpacing: "1.5px",
              textTransform: "uppercase", cursor: "pointer",
            }}
          >
            Entrar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", padding: "32px 24px" }}>
      <div style={{ maxWidth: "960px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" }}>
          <div>
            <span style={{ fontFamily: "var(--font-display)", fontSize: "14px", fontWeight: 700, letterSpacing: "0.12em", color: "var(--fg)" }}>
              CARACTR
            </span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)", marginLeft: "10px", letterSpacing: "1px" }}>
              ADMIN
            </span>
          </div>
          <div style={{ display: "flex", gap: "4px" }}>
            {["7d", "30d", "90d"].map(p => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                style={{
                  padding: "6px 16px", borderRadius: "100px",
                  border: period === p ? "1px solid var(--accent)" : "1px solid var(--border)",
                  background: period === p ? "rgba(200,168,130,0.10)" : "transparent",
                  color: period === p ? "var(--accent)" : "var(--muted)",
                  fontFamily: "var(--font-mono)", fontSize: "10px", letterSpacing: "1px",
                  cursor: "pointer",
                }}
              >
                {p}
              </button>
            ))}
            <button
              onClick={() => { localStorage.removeItem("caractr_admin_token"); setToken(""); setData(null); }}
              style={{
                padding: "6px 12px", borderRadius: "100px",
                border: "1px solid var(--border)", background: "transparent",
                color: "var(--muted)", fontFamily: "var(--font-mono)", fontSize: "10px",
                cursor: "pointer", marginLeft: "8px",
              }}
            >
              SAIR
            </button>
          </div>
        </div>

        {/* Loading / Error */}
        {loading && (
          <div style={{ textAlign: "center", padding: "60px 0" }}>
            <p style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--muted)", letterSpacing: "1px" }}>A CARREGAR...</p>
          </div>
        )}

        {error && (
          <div style={{ textAlign: "center", padding: "60px 0" }}>
            <p style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "#d23c3c", letterSpacing: "1px" }}>{error.toUpperCase()}</p>
          </div>
        )}

        {/* Dashboard content */}
        {data && !loading && (
          <>
            <OverviewCards data={data.overview} />
            <FunnelChart steps={data.funnel} />
            <DailyTrend data={data.daily_trend} />
            <TopModels recommended={data.top_recommended} analysed={data.top_analysed} />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "32px" }}>
              <AnalysisStats stats={data.analysis_stats} />
              <BudgetDist data={data.budget_distribution} />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "32px" }}>
              <FeedbackSection data={data.feedback} />
              <div style={cardStyle}>
                <div style={sectionLabel}>Eventos totais</div>
                <div style={{ ...statNumber, fontSize: "36px" }}>{(data.overview?.total_events ?? 0).toLocaleString()}</div>
                <div style={{ ...statLabel, marginTop: "8px" }}>nos ultimos {data.period_days} dias</div>
                <div style={{ marginTop: "16px", fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--muted)" }}>
                  Completaram wizard: {data.overview?.sessions_started > 0
                    ? Math.round((data.overview.sessions_completed / data.overview.sessions_started) * 100)
                    : 0}%
                </div>
              </div>
            </div>

            {/* Timestamp */}
            <div style={{ textAlign: "center", padding: "16px 0", fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--muted)", letterSpacing: "1px" }}>
              PERIODO: {data.period} &middot; ATUALIZADO: {new Date().toLocaleString("pt-PT")}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
