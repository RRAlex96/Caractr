import type { MetadataRoute } from "next"
import { MODELS, SNAPSHOT } from "@/lib/models"

const SITE_URL = "https://caractr.pt"

/**
 * Pages we want in search results. Generated, so the model and engine pages
 * can be added here from data instead of by hand. Personal or ephemeral pages
 * (results, feedback, shared analyses, admin) are deliberately absent.
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date()
  const page = (
    path: string,
    priority: number,
    changeFrequency: "weekly" | "monthly" = "monthly",
  ) => ({ url: `${SITE_URL}${path}`, lastModified: now, changeFrequency, priority })

  return [
    page("/", 1, "weekly"),
    page("/analisar", 0.9),
    page("/escolher", 0.9),
    page("/exemplos", 0.7, "weekly"),
    page("/concierge", 0.5),
    page("/carros", 0.8, "monthly"),
    // One page per model with enough market data; refreshed with each snapshot.
    ...MODELS.filter((m) => m.indexable).map((m) => ({
      url: `${SITE_URL}/carros/${m.slug}`,
      lastModified: SNAPSHOT ? new Date(SNAPSHOT.collected_on) : now,
      changeFrequency: "monthly" as const,
      priority: 0.6,
    })),
  ]
}
