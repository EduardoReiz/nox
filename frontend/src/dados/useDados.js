import { useEffect, useRef, useState } from 'react'

// Carrega dados assíncronos e expõe { dados, erro, carregando }. A busca é
// refeita quando a `chave` muda (por exemplo, o ativo da página).
export function useDados(buscar, chave = '') {
  const [estado, setEstado] = useState({ dados: null, erro: null, carregando: true })
  const buscarAtual = useRef(buscar)
  useEffect(() => {
    buscarAtual.current = buscar
  })

  useEffect(() => {
    let vivo = true
    buscarAtual.current()
      .then((dados) => vivo && setEstado({ dados, erro: null, carregando: false }))
      .catch((erro) => vivo && setEstado({ dados: null, erro, carregando: false }))
    return () => {
      vivo = false
    }
  }, [chave])

  return estado
}
