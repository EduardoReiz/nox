import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { conta } from './conta'

const Contexto = createContext(null)

// Guarda quem está conectado. `usuario` é undefined enquanto carrega e null
// quando não há sessão.
export function ContaProvedor({ children }) {
  const [usuario, setUsuario] = useState(undefined)

  const recarregar = useCallback(() => conta.eu().then(setUsuario, () => setUsuario(null)), [])

  useEffect(() => {
    let vivo = true
    conta.eu().then(
      (u) => vivo && setUsuario(u),
      () => vivo && setUsuario(null),
    )
    return () => {
      vivo = false
    }
  }, [])

  const sair = useCallback(async () => {
    await conta.sair().catch(() => {})
    setUsuario(null)
  }, [])

  return <Contexto.Provider value={{ usuario, setUsuario, recarregar, sair }}>{children}</Contexto.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useConta() {
  return useContext(Contexto)
}
