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
  comprar: { rotulo: 'Comprar', cor: 'bg-alta text-white' },
  vender: { rotulo: 'Vender', cor: 'bg-queda text-white' },
  manter: { rotulo: 'Manter', cor: 'bg-texto-suave text-white' },
}

export function simbolo(ativo) {
  return ativo.replace(/USDT$/, '')
}
