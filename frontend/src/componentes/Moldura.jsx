import { Outlet } from 'react-router-dom'
import Cabecalho, { FaixaSimulado } from './Cabecalho'

// Estrutura comum a todas as telas: cabeçalho, a faixa de aviso nos testes com
// dados simulados e o conteúdo.
export default function Moldura() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col">
      <Cabecalho />
      <FaixaSimulado />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
