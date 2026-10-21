import { TERMOS } from '../dados/termos'

// Aprendizado (RF-014): os três temas previstos e o que o Nox é e não é.
const TEMAS = [
  {
    titulo: 'O que é o Nox, e o que não é',
    texto: [
      'O Nox lê o mercado de criptoativos e mostra, em linguagem simples, o que os indicadores estão indicando. Cada leitura vem com a explicação do cálculo, para você entender e discordar se quiser.',
      'Ele não é uma corretora: não guarda dinheiro, não compra nem vende por você e não pede seus dados bancários. Também não é consultoria de investimentos, e por isso não diz o que você deve fazer.',
      'Quem decide é sempre você. O Nox é só uma fonte a mais para você decidir com mais calma.',
    ],
    termos: ['score'],
  },
  {
    titulo: 'Risco',
    texto: [
      'Criptoativos podem subir ou cair muito em poucas horas. Nenhuma ferramenta, nem o Nox, acerta sempre.',
      'O preço pode cair depois de um sinal de alta, e subir depois de um sinal de queda. Indicadores descrevem o passado e não garantem o futuro.',
      'Invista só o que pode perder sem comprometer contas e reservas. Dividir o dinheiro entre ativos diferentes reduz o impacto de uma queda.',
      'Desconfie de promessas de lucro rápido e de grupos que vendem sinais sem mostrar o motivo.',
    ],
    termos: ['divergencia'],
  },
  {
    titulo: 'Indicadores do gráfico',
    texto: [
      'Indicadores resumem como o preço se comportou nos últimos dias. Eles ajudam a ler o momento, mas descrevem o passado.',
      'O RSI mostra se o preço subiu ou caiu rápido demais. Abaixo de 30, a queda foi forte e o preço costuma reagir; acima de 70, a alta foi forte e o preço costuma corrigir. Entre 40 e 60, está neutro.',
      'O MACD compara uma média rápida e uma lenta dos preços para mostrar se a tendência está ganhando força. Quando a linha cruza para cima, a alta ganha força; para baixo, a queda ganha força.',
      'O Nox junta os dois. A lua só enche quando eles concordam, e por isso, na maior parte do tempo, a leitura é neutra: sinais fracos não merecem destaque.',
    ],
    termos: ['rsi', 'macd'],
  },
  {
    titulo: 'Volume, volatilidade e sentimento',
    texto: [
      'Volume é quanto foi negociado. Um movimento com volume alto costuma ser mais confiável que um com volume baixo.',
      'Volatilidade é o tamanho das oscilações. Quanto maior, mais rápido se ganha ou se perde.',
      'Sentimento é o humor das notícias e das redes sobre o ativo, que muitas vezes move o preço antes dos indicadores. Ele ainda não entra na leitura do Nox.',
    ],
    termos: ['sentimento', 'ml'],
  },
  {
    titulo: 'Como ler a lua e a explicação',
    texto: [
      'Cada lua mostra a confiança de uma leitura, de 0 (lua nova) a 100 (lua cheia). Quanto mais cheia, mais os indicadores concordam.',
      'A partir de 60, o Nox destaca um sinal de alta ou de queda, na cor verde ou rosa. Abaixo disso, a leitura é neutra.',
      'Toque num ativo para abrir a explicação. Ela diz o que pesou no cálculo, quanto cada parte vale e o que ficou de fora. Os números técnicos aparecem só se você quiser ver.',
    ],
    termos: [],
  },
]

export default function Aprendizado() {
  return (
    <>
      <div className="px-5 pb-5 pt-9">
        <h1 className="font-serif text-[2.1rem] font-medium leading-tight tracking-tight">Aprender</h1>
        <p className="mt-2 text-[15px] leading-relaxed text-nevoa">
          O mínimo para entender uma leitura do Nox antes de decidir qualquer coisa.
        </p>
      </div>
      <div className="border-t border-linha">
        {TEMAS.map((t, i) => (
          <details key={t.titulo} className="border-b border-linha px-5 py-5" open={i === 0}>
            <summary className="cursor-pointer font-serif text-xl">{t.titulo}</summary>
            <div className="mt-3 max-w-[62ch] space-y-3 font-serif text-[1.1rem] leading-[1.65]">
              {t.texto.map((p) => <p key={p}>{p}</p>)}
            </div>
            {t.termos.length > 0 && <dl className="mt-5 space-y-4">
              {t.termos.map((id) => (
                <div key={id}>
                  <dt className="font-semibold">{TERMOS[id].nome}</dt>
                  <dd className="mt-0.5 text-[15px] leading-relaxed text-nevoa">{TERMOS[id].texto}</dd>
                </div>
              ))}
            </dl>}
          </details>
        ))}
      </div>
    </>
  )
}
