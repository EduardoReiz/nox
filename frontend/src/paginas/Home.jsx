import { Link } from 'react-router-dom'
import iconeBtc from '../assets/icone-btc.svg'
import logoIa from '../assets/logo-nox-ia.png'
import Cabecalho from '../componentes/Cabecalho'
import { GraficoPreco, Mini } from '../componentes/Graficos'
import { AvisoRisco, Erro, SeloAcao } from '../componentes/Partes'
import { buscarSinais, buscarVelas } from '../dados/fonte'
import { dolar, horario, porcentagem, simbolo } from '../dados/formato'
import { useDados } from '../dados/useDados'

// Home do Figma. Os cartões de PIX e de transferência bancária deram lugar a
// Sinais e Aprendizado: o Nox é informativo e não movimenta dinheiro (RNE-007).

function CartaoBtc({ sinal, velas }) {
  const variacao = sinal.preco.variacao_24h_pct
  const subiu = variacao >= 0
  return (
    <Link to="/sinais/BTCUSDT" className="cartao flex aspect-square flex-col p-3 transition hover:ring-2 hover:ring-white/60">
      <div className="flex items-center gap-3">
        <img src={iconeBtc} alt="" width="40" height="40" />
        <span className="font-black text-[20px] text-texto-suave">BTC</span>
      </div>
      <p className="mt-auto font-black text-[15px] leading-tight">{dolar(sinal.preco.ultimo)}</p>
      <p className={`flex items-center gap-1 text-[12px] font-semibold ${subiu ? 'text-alta' : 'text-queda'}`}>
        <span aria-hidden="true">{subiu ? '▲' : '▼'}</span>
        {porcentagem(variacao)} <span className="font-normal text-texto-suave">em 24 h</span>
      </p>
      {velas && <Mini velas={velas.slice(-48)} subiu={subiu} />}
    </Link>
  )
}

function CartaoSinais({ sinais }) {
  const destaque = sinais.filter((s) => s.disponivel).sort((a, b) => b.score - a.score)[0]
  return (
    <Link to="/sinais" className="cartao flex aspect-square flex-col p-3 font-inter transition hover:ring-2 hover:ring-white/60">
      <div className="flex items-center justify-between">
        <span className="text-[16px] font-semibold text-texto-suave">Sinais</span>
        <span aria-hidden="true" className="text-texto-suave">▶</span>
      </div>
      <p className="mt-2 text-[12px] font-semibold leading-snug">O que o Nox sugere para os seus ativos</p>
      {destaque && (
        <div className="mt-auto">
          <p className="text-[11px] text-texto-suave">Maior confiança agora</p>
          <p className="mt-1 flex items-center gap-2 text-[13px] font-black">
            {simbolo(destaque.ativo)} <SeloAcao acao={destaque.acao} />
          </p>
          <p className="text-[11px] text-texto-suave">confiança {destaque.score} de 100</p>
        </div>
      )}
    </Link>
  )
}

function CartaoIa() {
  return (
    // A imagem do logo tem margem transparente em cima e embaixo; no Figma o
    // cartão avança sobre as linhas vizinhas para compensar.
    <Link to="/sinais" className="relative -my-9 block h-[242px] w-full" aria-label="Acesse sua IA de investimento">
      <div className="cartao absolute inset-x-0 inset-y-[21.49%] transition" />
      <img src={logoIa} alt="" width="256" height="242" className="absolute left-1/2 top-0 -translate-x-1/2" />
      <p className="absolute inset-x-0 top-[65.29%] text-center font-bold text-[16px] text-black">
        Acesse sua IA de investimento
      </p>
    </Link>
  )
}

function CartaoAprendizado() {
  return (
    <Link to="/aprendizado" className="cartao flex aspect-square flex-col p-3 transition hover:ring-2 hover:ring-white/60">
      <span className="font-inter text-[16px] font-semibold text-texto-suave">Aprendizado</span>
      <ul className="mt-2 space-y-1.5 text-[12px] font-semibold leading-tight">
        <li>O que é risco</li>
        <li>RSI e MACD</li>
        <li>Volume, volatilidade e sentimento</li>
      </ul>
      <span className="mt-auto self-start rounded bg-alta-claro px-2 py-0.5 font-inter text-[12px] font-black text-alta">
        Aprender
      </span>
    </Link>
  )
}

function CartaoNoticias() {
  return (
    <div className="cartao flex aspect-square flex-col p-3">
      <span className="text-center text-[12px] font-semibold">Notícias</span>
      <p className="mt-3 rounded-[3px] bg-moldura p-2 text-[11px] leading-snug text-texto-suave">
        A leitura de notícias e redes sociais (sentimento) entra no Nox no próximo período.
      </p>
    </div>
  )
}

export default function Home() {
  const sinais = useDados(buscarSinais)
  const velas = useDados(() => buscarVelas('BTCUSDT', 168))
  const btc = sinais.dados?.find((s) => s.ativo === 'BTCUSDT')

  return (
    <main className="mx-auto max-w-[440px] pb-10">
      <Cabecalho />
      <p className="mx-auto mt-7 max-w-[384px] px-4 text-center font-titulo text-[20px] text-white">
        Olá, seja bem-vindo!
        <br />
        Aqui estão os sinais dos seus ativos.
      </p>

      {sinais.erro && <Erro erro={sinais.erro} />}

      <div className="mt-7 space-y-4 px-[28px]">
        {velas.dados && (
          <GraficoPreco velas={velas.dados} titulo="BTC/USDT · velas de 1 hora · últimos 7 dias" />
        )}
        {sinais.dados && (
          <>
            <div className="grid grid-cols-2 gap-[50px]">
              {btc && <CartaoBtc sinal={btc} velas={velas.dados} />}
              <CartaoSinais sinais={sinais.dados} />
            </div>
            <CartaoIa />
            <div className="grid grid-cols-2 gap-[50px]">
              <CartaoAprendizado />
              <CartaoNoticias />
            </div>
            {btc && (
              <p className="text-center text-[11px] text-white/60">
                Preços atualizados em {horario(btc.preco.atualizado_em)}
              </p>
            )}
            <AvisoRisco texto={sinais.dados[0].aviso_risco ?? ''} />
          </>
        )}
      </div>
    </main>
  )
}
