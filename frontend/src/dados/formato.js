// Números e horários sempre no padrão brasileiro e no horário de Brasília.
// Os instantes chegam em UTC (Experimentação 1).

export function dolar(valor) {
  const casas = valor < 1 ? 4 : 2
  return valor.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  })
}

export function porcentagem(valor) {
  const sinal = valor > 0 ? '+' : ''
  return `${sinal}${valor.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`
}

export function horario(iso) {
  return new Date(iso).toLocaleString('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export const ACOES = {
  comprar: { rotulo: 'Comprar', cor: 'text-alta' },
  vender: { rotulo: 'Vender', cor: 'text-queda' },
  manter: { rotulo: 'Manter', cor: 'text-luar' },
}

// Saudação pelo horário de Brasília.
export function saudacao(agora = new Date()) {
  const hora = Number(agora.toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', hour12: false }))
  if (hora >= 5 && hora < 12) return 'Bom dia'
  if (hora >= 12 && hora < 18) return 'Boa tarde'
  return 'Boa noite'
}

export function simbolo(ativo) {
  return ativo.replace(/USDT$/, '')
}
