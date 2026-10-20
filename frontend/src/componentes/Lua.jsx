import { useEffect, useState } from 'react'

// A confiança do sinal desenhada como fase da lua: 0 é lua nova, 100 é lua
// cheia. No Brasil (hemisfério sul) a lua crescente acende pela esquerda,
// então o desenho é espelhado para ficar igual à lua que o usuário vê no céu.

const COR = { comprar: 'var(--color-alta)', vender: 'var(--color-queda)', manter: 'var(--color-luar)' }
const DURACAO_MS = 900

// Caminho da parte iluminada para uma fração f entre 0 e 1. O contorno é o
// semicírculo da direita mais a linha do terminador, uma meia-elipse cuja
// largura muda com a fase.
function parteAcesa(f, r) {
  if (f <= 0) return ''
  if (f >= 1) return `M ${r} 0 A ${r} ${r} 0 1 1 ${r} ${2 * r} A ${r} ${r} 0 1 1 ${r} 0 Z`
  const rx = Math.abs(1 - 2 * f) * r
  const varre = f < 0.5 ? 0 : 1
  return `M ${r} 0 A ${r} ${r} 0 0 1 ${r} ${2 * r} A ${rx} ${r} 0 0 ${varre} ${r} 0 Z`
}

// O único movimento automático do Nox: ao abrir a tela, a lua passa de nova
// até a fase do sinal. Quem pediu menos movimento no sistema vê a fase direto.
function useFase(alvo) {
  const semMovimento = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const [fase, setFase] = useState(0)
  useEffect(() => {
    if (semMovimento) return
    let quadro
    const inicio = performance.now()
    const passo = (agora) => {
      const t = Math.min((agora - inicio) / DURACAO_MS, 1)
      setFase(alvo * (1 - (1 - t) ** 3))
      if (t < 1) quadro = requestAnimationFrame(passo)
    }
    quadro = requestAnimationFrame(passo)
    return () => cancelAnimationFrame(quadro)
  }, [alvo, semMovimento])
  return semMovimento ? alvo : fase
}

export default function Lua({ score, acao = 'manter', tamanho = 64, rotulo }) {
  const r = 50
  const cor = COR[acao]
  const fase = useFase(score / 100)
  return (
    <svg
      width={tamanho}
      height={tamanho}
      viewBox="-4 -4 108 108"
      role="img"
      aria-label={rotulo ?? `Confiança ${score} de 100`}
      className="shrink-0 overflow-visible"
    >
      <circle cx={r} cy={r} r={r} fill="var(--color-ceu-alto)" stroke="var(--color-linha)" strokeWidth="1.5" />
      <path d={parteAcesa(fase, r)} fill={cor} transform={`matrix(-1 0 0 1 ${2 * r} 0)`} />
      {/* halo discreto quando a confiança passa do limiar de 60 */}
      {score >= 60 && <circle cx={r} cy={r} r={r + 3} fill="none" stroke={cor} strokeOpacity="0.35" strokeWidth="1.5" />}
    </svg>
  )
}
