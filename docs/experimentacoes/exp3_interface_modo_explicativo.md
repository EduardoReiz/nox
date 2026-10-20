# Experimentação 3 – Interface React e Modo Explicativo

Situação: **Parcialmente realizado** (20/10/2026). As telas estão prontas e funcionam com dados simulados e reais. Falta o passo 5, a avaliação com três pessoas de fora da equipe.

- **Objetivo:** verificar como apresentar a recomendação, o score e a explicação de forma clara para o investidor iniciante (RNE-002).

- **O que foi testado:** o frontend foi construído do zero em React. Ficaram prontas quatro telas:
  - **Hoje:** uma lua para cada ativo, com a fase mostrando a confiança, mais o gráfico de 7 dias do BTC e o acesso ao Aprendizado;
  - **Feed de Sinais;**
  - **Modo Explicativo;**
  - **Aprendizado.**

  A API do backend em FastAPI, prevista na seção 19.1, passou a entregar os sinais calculados com os dados reais da Binance.

- **Como foi testado:**
  1. o formato de dados de um sinal foi definido em `docs/contrato_sinal.md`: ativo, ação, score, contribuição de cada componente, divergência, texto explicativo, aviso de risco e instantes;
  2. foram criados cinco sinais simulados (`frontend/src/dados/sinais_simulados.json`): comprar com confiança alta, vender, manter com divergência, manter neutro e comprar sem ML. As forças foram escolhidas à mão, mas o score, a ação e o texto foram gerados pelas regras do backend (`experimentos/exp3_interface/gerar_simulados.py`), para que o simulado seja igual ao que a API entregaria;
  3. foram construídos o feed, a linha de sinal e o painel do Modo Explicativo, com o aviso de risco (RF-013);
  4. a fonte de dados foi trocada de simulada (`VITE_FONTE=simulado`) para a API real, e as telas mudaram sem nenhuma alteração nos componentes;
  5. a avaliação com participantes ainda será feita, com o roteiro abaixo.

- **Resultado ou evidência:**
  - As telas funcionam em tela de celular com as duas fontes de dados, sem erros no console do navegador.
  - Quando os dados são simulados, uma faixa abaixo do cabeçalho avisa que não são preços nem sinais reais, para que nenhuma captura seja confundida com dados reais.
  - Telas e requisitos:

  | Tela | O que mostra | Requisitos |
  | --- | --- | --- |
  | Hoje | uma lua por ativo (fase = confiança), ação sugerida, gráfico de 7 dias do BTC, preço e variação em 24 h, horário da atualização | RF-009, RNF-006 |
  | Sinais | uma linha por ativo, do mais ao menos confiante, com lua, preço, ação, confiança, alerta de divergência e horário | RF-008, RF-009, RF-013 |
  | Modo Explicativo | ação e confiança, explicação em linguagem simples, quadro de divergência, contribuição e peso de cada componente, componentes ausentes, números técnicos sob demanda e aviso de risco | RF-005, RF-013, RNE-002, RNE-003 |
  | Aprendizado | os três temas do protótipo (risco, indicadores, volume, volatilidade e sentimento) e o glossário | RF-014 |

  - Termos técnicos (confiança, RSI, MACD, divergência, sentimento, ML) abrem uma explicação curta com um toque (RNF-001).

- **Aprendizados:**
  - Definir primeiro o formato do sinal permitiu construir as telas com dados simulados e depois ligá-las à API sem retrabalho.
  - Gerar os sinais simulados com o próprio código do backend evitou exemplos impossíveis, como um score que não bate com os componentes.
  - Ver os dados reais na tela revelou incoerências que os testes automáticos não pegaram:
    - o RSI de 57 era chamado de "neutro" no texto, mas puxava o cálculo para baixo (corrigido na Experimentação 4);
    - um componente aparecia como "neutro" na barra enquanto o texto dizia "levemente para baixa";
    - os pesos arredondados somavam 101%.

    O número, o texto e a tela precisam usar as mesmas regras.
  - Identidade visual. O protótipo do Figma feito no 2º Período foi substituído por uma identidade nova, decidida em 20/10/2026, porque não comunicava o produto. O nome Nox vem de "noite" em latim, e o mercado de cripto não fecha, então a interface usa um céu noturno. A peça central é a **lua**: a confiança do sinal é a fase da lua, de nova (0) a cheia (100), e a partir de 60% cheia o Nox sugere agir. A lua cresce pela esquerda, como no céu do hemisfério sul. Para o iniciante, a lua explica o score sem exigir que ele leia números.
    - Cores: céu índigo (#151A36) como fundo, luar (#EEE7D0) no texto e nas luas, verde-aurora para alta, rosa para queda e âmbar só nos avisos.
    - Fontes: Newsreader, uma serifa de leitura, nas explicações, que são o centro do produto; Figtree na interface e nos números.
    - Movimento: um único, ao abrir a tela, quando as luas enchem até a fase. Quem ativou "reduzir movimento" no sistema vê a fase direto.
  - Escolhas que seguem a especificação e diferem do protótipo antigo:
    - não há telas de PIX, depósito ou transferência, porque o Nox é informativo e não movimenta dinheiro (RNE-007);
    - o cadastro não vai pedir CPF, por minimização de dados (seção 18.2, LGPD);
    - o gráfico usa os preços reais, e não uma imagem fixa;
    - as telas de Sinais e Modo Explicativo, que não existiam no protótipo, passaram a ser o caminho principal.

- **Limitações identificadas:**
  - A clareza da explicação ainda não foi avaliada por pessoas de fora da equipe.
  - Login, cadastro e verificação em duas etapas (RF-010) ainda não foram implementados; as telas abrem direto, sem conta.
  - A tela de notícias aguarda a coleta de sentimento (RF-004).
  - O texto explicativo é montado a partir de frases fixas e pode ficar longo quando há divergência.

- **Próximos passos:**
  - aplicar o roteiro de avaliação com três pessoas e registrar as respostas;
  - implementar o login e o cadastro sobre o backend Python (RF-010), já com as falhas da revisão do protótipo de referência corrigidas;
  - adicionar à tela Hoje o gráfico do RSI e do MACD.

## Roteiro da avaliação com participantes (passo 5)

Participantes: três pessoas de fora da equipe, de preferência sem experiência com análise técnica. Usar a versão com dados simulados (`VITE_FONTE=simulado npm run dev`), para que todos vejam os mesmos sinais.

1. Mostrar o Feed de Sinais e perguntar: "Para qual moeda o Nox está mais confiante? O que ele sugere?"
2. Abrir o Modo Explicativo do Bitcoin e pedir: "Explique, com suas palavras, por que o Nox sugeriu comprar."
3. Abrir o Modo Explicativo da Solana e perguntar: "Por que aqui ele sugere manter? O que é essa divergência?"
4. Perguntar: "O Nox vai comprar ou vender por você?" (verifica se o aviso de risco foi entendido).
5. Perguntar: "Que palavra ou parte da tela você não entendeu?"

| Participante | Pergunta 1 | Pergunta 2 | Pergunta 3 | Pergunta 4 | Pergunta 5 |
| --- | --- | --- | --- | --- | --- |
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

Critério: a explicação é considerada clara se pelo menos duas das três pessoas responderem corretamente às perguntas 2, 3 e 4.
