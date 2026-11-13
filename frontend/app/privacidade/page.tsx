import type { Metadata } from "next"
import Link from "next/link"

export const metadata: Metadata = {
  title: "Política de Privacidade",
  description:
    "Como o Caractr recolhe, utiliza e protege os teus dados pessoais, em conformidade com o RGPD.",
  alternates: { canonical: "/privacidade" },
  robots: { index: false, follow: false },
}

export default function PrivacidadePage() {
  const updated = "5 de abril de 2026"
  const email = "privacidade@caractr.pt"

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-[720px] px-8 pb-24 pt-24 md:pt-28">
        <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.1em] text-muted-foreground">
          ÚLTIMA ATUALIZAÇÃO — {updated}
        </p>

        <h1 className="mb-2 font-display text-[clamp(28px,5vw,40px)] font-extrabold leading-tight tracking-[0.04em]">
          POLÍTICA DE PRIVACIDADE
        </h1>
        <p className="mb-14 text-[15px] leading-relaxed text-muted-foreground">
          A tua privacidade é levada a sério. Este documento explica quais dados
          recolhemos, para quê, durante quanto tempo e quais os teus direitos ao
          abrigo do RGPD.
        </p>

        <Section title="1. Responsável pelo tratamento">
          <P>
            O responsável pelo tratamento dos teus dados pessoais é o Caractr,
            contactável em{" "}
            <a href={`mailto:${email}`} className="text-gold-dark underline">
              {email}
            </a>
            .
          </P>
        </Section>

        <Section title="2. Dados que recolhemos">
          <P>
            O Caractr recolhe apenas os dados estritamente necessários para
            prestar o serviço:
          </P>
          <Ul>
            <li>
              <strong>Respostas ao questionário de perfil</strong> — as tuas
              preferências de estilo de vida, orçamento e tipo de utilização. Não
              contêm dados de identificação pessoal.
            </li>
            <li>
              <strong>URL de anúncios</strong> — fornecidos por ti para análise.
              Não armazenamos o conteúdo scrapeado.
            </li>
            <li>
              <strong>Nome e email</strong> — apenas se submeteres o formulário
              de concierge. Usados exclusivamente para te contactar. Ao submeter
              o formulário, o teu resumo de perfil de preferências (prioridades,
              contexto) é associado à tua identidade para que possamos prestar um
              serviço personalizado.
            </li>
            <li>
              <strong>Dados de sessão anónimos</strong> — um identificador
              aleatorio gerado localmente (sem cookies de terceiros), para ligar
              eventos de navegação numa mesma visita.
            </li>
            <li>
              <strong>Dados de uso</strong> — páginas visitadas, interações com
              recomendações, tempo de sessão. Não contêm IP completo nem
              informação identificativa.
            </li>
          </Ul>
        </Section>

        <Section title="3. Finalidade do tratamento">
          <Ul>
            <li>
              <strong>Prestar o serviço de recomendação</strong> — processar o
              teu perfil e devolver recomendações personalizadas (base legal:
              execução de contrato / interesse legítimo).
            </li>
            <li>
              <strong>Analisar anúncios</strong> — avaliar um URL de anúncio
              específico com dados de mercado e fiabilidade (base legal: execução
              de contrato).
            </li>
            <li>
              <strong>Serviço de concierge</strong> — encaminhar o teu pedido
              para a equipa Caractr (base legal: consentimento explícito no
              formulário).
            </li>
            <li>
              <strong>Melhoria do produto</strong> — análise agregada e anónima
              de padrões de uso (base legal: interesse legítimo).
            </li>
          </Ul>
        </Section>

        <Section title="4. Partilha de dados com terceiros">
          <P>
            Não vendemos nem partilhamos os teus dados com terceiros para fins
            comerciais. Os dados podem ser partilhados com:
          </P>
          <Ul>
            <li>
              <strong>Google</strong> — quando utilizas a funcionalidade de
              análise de anúncios (/analisar), o URL do anúncio e o teu perfil de
              preferências são enviados para a API Gemini para gerar a análise.
              Este envio só ocorre quando acedes explicitamente à análise de um
              anúncio, nunca de forma passiva. A Google não utiliza dados
              enviados via API para treino de modelos (conforme os seus termos de
              serviço da API).
            </li>
            <li>
              <strong>Resend</strong> — serviço de envio de email transacional,
              utilizado para confirmações de concierge. São transmitidos: nome,
              email, modelo de interesse, orçamento, feedback de preferências,
              identificador de sessão e resumo do perfil de comprador.
            </li>
            <li>
              <strong>Fornecedores de infraestrutura</strong> — alojamento e base
              de dados (na UE). Tratamento realizado ao abrigo de Acordos de
              Processamento de Dados conformes com o RGPD.
            </li>
          </Ul>
        </Section>

        <Section title="5. Período de conservação">
          <Ul>
            <li>
              <strong>Respostas ao questionário</strong> — armazenadas durante 90
              dias para permitir retomas de sessão. A eliminação é executada
              automaticamente todos os dias pelo sistema.
            </li>
            <li>
              <strong>
                Dados de concierge (nome, email e informação associada)
              </strong>{" "}
              — conservados durante 12 meses após o registo. A eliminação é
              executada automaticamente todos os dias pelo sistema.
            </li>
            <li>
              <strong>Dados de uso anónimos</strong> — conservados durante 24
              meses para análise de produto, depois eliminados automaticamente.
            </li>
            <li>
              <strong>Dados locais (localStorage)</strong> — armazenados no teu
              dispositivo; podes elimina-los a qualquer momento limpando os dados
              de site do teu browser.
            </li>
          </Ul>
        </Section>

        <Section title="6. Os teus direitos (RGPD)">
          <P>
            Ao abrigo do Regulamento Geral sobre a Proteção de Dados (RGPD),
            tens os seguintes direitos:
          </P>
          <Ul>
            <li>
              <strong>Direito de acesso</strong> — solicitar uma copia dos teus
              dados.
            </li>
            <li>
              <strong>Direito de retificação</strong> — corrigir dados incorretos
              ou incompletos.
            </li>
            <li>
              <strong>Direito ao apagamento</strong> — solicitar a eliminação dos
              teus dados (&ldquo;direito a ser esquecido&rdquo;).
            </li>
            <li>
              <strong>Direito de oposição</strong> — opor-te ao tratamento com
              base em interesse legítimo.
            </li>
            <li>
              <strong>Direito a portabilidade</strong> — receber os teus dados
              num formato estruturado e legível por máquina.
            </li>
            <li>
              <strong>Direito de retirar o consentimento</strong> — a qualquer
              momento, sem afetar a licitude do tratamento anterior.
            </li>
          </Ul>
          <P>
            <strong>Apagamento em self-service:</strong> Podes eliminar os dados
            da tua sessão de recomendação imediatamente, sem enviar email. O teu
            identificador de sessão está guardado no teu browser em{" "}
            <Code>localStorage</Code> sob a chave{" "}
            <Code>caractr_session_id</Code>. Com esse valor, chama:
          </P>
          <pre className="my-1 overflow-x-auto rounded-md border border-border bg-card px-4 py-3 font-mono text-xs">
            {`DELETE https://api.caractr.pt/api/user/session/{session_id}`}
          </pre>
          <P>
            Isto elimina imediatamente o teu perfil de recomendação e qualquer
            pedido de concierge associado. Os eventos de análise anónimos (sem
            nome nem email) são eliminados automaticamente ao fim de 24 meses.
          </P>
          <P>
            Para exercer qualquer outro direito, ou se preferires contacto
            direto:{" "}
            <a href={`mailto:${email}`} className="text-gold-dark underline">
              {email}
            </a>
            . Responderemos no prazo de 30 dias.
          </P>
          <P>
            Tens também o direito de apresentar reclamação junto da{" "}
            <a
              href="https://www.cnpd.pt"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gold-dark underline"
            >
              Comissão Nacional de Proteção de Dados (CNPD)
            </a>
            .
          </P>
        </Section>

        <Section title="7. Cookies e armazenamento local">
          <P>
            O Caractr não utiliza cookies de terceiros nem tecnologias de
            rastreamento publicitário. Utilizamos <Code>localStorage</Code> do
            browser para armazenar o teu perfil e preferências localmente no teu
            dispositivo. Estes dados nunca são enviados para terceiros e podem
            ser eliminados a qualquer momento limpando os dados de site do teu
            browser.
          </P>
        </Section>

        <Section title="8. Segurança">
          <P>
            Os dados são transmitidos através de HTTPS. As bases de dados estão
            alojadas na União Europeia, com acesso restrito e encriptação em
            repouso. Não armazenamos passwords nem dados de pagamento.
          </P>
        </Section>

        <Section title="9. Menores">
          <P>
            O Caractr não é dirigido a menores de 18 anos. Não recolhemos
            conscientemente dados de menores. Se tomares conhecimento de que um
            menor forneceu dados pessoais, contacta-nos para os eliminarmos.
          </P>
        </Section>

        <Section title="10. Alterações a esta política">
          <P>
            Podemos atualizar esta política ocasionalmente. A data de última
            atualização no topo do documento indica quando ocorreu a última
            revisão. Para alterações substanciais, notificaremos os utilizadores
            com endereço de email registado.
          </P>
        </Section>

        <Section title="11. Contacto">
          <P>
            Para qualquer questão sobre privacidade ou proteção de dados:{" "}
            <a href={`mailto:${email}`} className="text-gold-dark underline">
              {email}
            </a>
          </P>
        </Section>

        {/* Back */}
        <div className="mt-16 border-t border-border pt-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 font-mono text-xs tracking-[0.08em] text-muted-foreground transition-colors hover:text-gold"
          >
            ← VOLTAR AO INÍCIO
          </Link>
        </div>
      </main>
    </div>
  )
}

/* ── Sub-components ── */

function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="mb-10">
      <h2 className="mb-3.5 font-display text-base font-bold tracking-[0.05em]">
        {title}
      </h2>
      <div className="flex flex-col gap-2.5">{children}</div>
    </section>
  )
}

function P({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-sm font-light leading-relaxed">{children}</p>
  )
}

function Ul({ children }: { children: React.ReactNode }) {
  return (
    <ul className="flex list-disc flex-col gap-2 pl-5 text-sm font-light leading-relaxed">
      {children}
    </ul>
  )
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded border border-border bg-card px-1.5 py-px font-mono text-xs">
      {children}
    </code>
  )
}
