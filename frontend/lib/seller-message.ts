// The first message to a seller, written from the analysis: the questions a
// buyer should have answered before travelling to see a car. Plain text in
// European Portuguese, editable before sending. No price offer here: the
// negotiation numbers are for the visit, not the first message.
import type { AnalysisResult, DealbreakerIssue } from "@/lib/types"

function lowerFirst(s: string): string {
  return s ? s.charAt(0).toLowerCase() + s.slice(1) : s
}

function issueQuestion(i: DealbreakerIssue): string | null {
  const engine = i.engine ? `O motor ${i.engine}` : i.component === "caixa" ? "Esta caixa" : "Este motor"
  if (!i.problem) return null
  const topic = i.component === "caixa" ? "a caixa" : "o motor"
  return `${engine} tem um problema conhecido (${lowerFirst(i.problem).replace(/\.$/, "")}). Já foi feita alguma intervenção n${topic === "a caixa" ? "a caixa" : "esse ponto"}? Tem as faturas?`
}

export function sellerMessage(r: AnalysisResult): string {
  const l = r.listing
  const car = [l.brand_name, l.model_name, l.year].filter(Boolean).join(" ")
  const questions: string[] = [
    "O livro de revisões está completo? As revisões foram feitas na marca ou em oficina independente?",
  ]

  const issues = [...(r.dealbreakers?.critical_issues ?? []), ...(r.dealbreakers?.watch_items ?? [])]
    .filter((i) => i.curated)
  const seen = new Set<string>()
  for (const i of issues) {
    const q = issueQuestion(i)
    if (q && !seen.has(i.id ?? q)) {
      questions.push(q)
      seen.add(i.id ?? q)
    }
    if (seen.size >= 2) break
  }

  questions.push("Quantos donos teve? Tem algum historial de acidentes ou reparações de chapa?")

  const recalls = r.dealbreakers?.recall_count ?? 0
  questions.push(
    recalls > 0
      ? `Pode enviar-me o número do quadro (VIN)? Há ${recalls} ${recalls === 1 ? "campanha de recolha" : "campanhas de recolha"} para este modelo e ano e queria confirmar se este carro estava abrangido.`
      : "Pode enviar-me o número do quadro (VIN)? Queria confirmar o historial do carro.",
  )

  const kmYear = r.deal?.km_per_year
  if (kmYear && kmYear > 20000) {
    questions.push("Que tipo de utilização teve? Fez sobretudo autoestrada?")
  }

  if (l.seller_type === "stand") {
    questions.push("Que garantia dão e o que cobre exatamente?")
  } else {
    questions.push("O carro está registado em seu nome e tem a inspeção periódica em dia?")
  }
  questions.push("O preço é negociável?")

  return [
    "Olá, boa tarde.",
    "",
    `Vi o anúncio do ${car} e tenho interesse. Antes de marcar uma visita, podia confirmar-me o seguinte?`,
    "",
    ...questions.map((q, k) => `${k + 1}. ${q}`),
    "",
    "Obrigado.",
  ].join("\n")
}
