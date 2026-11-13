"use client"

import { cn, formatPrice } from "@/lib/utils"
import type { DepreciationData } from "@/lib/types"
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts"

interface DepreciationChartProps {
  depreciation: DepreciationData
  currentPrice?: number | null
  className?: string
}

export function DepreciationChart({
  depreciation,
  currentPrice,
  className,
}: DepreciationChartProps) {
  const { curve, future_value, annual_pct, annual_pct_label, holds_value, loses_fast } = depreciation

  // Build chart data from curve points
  const chartData = (curve || []).map((pt) => ({
    year: pt.year,
    age: pt.age,
    value: pt.p50,
    pctOfNew: Math.round(pt.pct_of_new * 100),
  }))

  // Append future projections if available
  const futureData = (future_value || []).map((fp) => ({
    year: fp.year,
    value: fp.value,
    pctOfCurrent: Math.round(fp.pct_of_current * 100),
    loss: fp.loss,
    isFuture: true,
  }))

  const hasChart = chartData.length >= 2
  const hasFuture = futureData.length > 0

  return (
    <div className={cn("rounded-xl border border-border bg-card p-5", className)}>
      <div className="mb-4 flex items-center justify-between">
        <p className="font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
          Depreciação
        </p>
        <div className="flex items-center gap-2">
          {holds_value && (
            <span className="rounded-full border border-success/40 px-2 py-0.5 font-mono text-[9px] uppercase text-success">
              Segura valor
            </span>
          )}
          {loses_fast && (
            <span className="rounded-full border border-danger/40 px-2 py-0.5 font-mono text-[9px] uppercase text-danger">
              Perde rápido
            </span>
          )}
        </div>
      </div>

      {/* Annual rate */}
      <div className="mb-4 flex items-baseline gap-2">
        <span className="font-mono text-2xl font-bold text-foreground">
          {annual_pct.toFixed(1)}%
        </span>
        <span className="font-mono text-[10px] text-muted-foreground/60">
          {annual_pct_label || "/ ano"}
        </span>
      </div>

      {/* Chart */}
      {hasChart && (
        <div className="mb-4 h-[180px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
              <defs>
                <linearGradient id="depGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#C8A882" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#C8A882" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="year"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 10, fill: "#71717A" }}
                interval="preserveStartEnd"
              />
              <YAxis
                hide
                domain={["dataMin", "dataMax"]}
              />
              <RechartsTooltip
                contentStyle={{
                  background: "#131316",
                  border: "1px solid #27272A",
                  borderRadius: 8,
                  fontSize: 12,
                  color: "#FAFAF9",
                }}
                formatter={(value) => [formatPrice(Number(value)), "Valor"]}
                labelFormatter={(label) => `${label}`}
              />
              {currentPrice && (
                <ReferenceLine
                  y={currentPrice}
                  stroke="#C8A882"
                  strokeDasharray="4 4"
                  strokeOpacity={0.4}
                />
              )}
              <Area
                type="monotone"
                dataKey="value"
                stroke="#C8A882"
                strokeWidth={2}
                fill="url(#depGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Future projections table */}
      {hasFuture && (
        <div>
          <p className="mb-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
            Projeção futura
          </p>
          <div className="grid grid-cols-3 gap-px overflow-hidden rounded-lg border border-border bg-border">
            {futureData.map((fp) => (
              <div key={fp.year} className="bg-card p-3 text-center">
                <p className="mb-1 font-mono text-[10px] text-muted-foreground">
                  {fp.year}
                </p>
                <p className="font-mono text-sm font-bold text-foreground">
                  {formatPrice(fp.value)}
                </p>
                <p className="font-mono text-[10px] text-danger/70">
                  -{formatPrice(fp.loss)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
