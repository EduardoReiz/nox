import { useState } from 'react'

// Envia o formulário cuidando de carregando e erro.
export function useEnvio(acao) {
  const [estado, setEstado] = useState({ carregando: false, erro: '' })
  const enviar = async (evento) => {
    evento?.preventDefault()
    setEstado({ carregando: true, erro: '' })
    try {
      await acao()
      setEstado({ carregando: false, erro: '' })
    } catch (e) {
      setEstado({ carregando: false, erro: e.message })
    }
  }
  return [enviar, estado]
}
