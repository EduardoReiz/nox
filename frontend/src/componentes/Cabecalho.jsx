import { Link, useNavigate } from 'react-router-dom'
import logo from '../assets/logo-nox.png'
import { FONTE } from '../dados/fonte'

// Logo do Figma: imagem de 120x150 recortada num círculo de 60 px.
export function Logo() {
  return (
    <Link to="/" aria-label="Nox, início" className="relative block size-[60px] overflow-hidden rounded-full">
      <img src={logo} alt="" width="120" height="150" className="absolute -left-[30px] -top-[45px] max-w-none" />
    </Link>
  )
}

export default function Cabecalho({ voltar = false, titulo }) {
  const navegar = useNavigate()
  return (
    <header className="flex items-center gap-3 px-[25px] pt-[27px]">
      {voltar ? (
        <button
          type="button"
          onClick={() => navegar(-1)}
          aria-label="Voltar"
          className="flex size-[44px] items-center justify-center rounded-full text-white hover:bg-white/10"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
      ) : (
        <Logo />
      )}
      {titulo && <h1 className="font-inter text-xl font-semibold text-white">{titulo}</h1>}
      {FONTE === 'simulado' && (
        <span className="ml-auto rounded bg-amber-300 px-2 py-0.5 text-xs font-semibold text-black">
          Dados simulados
        </span>
      )}
    </header>
  )
}
