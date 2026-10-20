// Explicações curtas dos termos técnicos, a um clique (RNF-001, RF-014).
export const TERMOS = {
  score: {
    nome: 'Score de confiança',
    texto:
      'Número de 0 a 100 que mostra o quanto os sinais concordam entre si. Abaixo de 60 o Nox sugere manter, porque os sinais ainda são fracos para agir.',
  },
  rsi: {
    nome: 'RSI (Índice de Força Relativa)',
    texto:
      'Mede, de 0 a 100, a força das altas e quedas recentes. Abaixo de 30 o preço caiu rápido e costuma voltar a subir; acima de 70 subiu rápido e costuma corrigir. Entre 40 e 60 é neutro.',
  },
  macd: {
    nome: 'MACD',
    texto:
      'Compara uma média rápida com uma média lenta dos preços para mostrar se a tendência está ganhando ou perdendo força. Quando a linha cruza para cima, a alta ganha força; para baixo, a queda ganha força.',
  },
  divergencia: {
    nome: 'Divergência',
    texto:
      'Quando o gráfico aponta um lado e o sentimento das notícias aponta o outro. Nesses casos o Nox reduz a confiança, porque a situação é incerta.',
  },
  sentimento: {
    nome: 'Sentimento do mercado',
    texto:
      'Uma nota de positivo a negativo tirada de notícias e redes sociais sobre o ativo. Ela vale por pouco tempo, porque o humor do mercado muda rápido.',
  },
  ml: {
    nome: 'Machine Learning',
    texto:
      'Um modelo treinado com dados do passado para estimar o próximo movimento. Ainda não faz parte do cálculo; está previsto para os próximos períodos.',
  },
}
