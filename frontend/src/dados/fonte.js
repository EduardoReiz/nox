// De onde vêm os dados das telas. Os componentes não sabem qual fonte está em
// uso: os dois caminhos entregam o mesmo formato (docs/contrato_sinal.md).
//   VITE_FONTE=api       -> API do Nox (padrão; precisa do backend rodando)
//   VITE_FONTE=simulado  -> sinais_simulados.json, sem backend
import simulados from './sinais_simulados.json'

export const FONTE = import.meta.env.VITE_FONTE === 'simulado' ? 'simulado' : 'api'

async function pedir(caminho) {
  const resposta = await fetch(caminho)
  if (!resposta.ok) throw new Error(`A API respondeu ${resposta.status}`)
  return resposta.json()
}

export function buscarSinais() {
  if (FONTE === 'simulado') return Promise.resolve(simulados)
  return pedir('/api/sinais')
}

export function buscarSinal(ativo) {
  if (FONTE === 'simulado') {
    const sinal = simulados.find((s) => s.ativo === ativo)
    return sinal ? Promise.resolve(sinal) : Promise.reject(new Error('Ativo não acompanhado'))
  }
  return pedir(`/api/sinais/${ativo}`)
}

// Série simulada determinística: uma onda em torno do último preço, para o
// gráfico ter forma sem inventar dados que pareçam reais.
function velasSimuladas(ativo, quantidade) {
  const sinal = simulados.find((s) => s.ativo === ativo)
  const base = sinal?.preco.ultimo ?? 100
  const fim = new Date(sinal?.preco.atualizado_em ?? Date.now()).getTime()
  return Array.from({ length: quantidade }, (_, i) => {
    const t = i / quantidade
    const fator = 1 + 0.03 * Math.sin(t * 9) + 0.015 * Math.sin(t * 31) - 0.02 * (1 - t)
    return {
      instante: new Date(fim - (quantidade - 1 - i) * 3_600_000).toISOString(),
      fechamento: base * fator,
    }
  })
}

export function buscarVelas(ativo, quantidade = 168) {
  if (FONTE === 'simulado') return Promise.resolve(velasSimuladas(ativo, quantidade))
  return pedir(`/api/ativos/${ativo}/velas?quantidade=${quantidade}`)
}
