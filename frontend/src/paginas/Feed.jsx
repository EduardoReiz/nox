import { Link } from 'react-router-dom'
import Lua from '../componentes/Lua'
import { Acao, AvisoRisco, Carregando, Erro, Termo } from '../componentes/Partes'
import { buscarSinais } from '../dados/fonte'
import { dolar, horario, porcentagem, simbolo } from '../dados/formato'
import { useDados } from '../dados/useDados'

// Feed de Sinais (RF-009): o sinal mais recente de cada ativo, do mais
// confiante ao menos confiante, com o aviso de risco à vista (RF-013).

function Linha({ s }) {
  const conteudo = (
    <>
      <Lua score={s.disponivel ? s.score : 0} acao={s.acao} tamanho={48} />
      <div className="min-w-0 flex-1">
        <p className="font-semibold">
          {s.nome} <span className="font-normal text-nevoa">{simbolo(s.ativo)}</span>
        </p>
        {s.preco && (
          <p className="text-sm text-nevoa">
            {dolar(s.preco.ultimo)}{' '}
            <span className={s.preco.variacao_24h_pct >= 0 ? 'text-alta' : 'text-queda'}>
              {porcentagem(s.preco.variacao_24h_pct)}
            </span>
          </p>
        )}
        {s.divergencia && (
          <p className="mt-1 text-sm text-aviso">Gráfico e notícias discordam, confiança reduzida</p>
        )}
        {!s.disponivel && <p className="mt-1 text-sm text-nevoa">Sem sinal agora: {s.motivo}.</p>}
      </div>
      {s.disponivel && (
        <div className="text-right">
          <Acao acao={s.acao} className="text-lg" />
          <p className="text-sm text-nevoa">{s.score} de 100</p>
        </div>
      )}
    </>
  )
  return (
    <li className="border-b border-linha">
      {s.disponivel ? (
        <Link to={`/sinais/${s.ativo}`} className="flex items-center gap-4 px-5 py-4 hover:bg-ceu-alto/60">
          {conteudo}
        </Link>
      ) : (
        <div className="flex items-center gap-4 px-5 py-4">{conteudo}</div>
      )}
    </li>
  )
}

export default function Feed() {
  const { dados, erro, carregando } = useDados(buscarSinais)
  const ordenados = dados && [...dados].sort((a, b) => (b.score ?? -1) - (a.score ?? -1))
  const gerado = dados?.find((s) => s.gerado_em)?.gerado_em

  return (
    <>
      <div className="px-5 pb-5 pt-9">
        <h1 className="font-serif text-[2.1rem] font-medium leading-tight tracking-tight">Sinais</h1>
        <p className="mt-2 text-[15px] leading-relaxed text-nevoa">
          Do mais ao menos confiante. Abaixo de 60 de <Termo id="score">confiança</Termo>, a sugestão é sempre
          manter. Toque num ativo para ver o porquê.
        </p>
      </div>
      {carregando && <Carregando />}
      {erro && <Erro erro={erro} />}
      {ordenados && (
        <>
          <ul className="border-t border-linha">
            {ordenados.map((s) => <Linha key={s.ativo} s={s} />)}
          </ul>
          <div className="space-y-4 px-5 py-7">
            {gerado && <p className="text-xs text-nevoa">Calculados em {horario(gerado)}, horário de Brasília.</p>}
            <AvisoRisco texto={dados.find((s) => s.aviso_risco)?.aviso_risco ?? ''} />
          </div>
        </>
      )}
    </>
  )
}
