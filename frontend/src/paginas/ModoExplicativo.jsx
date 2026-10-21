import { Link, useParams } from 'react-router-dom'
import Lua from '../componentes/Lua'
import { Acao, AvisoRisco, Carregando, Erro, Termo } from '../componentes/Partes'
import { buscarSinal } from '../dados/fonte'
import { dolar, horario, porcentagem, simbolo } from '../dados/formato'
import { useDados } from '../dados/useDados'

// Modo Explicativo (RF-005): primeiro o porquê, em linguagem simples; os
// números ficam guardados para quem quiser abrir.

const TERMO_DO_COMPONENTE = { tecnico: null, sentimento: 'sentimento', ml: 'ml' }

function Componente({ c }) {
  const termo = TERMO_DO_COMPONENTE[c.nome]
  // Mesma regra do backend: qualquer força diferente de zero já aponta um lado.
  const lado = c.forca > 0 ? 'aponta alta' : c.forca < 0 ? 'aponta queda' : 'neutro'
  const peso = (c.peso * 100).toLocaleString('pt-BR', { maximumFractionDigits: 1 })
  return (
    <li className="py-4">
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-semibold">{termo ? <Termo id={termo}>{c.rotulo}</Termo> : c.rotulo}</span>
        <span className="text-sm text-nevoa">{lado}</span>
      </div>
      <div className="mt-2 h-1.5 rounded-full bg-ceu-alto" aria-hidden="true">
        <div className="h-full rounded-full bg-luar" style={{ width: `${c.pontuacao}%` }} />
      </div>
      <p className="mt-1.5 text-sm text-nevoa">
        Apoia a leitura com {c.pontuacao} de 100 e vale {peso}% do cálculo.
      </p>
    </li>
  )
}

function NumerosTecnicos({ d }) {
  const fmt = (v, casas = 2) => v.toLocaleString('pt-BR', { maximumFractionDigits: casas })
  const cruzamento = d.cruzamento === 'alta' ? 'para cima' : d.cruzamento === 'baixa' ? 'para baixo' : 'nenhum'
  const linhas = [
    [<Termo key="r" id="rsi">RSI</Termo>, fmt(d.rsi, 1)],
    ...('macd' in d
      ? [
          [<Termo key="m" id="macd">MACD</Termo>, fmt(d.macd)],
          ['Linha de sinal', fmt(d.linha_sinal)],
          ['Histograma', fmt(d.histograma)],
        ]
      : []),
    ['Cruzamento do MACD', cruzamento],
  ]
  return (
    <dl className="mt-3 divide-y divide-linha text-sm">
      {linhas.map(([nome, valor], i) => (
        <div key={i} className="flex justify-between py-2">
          <dt>{nome}</dt>
          <dd className="text-nevoa">{valor}</dd>
        </div>
      ))}
    </dl>
  )
}

export default function ModoExplicativo() {
  const { ativo } = useParams()
  const { dados: s, erro, carregando } = useDados(() => buscarSinal(ativo), ativo)

  return (
    <div className="px-5 pb-10 pt-6">
      <Link to="/sinais" className="text-sm text-nevoa hover:text-luar">
        Voltar para os sinais
      </Link>
      {carregando && <Carregando />}
      {erro && <Erro erro={erro} />}
      {s && !s.disponivel && (
        <p className="mt-8 text-[15px] text-nevoa">Sem sinal para {s.nome} agora: {s.motivo}.</p>
      )}
      {s?.disponivel && (
        <article>
          <header className="mt-6 flex items-center gap-5">
            <Lua score={s.score} acao={s.acao} tamanho={112} />
            <div>
              <p className="text-nevoa">
                {s.nome} ({simbolo(s.ativo)})
              </p>
              <h1 className="font-serif text-[2.6rem] font-medium leading-none tracking-tight">
                <Acao acao={s.acao} className="font-medium" />
              </h1>
              <p className="mt-2 text-[15px]">
                <Termo id="score">Confiança</Termo> {s.score} de 100
              </p>
            </div>
          </header>
          <p className="mt-2 text-sm text-nevoa">
            {dolar(s.preco.ultimo)},{' '}
            <span className={s.preco.variacao_24h_pct >= 0 ? 'text-alta' : 'text-queda'}>
              {porcentagem(s.preco.variacao_24h_pct)}
            </span>{' '}
            em 24 h
          </p>

          <p className="mt-7 font-serif text-[1.2rem] leading-[1.7]">{s.explicacao}</p>

          {s.divergencia && (
            <aside className="mt-7 border-l-2 border-aviso pl-4">
              <p className="font-semibold text-aviso">
                <Termo id="divergencia">Divergência</Termo> encontrada
              </p>
              <p className="mt-1 text-[15px] leading-relaxed">
                O gráfico aponta {s.divergencia.tecnico}, mas o sentimento está {s.divergencia.sentimento}. Por
                isso a confiança caiu de {s.divergencia.score_antes} para {s.score}.
              </p>
            </aside>
          )}

          <section className="mt-9">
            <h2 className="font-serif text-xl">O que pesou no cálculo</h2>
            <ul className="mt-1 divide-y divide-linha">
              {s.componentes.map((c) => <Componente key={c.nome} c={c} />)}
            </ul>
            {s.ausentes.length > 0 && (
              <p className="text-sm leading-relaxed text-nevoa">
                Ficaram de fora: {s.ausentes.join(' e ')}. O peso deles foi dividido entre os outros.
              </p>
            )}
            <details className="mt-5 border-t border-linha pt-4">
              <summary className="cursor-pointer font-semibold">Ver os números da análise técnica</summary>
              <NumerosTecnicos d={s.componentes.find((c) => c.nome === 'tecnico').detalhes} />
            </details>
          </section>

          <div className="mt-9 space-y-4 border-t border-linha pt-6">
            <p className="text-xs text-nevoa">
              Sinal calculado em {horario(s.gerado_em)}, com preços até {horario(s.preco.atualizado_em)}.
            </p>
            <AvisoRisco texto={s.aviso_risco} />
          </div>
        </article>
      )}
    </div>
  )
}
