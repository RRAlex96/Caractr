import { OverviewCards } from "./overview-cards"
import { FunnelChart } from "./funnel-chart"
import { DailyTrend } from "./daily-trend"
import { TopModels } from "./top-models"
import { AnalysisStats } from "./analysis-stats"
import { BudgetDist } from "./budget-dist"
import { FeedbackSection } from "./feedback-section"

interface AnalyticsTabProps {
  data: any
}

export function AnalyticsTab({ data }: AnalyticsTabProps) {
  return (
    <>
      <OverviewCards data={data.overview} />
      <FunnelChart steps={data.funnel} />
      <DailyTrend data={data.daily_trend} />
      <TopModels
        recommended={data.top_recommended}
        analysed={data.top_analysed}
      />

      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-2">
        <AnalysisStats stats={data.analysis_stats} />
        <BudgetDist data={data.budget_distribution} />
      </div>

      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-2">
        <FeedbackSection data={data.feedback} />
        <div className="rounded-xl border border-border bg-card px-6 py-5">
          <div className="mb-4 font-mono text-[10px] uppercase tracking-[2px] text-gold">
            Eventos totais
          </div>
          <div className="font-display text-4xl font-bold text-foreground">
            {(data.overview?.total_events ?? 0).toLocaleString()}
          </div>
          <div className="mt-2 font-mono text-[9px] uppercase tracking-[1.5px] text-muted-foreground">
            nos ultimos {data.period_days} dias
          </div>
          <div className="mt-4 font-mono text-[10px] text-muted-foreground">
            Completaram wizard:{" "}
            {data.overview?.sessions_started > 0
              ? Math.round(
                  (data.overview.sessions_completed /
                    data.overview.sessions_started) *
                    100
                )
              : 0}
            %
          </div>
        </div>
      </div>

      {/* Timestamp */}
      <div className="py-4 text-center font-mono text-[9px] tracking-[1px] text-muted-foreground">
        PERIODO: {data.period} &middot; ATUALIZADO:{" "}
        {new Date().toLocaleString("pt-PT")}
      </div>
    </>
  )
}
