# Experimentação 3 – Interface React e Modo Explicativo

Situação: **Parcialmente realizado** (20/10/2026). As telas estão prontas e funcionam com dados simulados e reais. Falta o passo 5, a avaliação com três pessoas de fora da equipe.

- **Objetivo:** verificar como apresentar a recomendação, o score e a explicação de forma clara para o investidor iniciante (RNE-002).

- **O que foi testado:** o frontend foi construído do zero em React, a partir do protótipo de alta fidelidade no Figma (arquivo NOX-AI). Ficaram prontas quatro telas:
  - **Home:** segue o Figma, com o gráfico de preço do BTC, o cartão do BTC, o acesso à IA, Aprendizado e Notícias;
  - **Feed de Sinais;**
  - **Modo Explicativo;**
  - **Aprendizado.**

  A API do backend em FastAPI, prevista na seção 19.1, passou a entregar os sinais calculados com os dados reais da Binance.

- **Como foi testado:**
  1. o formato de dados de um sinal foi definido em `docs/contrato_sinal.md`: ativo, ação, score, contribuição de cada componente, divergência, texto explicativo, aviso de risco e instantes;
  2. foram criados cinco sinais simulados (`frontend/src/dados/sinais_simulados.json`): comprar com confiança alta, vender, manter com divergência, manter neutro e comprar sem ML. As forças foram escolhidas à mão, mas o score, a ação e o texto foram gerados pelas regras do backend (`experimentos/exp3_interface/gerar_simulados.py`), para que o simulado seja igual ao que a API entregaria;
  3. foram construídos o feed, o cartão de sinal e o painel do Modo Explicativo, com o aviso de risco (RF-013);
  4. a fonte de dados foi trocada de simulada (`VITE_FONTE=simulado`) para a API real, e as telas mudaram sem nenhuma alteração nos componentes;
  5. a avaliação com participantes ainda será feita, com o roteiro abaixo.

- **Resultado ou evidência:**
  - As telas funcionam no tamanho de celular do protótipo (440 px) com as duas fontes de dados, sem erros no console do navegador.
  - Quando os dados são simulados, a tela mostra o selo "Dados simulados", para que nenhuma captura seja confundida com dados reais.
  - Telas e requisitos:

  | Tela | O que mostra | Requisitos |
  | --- | --- | --- |
  | Home | gráfico de 7 dias do BTC, preço e variação em 24 h, sinal de maior confiança, acesso ao feed e ao Aprendizado, horário da atualização | RF-009, RNF-006 |
  | Feed de Sinais | um cartão por ativo com ação, barra de confiança (com a marca do limiar de 60), alerta de divergência e horário | RF-008, RF-009, RF-013 |
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
  - Adaptações em relação ao protótipo do Figma, para seguir a especificação:
    - os cartões "PIX" e "Transferência bancária / Depositar" foram trocados por "Sinais" e "Aprendizado", porque o Nox é informativo e não movimenta dinheiro (RNE-007);
    - o campo de CPF do cadastro não será usado, por minimização de dados (seção 18.2, LGPD);
    - o gráfico, que no Figma era uma imagem fixa, passou a ser desenhado com os preços reais;
    - as telas de Feed e Modo Explicativo, que não existiam no Figma, foram criadas no mesmo estilo visual (fundo escuro, cartões brancos arredondados, fontes Roboto, Inter e Joan).

- **Limitações identificadas:**
  - A clareza da explicação ainda não foi avaliada por pessoas de fora da equipe.
  - Login, cadastro e verificação em duas etapas (RF-010) ainda não foram implementados; as telas abrem direto, sem conta.
  - A tela de notícias aguarda a coleta de sentimento (RF-004).
  - O texto explicativo é montado a partir de frases fixas e pode ficar longo quando há divergência.

- **Próximos passos:**
  - aplicar o roteiro de avaliação com três pessoas e registrar as respostas;
  - implementar o login e o cadastro sobre o backend Python (RF-010), já com as falhas da revisão do protótipo de referência corrigidas;
  - adicionar à Home o gráfico do RSI e do MACD.

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
