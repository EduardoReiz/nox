import { useId, useState } from 'react'
import { ACOES } from '../dados/formato'
import { TERMOS } from '../dados/termos'

// RF-013: aviso de risco visível, sem depender de ação do usuário.
export function AvisoRisco({ texto, claro = false }) {
  return (
    <p
      role="note"
      className={`rounded-lg px-4 py-3 text-xs leading-relaxed ${
        claro ? 'bg-amber-50 text-amber-950' : 'border border-amber-300/40 bg-amber-300/10 text-amber-100'
      }`}
    >
      <strong className="font-semibold">Aviso de risco: </strong>
      {texto}
    </p>
  )
}

export function SeloAcao({ acao, grande = false }) {
  const { rotulo, cor } = ACOES[acao]
  return (
    <span className={`inline-block rounded font-inter font-black uppercase ${cor} ${grande ? 'px-3 py-1 text-base' : 'px-2 py-0.5 text-xs'}`}>
      {rotulo}
    </span>
  )
}

// Barra de 0 a 100 com a marca do limiar de 60 (RNE-008).
export function BarraScore({ score, acao }) {
  const cor = acao === 'comprar' ? 'bg-alta' : acao === 'vender' ? 'bg-queda' : 'bg-texto-suave'
  return (
    <div className="relative h-2 w-full rounded-full bg-moldura" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={score} aria-label={`Confiança ${score} de 100`}>
      <div className={`h-full rounded-full ${cor}`} style={{ width: `${score}%` }} />
      <div className="absolute -top-1 h-4 w-0.5 bg-black/60" style={{ left: '60%' }} title="Limiar de 60" />
    </div>
  )
}

// Termo técnico com a explicação a um clique (RNF-001).
export function Termo({ id, children }) {
  const [aberto, setAberto] = useState(false)
  const idTexto = useId()
  const termo = TERMOS[id]
  return (
    <span className="relative">
      <button
        type="button"
        onClick={() => setAberto((a) => !a)}
        aria-expanded={aberto}
        aria-controls={idTexto}
        className="cursor-help underline decoration-dotted underline-offset-4"
      >
        {children ?? termo.nome}
      </button>
      {aberto && (
        <span id={idTexto} role="tooltip" className="absolute left-0 top-full z-10 mt-2 block w-64 rounded-lg bg-black p-3 text-left text-xs font-normal leading-relaxed text-white shadow-xl">
          <strong className="mb-1 block">{termo.nome}</strong>
          {termo.texto}
        </span>
      )}
    </span>
  )
}

export function Carregando() {
  return <p className="px-[25px] py-10 text-center text-sm text-white/70">Carregando...</p>
}

export function Erro({ erro }) {
  return (
    <div className="mx-[25px] my-8 rounded-lg bg-white/10 p-4 text-sm text-white">
      <p className="font-semibold">Não foi possível carregar os dados.</p>
      <p className="mt-1 text-white/70">{erro.message}. Confira se a API do Nox está rodando.</p>
    </div>
  )
}
