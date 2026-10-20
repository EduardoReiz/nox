import { Area, AreaChart, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { dolar, horario } from '../dados/formato'

function Dica({ active, payload }) {
  if (!active || !payload?.length) return null
  const { instante, fechamento } = payload[0].payload
  return (
    <div className="rounded bg-black/90 px-2 py-1 text-xs text-white">
      <div>{horario(instante)}</div>
      <div className="font-semibold">{dolar(fechamento)}</div>
    </div>
  )
}

// Gráfico grande da Home: moldura cinza do Figma com o gráfico escuro dentro.
export function GraficoPreco({ velas, titulo }) {
  const subiu = velas.at(-1).fechamento >= velas[0].fechamento
  const cor = subiu ? '#26a69a' : '#ef5350'
  return (
    <figure className="rounded-lg bg-moldura p-2">
      <div className="rounded-[3px] bg-[#131722] px-1 pt-2">
        <figcaption className="px-2 text-[11px] text-white/70">{titulo}</figcaption>
        <ResponsiveContainer width="100%" height={170}>
          <AreaChart data={velas} margin={{ top: 8, right: 4, bottom: 0, left: 4 }}>
            <defs>
              <linearGradient id="preenchimento" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={cor} stopOpacity={0.35} />
                <stop offset="100%" stopColor={cor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="instante" hide />
            <YAxis
              domain={['auto', 'auto']}
              orientation="right"
              tick={{ fill: '#9aa0aa', fontSize: 10 }}
              tickFormatter={(v) => v.toLocaleString('pt-BR', { maximumFractionDigits: v < 10 ? 3 : 0 })}
              width={52}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<Dica />} />
            <Area type="monotone" dataKey="fechamento" stroke={cor} strokeWidth={1.6} fill="url(#preenchimento)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </figure>
  )
}

// Linha pequena do cartão do BTC.
export function Mini({ velas, subiu }) {
  return (
    <ResponsiveContainer width="100%" height={36}>
      <LineChart data={velas} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
        <YAxis domain={['auto', 'auto']} hide />
        <Line type="monotone" dataKey="fechamento" stroke={subiu ? '#2f8a3c' : '#e00000'} strokeWidth={1.5} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
