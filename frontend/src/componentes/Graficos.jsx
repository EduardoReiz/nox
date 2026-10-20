import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { dolar, horario } from '../dados/formato'

function Dica({ active, payload }) {
  if (!active || !payload?.length) return null
  const { instante, fechamento } = payload[0].payload
  return (
    <div className="rounded-lg border border-linha bg-ceu-alto px-3 py-2 text-xs text-luar">
      <div className="text-nevoa">{horario(instante)}</div>
      <div className="font-semibold">{dolar(fechamento)}</div>
    </div>
  )
}

export function GraficoPreco({ velas, altura = 160 }) {
  const subiu = velas.at(-1).fechamento >= velas[0].fechamento
  const cor = subiu ? 'var(--color-alta)' : 'var(--color-queda)'
  return (
    <ResponsiveContainer width="100%" height={altura}>
      <AreaChart data={velas} margin={{ top: 6, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="sombra-preco" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={cor} stopOpacity={0.22} />
            <stop offset="100%" stopColor={cor} stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis dataKey="instante" hide />
        <YAxis domain={['auto', 'auto']} hide />
        <Tooltip content={<Dica />} cursor={{ stroke: 'var(--color-linha)' }} />
        <Area type="monotone" dataKey="fechamento" stroke={cor} strokeWidth={1.75} fill="url(#sombra-preco)" isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
