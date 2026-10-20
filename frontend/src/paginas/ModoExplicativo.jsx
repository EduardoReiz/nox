import { useParams } from 'react-router-dom'
import Cabecalho from '../componentes/Cabecalho'
import { AvisoRisco, BarraScore, Carregando, Erro, SeloAcao, Termo } from '../componentes/Partes'
import { buscarSinal } from '../dados/fonte'
import { dolar, horario, simbolo } from '../dados/formato'
import { useDados } from '../dados/useDados'

// Modo Explicativo (RF-005): o resumo vem primeiro, em linguagem simples, e
// os números ficam nos detalhes, abertos sob demanda.

const TERMO_DO_COMPONENTE = { tecnico: null, sentimento: 'sentimento', ml: 'ml' }

function Componente({ c }) {
  const termo = TERMO_DO_COMPONENTE[c.nome]
  // Mesma regra do backend: qualquer força diferente de zero já aponta um lado.
  const lado = c.forca > 0 ? 'aponta alta' : c.forca < 0 ? 'aponta queda' : 'neutro'
  return (
    <li className="py-3">
      <div className="flex items-baseline justify-between gap-2 text-sm">
        <span className="font-semibold">{termo ? <Termo id={termo}>{c.rotulo}</Termo> : c.rotulo}</span>
        {/* uma casa decimal: com 62,5% e 37,5% o arredondamento somava 101% */}
        <span className="text-xs text-texto-suave">
          peso {(c.peso * 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%
        </span>
      </div>
      <div className="mt-2 flex items-center gap-3">
        <div className="h-2 w-full rounded-full bg-moldura">
          <div className="h-full rounded-full bg-black" style={{ width: `${c.pontuacao}%` }} />
        </div>
        <span className="w-32 shrink-0 text-right text-xs">
          {c.pontuacao} pts · {lado}
        </span>
      </div>
    </li>
  )
}

function DetalhesTecnicos({ d }) {
  const fmt = (v, casas = 2) => v.toLocaleString('pt-BR', { maximumFractionDigits: casas })
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
      <dt><Termo id="rsi">RSI</Termo></dt>
      <dd className="text-right">{fmt(d.rsi, 1)}</dd>
      {'macd' in d && (
        <>
          <dt><Termo id="macd">MACD</Termo></dt>
          <dd className="text-right">{fmt(d.macd)}</dd>
          <dt>Linha de sinal</dt>
          <dd className="text-right">{fmt(d.linha_sinal)}</dd>
          <dt>Histograma</dt>
          <dd className="text-right">{fmt(d.histograma)}</dd>
        </>
      )}
      <dt>Cruzamento do MACD</dt>
      <dd className="text-right">{d.cruzamento === 'alta' ? 'para cima' : d.cruzamento === 'baixa' ? 'para baixo' : 'nenhum'}</dd>
    </dl>
  )
}

export default function ModoExplicativo() {
  const { ativo } = useParams()
  const { dados: s, erro, carregando } = useDados(() => buscarSinal(ativo), ativo)

  return (
    <main className="mx-auto max-w-[440px] pb-10">
      <Cabecalho voltar titulo="Por que este sinal?" />
      {carregando && <Carregando />}
      {erro && <Erro erro={erro} />}
      {s && !s.disponivel && (
        <div className="cartao mx-[28px] mt-6 p-4 text-sm">Sem sinal para {s.nome} agora: {s.motivo}.</div>
      )}
      {s?.disponivel && (
        <div className="space-y-4 px-[28px] pt-5">
          <section className="cartao p-4">
            <p className="text-sm text-texto-suave">
              {s.nome} · {simbolo(s.ativo)} · {dolar(s.preco.ultimo)}
            </p>
            <div className="mt-2 flex items-center justify-between">
              <SeloAcao acao={s.acao} grande />
              <span className="text-2xl font-black">
                {s.score}<span className="text-base font-normal text-texto-suave">/100</span>
              </span>
            </div>
            <div className="mt-3">
              <BarraScore score={s.score} acao={s.acao} />
              <p className="mt-1 text-right text-[11px] text-texto-suave">
                <Termo id="score">confiança</Termo> · a marca indica o mínimo de 60 para agir
              </p>
            </div>
            <p className="mt-4 text-[15px] leading-relaxed">{s.explicacao}</p>
          </section>

          {s.divergencia && (
            <section className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">
              <p className="font-semibold">
                <Termo id="divergencia">Divergência</Termo> encontrada
              </p>
              <p className="mt-1">
                O gráfico aponta {s.divergencia.tecnico}, mas o sentimento está {s.divergencia.sentimento}.
                A confiança caiu de {s.divergencia.score_antes} para {s.score}.
              </p>
            </section>
          )}

          <section className="cartao p-4">
            <h2 className="font-inter font-semibold">Como a confiança foi calculada</h2>
            <ul className="divide-y divide-moldura">
              {s.componentes.map((c) => <Componente key={c.nome} c={c} />)}
            </ul>
            {s.ausentes.length > 0 && (
              <p className="mt-1 text-xs text-texto-suave">
                Não entraram neste cálculo: {s.ausentes.join(' e ')}. O peso deles foi dividido entre os demais.
              </p>
            )}
            <details className="mt-3 rounded bg-moldura/40 p-3">
              <summary className="cursor-pointer text-sm font-semibold">Ver os números da análise técnica</summary>
              <div className="mt-3">
                <DetalhesTecnicos d={s.componentes.find((c) => c.nome === 'tecnico').detalhes} />
              </div>
            </details>
          </section>

          <p className="text-center text-[11px] text-white/60">
            Sinal gerado em {horario(s.gerado_em)} · preço de {horario(s.preco.atualizado_em)}
          </p>
          <AvisoRisco texto={s.aviso_risco} />
        </div>
      )}
    </main>
  )
}
