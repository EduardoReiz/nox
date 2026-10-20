import { TERMOS } from '../dados/termos'

// Aprendizado (RF-014): os três temas previstos, em versão curta.
const TEMAS = [
  {
    titulo: 'Risco',
    texto: [
      'Criptoativos podem subir ou cair muito em poucas horas. Nenhuma ferramenta, nem o Nox, acerta sempre.',
      'Invista só o que pode perder sem comprometer contas e reservas. Dividir o dinheiro entre ativos diferentes reduz o impacto de uma queda.',
      'Desconfie de promessas de lucro rápido e de grupos que vendem sinais sem mostrar o motivo.',
    ],
    termos: ['score', 'divergencia'],
  },
  {
    titulo: 'Indicadores do gráfico',
    texto: [
      'Indicadores resumem como o preço se comportou nos últimos dias. Eles ajudam a ler o momento, mas descrevem o passado e não garantem o futuro.',
      'O Nox usa o RSI, que mostra se o preço subiu ou caiu rápido demais, e o MACD, que mostra se a tendência está ganhando força. A lua só enche quando os dois concordam.',
    ],
    termos: ['rsi', 'macd'],
  },
  {
    titulo: 'Volume, volatilidade e sentimento',
    texto: [
      'Volume é quanto foi negociado. Um movimento com volume alto costuma ser mais confiável que um com volume baixo.',
      'Volatilidade é o tamanho das oscilações. Quanto maior, mais rápido se ganha ou se perde.',
      'Sentimento é o humor das notícias e das redes sobre o ativo, que muitas vezes move o preço antes dos indicadores.',
    ],
    termos: ['sentimento', 'ml'],
  },
]

export default function Aprendizado() {
  return (
    <>
      <div className="px-5 pb-5 pt-9">
        <h1 className="font-serif text-[2.1rem] font-medium leading-tight tracking-tight">Aprender</h1>
        <p className="mt-2 text-[15px] leading-relaxed text-nevoa">
          O mínimo para entender um sinal antes de decidir qualquer coisa.
        </p>
      </div>
      <div className="border-t border-linha">
        {TEMAS.map((t, i) => (
          <details key={t.titulo} className="border-b border-linha px-5 py-5" open={i === 0}>
            <summary className="cursor-pointer font-serif text-xl">{t.titulo}</summary>
            <div className="mt-3 max-w-[62ch] space-y-3 font-serif text-[1.1rem] leading-[1.65]">
              {t.texto.map((p) => <p key={p}>{p}</p>)}
            </div>
            <dl className="mt-5 space-y-4">
              {t.termos.map((id) => (
                <div key={id}>
                  <dt className="font-semibold">{TERMOS[id].nome}</dt>
                  <dd className="mt-0.5 text-[15px] leading-relaxed text-nevoa">{TERMOS[id].texto}</dd>
                </div>
              ))}
            </dl>
          </details>
        ))}
      </div>
    </>
  )
}
