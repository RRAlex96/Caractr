import { Landing, type FeaturedEngine } from "@/components/landing/landing"
import { ENGINE_PAGES, MODELS, SNAPSHOT } from "@/lib/models"

// Server component: the figures come from the exported data (frontend/data/
// models.json), so the home page never claims more than the database holds.

const FEATURED = 6

export default function HomePage() {
  const engines: FeaturedEngine[] = [...ENGINE_PAGES]
    .sort((a, b) => Number(b.severity === "critico") - Number(a.severity === "critico") ||
      b.affected_models.length - a.affected_models.length)
    .slice(0, FEATURED)
    .map((e) => ({
      page: e.page,
      engine: e.engine,
      problem: e.problem,
      years: e.affected_years,
      critical: e.severity === "critico",
    }))

  return (
    <Landing
      stats={{ models: MODELS.length, engines: ENGINE_PAGES.length, listings: SNAPSHOT?.listings ?? null }}
      engines={engines}
    />
  )
}
