import { Link } from 'react-router-dom'
import { GraficoPreco } from '../componentes/Graficos'
import Lua from '../componentes/Lua'
import { Acao, AvisoRisco, Carregando, Erro } from '../componentes/Partes'
import { buscarSinais, buscarVelas } from '../dados/fonte'
import { dolar, horario, porcentagem, saudacao, simbolo } from '../dados/formato'
import { useDados } from '../dados/useDados'

function Ceu({ sinais }) {
  return (
    <ul className="mt-8 grid grid-cols-3 gap-x-3 gap-y-7">
      {sinais.map((s) => (
        <li key={s.ativo}>
          <Link to={`/sinais/${s.ativo}`} className="flex flex-col items-center gap-2 rounded-xl py-2 text-center">
            {s.disponivel ? (
              <Lua score={s.score} acao={s.acao} tamanho={72} rotulo={`${s.nome}: confiança ${s.score} de 100`} />
            ) : (
              <Lua score={0} tamanho={72} rotulo={`${s.nome}: sem sinal`} />
            )}
            <span className="text-sm font-semibold">{simbolo(s.ativo)}</span>
            {s.disponivel ? (
              <span className="-mt-1 text-sm">
                <Acao acao={s.acao} /> <span className="text-nevoa">{s.score}</span>
              </span>
            ) : (
              <span className="-mt-1 text-sm text-nevoa">sem sinal</span>
            )}
          </Link>
        </li>
      ))}
    </ul>
  )
}

function Bitcoin({ sinal }) {
  const velas = useDados(() => buscarVelas('BTCUSDT', 168))
  const variacao = sinal.preco.variacao_24h_pct
  return (
    <section className="border-t border-linha px-5 py-7">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="font-serif text-xl">Bitcoin nos últimos 7 dias</h2>
        <Link to="/sinais/BTCUSDT" className="text-sm text-nevoa underline underline-offset-4 hover:text-luar">
          Ver o sinal
        </Link>
      </div>
      <p className="mt-1 text-2xl font-semibold">
        {dolar(sinal.preco.ultimo)}{' '}
        <span className={`text-base font-medium ${variacao >= 0 ? 'text-alta' : 'text-queda'}`}>
          {porcentagem(variacao)} em 24 h
        </span>
      </p>
      <div className="mt-4">{velas.dados && <GraficoPreco velas={velas.dados} />}</div>
    </section>
  )
}

export default function Home() {
  const { dados, erro, carregando } = useDados(buscarSinais)
  const btc = dados?.find((s) => s.ativo === 'BTCUSDT' && s.disponivel)
  const atualizado = dados?.find((s) => s.preco)?.preco.atualizado_em

  return (
    <>
      <section className="px-5 pb-8 pt-9">
        <p className="text-nevoa">{saudacao()}.</p>
        <h1 className="mt-1 font-serif text-[2.1rem] font-medium leading-[1.15] tracking-tight">
          Como o Nox vê o mercado agora
        </h1>
        <p className="mt-3 max-w-[34ch] text-[15px] leading-relaxed text-nevoa">
          Cada lua mostra a confiança de um sinal. Quanto mais cheia, mais os indicadores concordam.
          A partir de 60% cheia, o Nox destaca um sinal de alta ou de queda.
        </p>
        {carregando && <Carregando />}
        {erro && <Erro erro={erro} />}
        {dados && <Ceu sinais={dados} />}
        {atualizado && <p className="mt-6 text-xs text-nevoa">Preços até {horario(atualizado)}, horário de Brasília.</p>}
      </section>

      {btc && <Bitcoin sinal={btc} />}

      <section className="border-t border-linha px-5 py-7">
        <h2 className="font-serif text-xl">Primeira vez por aqui?</h2>
        <p className="mt-2 text-[15px] leading-relaxed text-nevoa">
          Entenda o que são o RSI, o MACD e o risco de investir em cripto antes de seguir qualquer sinal.
        </p>
        <Link
          to="/aprendizado"
          className="mt-4 inline-block rounded-full bg-luar px-5 py-2.5 text-sm font-semibold text-ceu hover:bg-white"
        >
          Aprender o básico
        </Link>
      </section>

      {dados?.[0]?.aviso_risco && (
        <div className="border-t border-linha px-5 py-7">
          <AvisoRisco texto={dados.find((s) => s.aviso_risco).aviso_risco} />
        </div>
      )}
    </>
  )
}
