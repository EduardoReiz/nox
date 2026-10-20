import { Link, NavLink } from 'react-router-dom'
import logo from '../assets/logo-n.png'
import { FONTE } from '../dados/fonte'

const ABAS = [
  { para: '/', nome: 'Hoje', fim: true },
  { para: '/sinais', nome: 'Sinais' },
  { para: '/aprendizado', nome: 'Aprender' },
]

export default function Cabecalho() {
  return (
    <header className="flex items-center gap-4 border-b border-linha px-5 py-3">
      <Link to="/" className="flex items-center gap-2" aria-label="Nox, página inicial">
        <img src={logo} alt="" width="28" height="28" />
        <span className="font-serif text-xl font-medium tracking-tight">Nox</span>
      </Link>
      <nav className="ml-auto flex gap-1 text-sm" aria-label="Seções">
        {ABAS.map((a) => (
          <NavLink
            key={a.para}
            to={a.para}
            end={a.fim}
            className={({ isActive }) =>
              `rounded-full px-3 py-1.5 transition-colors ${isActive ? 'bg-ceu-alto text-luar' : 'text-nevoa hover:text-luar'}`
            }
          >
            {a.nome}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

// Faixa logo abaixo do cabeçalho quando os dados são simulados, para nenhuma
// captura de tela ser confundida com dados reais.
export function FaixaSimulado() {
  if (FONTE !== 'simulado') return null
  return (
    <p className="bg-aviso px-5 py-1.5 text-center text-xs font-semibold text-ceu">
      Dados simulados para teste. Não são preços nem sinais reais.
    </p>
  )
}
