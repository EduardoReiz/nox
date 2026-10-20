import Cabecalho from '../componentes/Cabecalho'
import { TERMOS } from '../dados/termos'

// Aprendizado (RF-014): os três temas do protótipo, em versão curta.
const TEMAS = [
  {
    titulo: 'Conceitos de risco',
    texto: [
      'Criptoativos podem subir ou cair muito em poucas horas. Nenhuma ferramenta, nem o Nox, acerta sempre.',
      'Invista só o que pode perder sem comprometer contas e reservas. Dividir o dinheiro entre ativos diferentes reduz o impacto de uma queda.',
      'Desconfie de promessas de lucro rápido e de grupos que vendem sinais sem mostrar o motivo.',
    ],
    termos: ['score', 'divergencia'],
  },
  {
    titulo: 'Indicadores técnicos',
    texto: [
      'Indicadores resumem o comportamento recente do preço. Eles descrevem o passado e ajudam a ler o momento, mas não garantem o futuro.',
      'O Nox usa o RSI, que mostra se o preço subiu ou caiu rápido demais, e o MACD, que mostra se a tendência está ganhando força. O sinal só fica forte quando os dois concordam.',
    ],
    termos: ['rsi', 'macd'],
  },
  {
    titulo: 'Volume, volatilidade e sentimento',
    texto: [
      'Volume é quanto foi negociado. Um movimento de preço com volume alto costuma ser mais confiável que um com volume baixo.',
      'Volatilidade é o tamanho das oscilações. Quanto maior, maior o risco de perder ou ganhar muito rápido.',
      'Sentimento é o humor das notícias e redes sociais sobre o ativo, que muitas vezes move o preço antes dos indicadores.',
    ],
    termos: ['sentimento', 'ml'],
  },
]

export default function Aprendizado() {
  return (
    <main className="mx-auto max-w-[440px] pb-10">
      <Cabecalho voltar titulo="Aprendizado" />
      <div className="space-y-4 px-[28px] pt-5">
        {TEMAS.map((t) => (
          <details key={t.titulo} className="cartao group p-4" open={t === TEMAS[0]}>
            <summary className="cursor-pointer font-inter text-[16px] font-semibold">{t.titulo}</summary>
            <div className="mt-3 space-y-2 text-sm leading-relaxed">
              {t.texto.map((p) => <p key={p}>{p}</p>)}
            </div>
            <dl className="mt-4 space-y-3 border-t border-moldura pt-3 text-sm">
              {t.termos.map((id) => (
                <div key={id}>
                  <dt className="font-semibold">{TERMOS[id].nome}</dt>
                  <dd className="text-texto-suave">{TERMOS[id].texto}</dd>
                </div>
              ))}
            </dl>
          </details>
        ))}
      </div>
    </main>
  )
}
