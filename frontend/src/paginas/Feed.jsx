import { Link } from 'react-router-dom'
import Cabecalho from '../componentes/Cabecalho'
import { AvisoRisco, BarraScore, Carregando, Erro, SeloAcao, Termo } from '../componentes/Partes'
import { buscarSinais } from '../dados/fonte'
import { dolar, horario, porcentagem, simbolo } from '../dados/formato'
import { useDados } from '../dados/useDados'

// Feed de Sinais (RF-009): o sinal mais recente de cada ativo, com acesso ao
// Modo Explicativo e o aviso de risco sempre à vista (RF-013).

function CartaoSinal({ sinal }) {
  const { preco } = sinal
  if (!sinal.disponivel) {
    return (
      <li className="cartao p-4">
        <p className="font-black">{sinal.nome} <span className="font-normal text-texto-suave">{simbolo(sinal.ativo)}</span></p>
        <p className="mt-2 text-sm text-texto-suave">Sem sinal agora: {sinal.motivo}.</p>
      </li>
    )
  }
  return (
    <li>
      <Link to={`/sinais/${sinal.ativo}`} className="cartao block p-4 transition hover:ring-2 hover:ring-white/60">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-black text-[17px]">
              {sinal.nome} <span className="font-normal text-texto-suave">{simbolo(sinal.ativo)}</span>
            </p>
            <p className="text-sm">
              {dolar(preco.ultimo)}{' '}
              <span className={preco.variacao_24h_pct >= 0 ? 'text-alta' : 'text-queda'}>
                {porcentagem(preco.variacao_24h_pct)}
              </span>
            </p>
          </div>
          <SeloAcao acao={sinal.acao} />
        </div>
        <div className="mt-3 flex items-center gap-3">
          <BarraScore score={sinal.score} acao={sinal.acao} />
          <span className="w-16 shrink-0 text-right text-sm font-semibold">{sinal.score}/100</span>
        </div>
        {sinal.divergencia && (
          <p className="mt-2 text-xs font-semibold text-amber-700">
            Gráfico e notícias discordam: confiança reduzida.
          </p>
        )}
        <p className="mt-3 flex justify-between text-xs text-texto-suave">
          <span>Gerado em {horario(sinal.gerado_em)}</span>
          <span className="font-semibold text-black">Entender por quê ▶</span>
        </p>
      </Link>
    </li>
  )
}

export default function Feed() {
  const { dados, erro, carregando } = useDados(buscarSinais)
  return (
    <main className="mx-auto max-w-[440px] pb-10">
      <Cabecalho voltar titulo="Sinais" />
      <p className="px-[28px] pt-4 text-sm text-white/80">
        A <Termo id="score">confiança</Termo> vai de 0 a 100. Abaixo de 60 o Nox sugere manter.
      </p>
      {carregando && <Carregando />}
      {erro && <Erro erro={erro} />}
      {dados && (
        <div className="space-y-4 px-[28px] pt-4">
          <AvisoRisco texto={dados.find((s) => s.aviso_risco)?.aviso_risco ?? ''} />
          <ul className="space-y-4">
            {[...dados]
              .sort((a, b) => (b.score ?? -1) - (a.score ?? -1))
              .map((s) => <CartaoSinal key={s.ativo} sinal={s} />)}
          </ul>
        </div>
      )}
    </main>
  )
}
