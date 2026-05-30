import type { Metadata } from "next"
import Link from "next/link"

export const metadata: Metadata = {
  title: "Politica de Privacidade | Caractr",
  description:
    "Como o Caractr recolhe, utiliza e protege os teus dados pessoais, em conformidade com o RGPD.",
  robots: { index: false, follow: false },
}

export default function PrivacidadePage() {
  const updated = "5 de abril de 2026"
  const email = "privacidade@caractr.pt"

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-[720px] px-8 pb-24 pt-24 md:pt-28">
        <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.1em] text-muted-foreground">
          ULTIMA ATUALIZACAO — {updated}
        </p>

        <h1 className="mb-2 font-display text-[clamp(28px,5vw,40px)] font-extrabold leading-tight tracking-[0.04em]">
          POLITICA DE PRIVACIDADE
        </h1>
        <p className="mb-14 text-[15px] leading-relaxed text-muted-foreground">
          A tua privacidade e levada a serio. Este documento explica quais dados
          recolhemos, para que, durante quanto tempo e quais os teus direitos ao
          abrigo do RGPD.
        </p>

        <Section title="1. Responsavel pelo tratamento">
          <P>
            O responsavel pelo tratamento dos teus dados pessoais e o Caractr,
            contactavel em{" "}
            <a href={`mailto:${email}`} className="text-gold-dark underline">
              {email}
            </a>
            .
          </P>
        </Section>

        <Section title="2. Dados que recolhemos">
          <P>
            O Caractr recolhe apenas os dados estritamente necessarios para
            prestar o servico:
          </P>
          <Ul>
            <li>
              <strong>Respostas ao questionario de perfil</strong> — as tuas
              preferencias de estilo de vida, orcamento e tipo de utilizacao. Nao
              contem dados de identificacao pessoal.
            </li>
            <li>
              <strong>URL de anuncios</strong> — fornecidos por ti para analise.
              Nao armazenamos o conteudo scrapeado.
            </li>
            <li>
              <strong>Nome e email</strong> — apenas se submeteres o formulario
              de concierge. Usados exclusivamente para te contactar. Ao submeter
              o formulario, o teu resumo de perfil de preferencias (prioridades,
              contexto) e associado a tua identidade para que possamos prestar um
              servico personalizado.
            </li>
            <li>
              <strong>Dados de sessao anonimos</strong> — um identificador
              aleatorio gerado localmente (sem cookies de terceiros), para ligar
              eventos de navegacao numa mesma visita.
            </li>
            <li>
              <strong>Dados de uso</strong> — paginas visitadas, interacoes com
              recomendacoes, tempo de sessao. Nao contem IP completo nem
              informacao identificativa.
            </li>
          </Ul>
        </Section>

        <Section title="3. Finalidade do tratamento">
          <Ul>
            <li>
              <strong>Prestar o servico de recomendacao</strong> — processar o
              teu perfil e devolver recomendacoes personalizadas (base legal:
              execucao de contrato / interesse legitimo).
            </li>
            <li>
              <strong>Analisar anuncios</strong> — avaliar um URL de anuncio
              especifico com dados de mercado e fiabilidade (base legal: execucao
              de contrato).
            </li>
            <li>
              <strong>Servico de concierge</strong> — encaminhar o teu pedido
              para a equipa Caractr (base legal: consentimento explicito no
              formulario).
            </li>
            <li>
              <strong>Melhoria do produto</strong> — analise agregada e anonima
              de padroes de uso (base legal: interesse legitimo).
            </li>
          </Ul>
        </Section>

        <Section title="4. Partilha de dados com terceiros">
          <P>
            Nao vendemos nem partilhamos os teus dados com terceiros para fins
            comerciais. Os dados podem ser partilhados com:
          </P>
          <Ul>
            <li>
              <strong>Google</strong> — quando utilizas a funcionalidade de
              analise de anuncios (/analisar), o URL do anuncio e o teu perfil de
              preferencias sao enviados para a API Gemini para gerar a analise.
              Este envio so ocorre quando acedes explicitamente a analise de um
              anuncio, nunca de forma passiva. A Google nao utiliza dados
              enviados via API para treino de modelos (conforme os seus termos de
              servico da API).
            </li>
            <li>
              <strong>Resend</strong> — servico de envio de email transacional,
              utilizado para confirmacoes de concierge. Sao transmitidos: nome,
              email, modelo de interesse, orcamento, feedback de preferencias,
              identificador de sessao e resumo do perfil de comprador.
            </li>
            <li>
              <strong>Fornecedores de infraestrutura</strong> — alojamento e base
              de dados (na UE). Tratamento realizado ao abrigo de Acordos de
              Processamento de Dados conformes com o RGPD.
            </li>
          </Ul>
        </Section>

        <Section title="5. Periodo de conservacao">
          <Ul>
            <li>
              <strong>Respostas ao questionario</strong> — armazenadas durante 90
              dias para permitir retomas de sessao. A eliminacao e executada
              automaticamente todos os dias pelo sistema.
            </li>
            <li>
              <strong>
                Dados de concierge (nome, email e informacao associada)
              </strong>{" "}
              — conservados durante 12 meses apos o registo. A eliminacao e
              executada automaticamente todos os dias pelo sistema.
            </li>
            <li>
              <strong>Dados de uso anonimos</strong> — conservados durante 24
              meses para analise de produto, depois eliminados automaticamente.
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
            Ao abrigo do Regulamento Geral sobre a Protecao de Dados (RGPD),
            tens os seguintes direitos:
          </P>
          <Ul>
            <li>
              <strong>Direito de acesso</strong> — solicitar uma copia dos teus
              dados.
            </li>
            <li>
              <strong>Direito de retificacao</strong> — corrigir dados incorretos
              ou incompletos.
            </li>
            <li>
              <strong>Direito ao apagamento</strong> — solicitar a eliminacao dos
              teus dados (&ldquo;direito a ser esquecido&rdquo;).
            </li>
            <li>
              <strong>Direito de oposicao</strong> — opor-te ao tratamento com
              base em interesse legitimo.
            </li>
            <li>
              <strong>Direito a portabilidade</strong> — receber os teus dados
              num formato estruturado e legivel por maquina.
            </li>
            <li>
              <strong>Direito de retirar o consentimento</strong> — a qualquer
              momento, sem afetar a licitude do tratamento anterior.
            </li>
          </Ul>
          <P>
            <strong>Apagamento em self-service:</strong> Podes eliminar os dados
            da tua sessao de recomendacao imediatamente, sem enviar email. O teu
            identificador de sessao esta guardado no teu browser em{" "}
            <Code>localStorage</Code> sob a chave{" "}
            <Code>caractr_session_id</Code>. Com esse valor, chama:
          </P>
          <pre className="my-1 overflow-x-auto rounded-md border border-border bg-card px-4 py-3 font-mono text-xs">
            {`DELETE https://api.caractr.pt/api/user/session/{session_id}`}
          </pre>
          <P>
            Isto elimina imediatamente o teu perfil de recomendacao e qualquer
            pedido de concierge associado. Os eventos de analise anonimos (sem
            nome nem email) sao eliminados automaticamente ao fim de 24 meses.
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
            Tens tambem o direito de apresentar reclamacao junto da{" "}
            <a
              href="https://www.cnpd.pt"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gold-dark underline"
            >
              Comissao Nacional de Protecao de Dados (CNPD)
            </a>
            .
          </P>
        </Section>

        <Section title="7. Cookies e armazenamento local">
          <P>
            O Caractr nao utiliza cookies de terceiros nem tecnologias de
            rastreamento publicitario. Utilizamos <Code>localStorage</Code> do
            browser para armazenar o teu perfil e preferencias localmente no teu
            dispositivo. Estes dados nunca sao enviados para terceiros e podem
            ser eliminados a qualquer momento limpando os dados de site do teu
            browser.
          </P>
        </Section>

        <Section title="8. Seguranca">
          <P>
            Os dados sao transmitidos atraves de HTTPS. As bases de dados estao
            alojadas na Uniao Europeia, com acesso restrito e encriptacao em
            repouso. Nao armazenamos passwords nem dados de pagamento.
          </P>
        </Section>

        <Section title="9. Menores">
          <P>
            O Caractr nao e dirigido a menores de 18 anos. Nao recolhemos
            conscientemente dados de menores. Se tomares conhecimento de que um
            menor forneceu dados pessoais, contacta-nos para os eliminarmos.
          </P>
        </Section>

        <Section title="10. Alteracoes a esta politica">
          <P>
            Podemos atualizar esta politica ocasionalmente. A data de ultima
            atualizacao no topo do documento indica quando ocorreu a ultima
            revisao. Para alteracoes substanciais, notificaremos os utilizadores
            com endereco de email registado.
          </P>
        </Section>

        <Section title="11. Contacto">
          <P>
            Para qualquer questao sobre privacidade ou protecao de dados:{" "}
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
            ← VOLTAR AO INICIO
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
