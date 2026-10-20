import { useId, useState } from 'react'
import { ACOES } from '../dados/formato'
import { TERMOS } from '../dados/termos'

// RF-013: aviso de risco visível, sem depender de ação do usuário.
export function AvisoRisco({ texto }) {
  return (
    <p role="note" className="border-l-2 border-aviso pl-4 text-sm leading-relaxed text-nevoa">
      <span className="font-semibold text-aviso">Antes de decidir: </span>
      {texto}
    </p>
  )
}

// A ação sugerida como palavra na cor do lado do mercado.
export function Acao({ acao, className = '' }) {
  const { rotulo, cor } = ACOES[acao]
  return <span className={`font-semibold ${cor} ${className}`}>{rotulo}</span>
}

// Termo técnico com a explicação a um toque (RNF-001).
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
        className="cursor-help underline decoration-nevoa decoration-dotted underline-offset-4"
      >
        {children ?? termo.nome}
      </button>
      {aberto && (
        <span
          id={idTexto}
          role="tooltip"
          className="absolute left-0 top-full z-10 mt-2 block w-72 rounded-xl border border-linha bg-ceu-alto p-4 text-left font-sans text-sm font-normal leading-relaxed text-luar shadow-2xl"
        >
          <strong className="mb-1 block font-semibold">{termo.nome}</strong>
          {termo.texto}
        </span>
      )}
    </span>
  )
}

export function Carregando() {
  return <p className="px-5 py-16 text-center text-sm text-nevoa">Buscando os sinais...</p>
}

export function Erro({ erro }) {
  return (
    <div className="mx-5 my-8 border-l-2 border-queda pl-4 text-sm">
      <p className="font-semibold">Os sinais não carregaram.</p>
      <p className="mt-1 text-nevoa">
        {erro.message}. Verifique se a API do Nox está rodando na porta 8000.
      </p>
    </div>
  )
}
