# Experimentação 4 – Indicadores técnicos e estrutura do score

Situação: **Realizado** (20/10/2026), com pesos e limites ainda provisórios. Falta conferir alguns valores com uma plataforma de gráficos.

- **Objetivo:** garantir que o RSI e o MACD sejam calculados corretamente e testar se a composição do score (RNE-001), a redução por divergência (RNE-003) e o limiar de ação (RNE-008) produzem resultados coerentes.

- **O que foi testado:**
  - as funções `rsi` (14 períodos, suavização de Wilder) e `macd` (12/26/9, com indicação de cruzamento de alta ou de baixa), em `backend/nox/domain/indicadores.py`. Foram escritas à mão, sem biblioteca de análise técnica. As médias começam pela média simples dos primeiros períodos, o que corrige o ponto levantado na revisão do protótipo de referência;
  - o cálculo do score, a regra de divergência, o limiar de ação e a geração do Sinal de Recomendação com o texto do Modo Explicativo e o aviso de risco, em `backend/nox/domain/score.py`.

- **Como foi testado:**
  1. as funções foram escritas em Python na camada domain, sem dependência de bancos ou APIs (RNF-008);
  2. os indicadores foram calculados sobre as 999 velas de 1 hora de BTCUSDT, ETHUSDT e SOLUSDT obtidas na Experimentação 1;
  3. os valores foram comparados, vela a vela, com os da biblioteca de análise técnica `ta` (`experimentos/exp4_indicadores/comparar.py`);
  4. foram escritos testes com Pytest para casos conhecidos:
     - preços sempre em alta, sempre em baixa e constantes;
     - a tabela de exemplo de RSI publicada pela StockCharts;
     - cruzamentos do MACD;
     - os mínimos de histórico (RNE-004);
     - cada regra do score;
  5. foi montada a planilha de cenários do score, com e sem divergência (`cenarios.py`, que gera `cenarios_score.csv`), e o score foi calculado para cada hora dos dados reais.

- **Estrutura do score adotada.** A fórmula do documento foi mantida, e foi definido o que cada termo significa:
  - cada componente vira uma **força** de -1 (aponta queda) a +1 (aponta alta);
  - a **direção** do sinal é a da média ponderada das forças;
  - a **pontuação S** de cada componente, de 0 a 100, é quanto ele apoia essa direção; um componente neutro ou contrário vale 0;
  - **Score** = w₁ · S(técnico) + w₂ · S(sentimento) + w₃ · S(ML), e **Score final** = Score · (1 − r) quando há divergência crítica.

  Assim o score mede confiança, e o mesmo limiar de 60 vale para comprar e para vender.

  | Parâmetro | Valor provisório | Observação |
  | --- | --- | --- |
  | Pesos w₁ / w₂ / w₃ | 0,5 / 0,3 / 0,2 | quem estiver ausente tem o peso redistribuído entre os presentes |
  | Força do RSI | 0 entre 40 e 60; cresce até +1 em 30 e até −1 em 70 | leitura clássica de sobrevenda e sobrecompra, com faixa neutra |
  | Força do MACD | tanh(histograma ÷ desvio-padrão das últimas 100 velas) | normaliza o MACD, que está na unidade do preço |
  | Componente técnico | 0,5 · RSI + 0,5 · MACD | |
  | Divergência crítica | técnico e sentimento em sentidos opostos, os dois com força de pelo menos 0,3 | |
  | Redução r | 0,3 | |
  | Limiar de ação | 60 | abaixo dele, "manter" (RNE-008) |
  | Histórico mínimo | 200 velas | resultado da comparação dos indicadores (ver Aprendizados) |
  | Dados atuais | a última vela fechada tem no máximo um intervalo de atraso | senão não há sinal novo (RNE-004) |
  | Sentimento | só medições com "expira em" no futuro | RNE-006 |

- **Resultado ou evidência:**

  Indicadores do Nox comparados com a biblioteca `ta`:

  | Ativo | Maior diferença no RSI (primeiras velas) | Maior diferença no RSI (após 200 velas) | Maior diferença no MACD (após 200 velas) |
  | --- | --- | --- | --- |
  | BTCUSDT | 5,87 pontos | 0,000007 | 0,0003 |
  | ETHUSDT | 5,43 pontos | 0,000003 | 0,00001 |
  | SOLUSDT | 5,48 pontos | 0,000002 | 0,000001 |

  Os seis primeiros valores de RSI da tabela da StockCharts (70,53; 66,32; 66,55; 69,41; 66,36; 57,97) foram reproduzidos exatamente.

  Planilha de cenários (forças de −1 a +1; "—" é componente ausente):

  | Cenário | Técnico | Sentimento | ML | Score | Ação |
  | --- | --- | --- | --- | --- | --- |
  | Tudo aponta alta com força | 0,9 | 0,8 | 0,8 | 85 | comprar |
  | Tudo aponta queda com força | −0,9 | −0,8 | −0,8 | 85 | vender |
  | Técnico forte, sem sentimento e sem ML | 0,8 | — | — | 80 | comprar |
  | Técnico moderado, sem sentimento e sem ML | 0,5 | — | — | 50 | manter |
  | Técnico forte, sentimento neutro | 0,9 | 0,0 | — | 56 | manter |
  | Técnico alta, sentimento levemente negativo | 0,8 | −0,2 | — | 50 | manter |
  | Técnico alta, sentimento muito negativo (divergência) | 0,8 | −0,7 | — | 50 → 35 | manter |
  | Técnico queda, sentimento muito positivo (divergência) | −0,8 | 0,7 | — | 50 → 35 | manter |
  | Técnico alta, sentimento negativo e ML a favor (divergência) | 0,8 | −0,6 | 0,9 | 58 → 41 | manter |
  | Técnico neutro, sentimento e ML muito positivos | 0,0 | 1,0 | 1,0 | 50 | manter |
  | Sinais fracos em todos os componentes | 0,3 | 0,2 | 0,25 | 26 | manter |
  | Técnico moderado de alta, sentimento e ML de queda (divergência) | 0,5 | −0,5 | −0,4 | 26 → 18 | manter |

  Dados reais, só com o componente técnico (cada hora de 800 horas por ativo, de setembro a outubro de 2026):

  | Ativo | Manter | Comprar | Vender | Score mediano | 10% maiores scores acima de |
  | --- | --- | --- | --- | --- | --- |
  | BTCUSDT | 782 (98%) | 2 | 16 | 17 | 45 |
  | ETHUSDT | 773 (97%) | 12 | 15 | 18 | 44 |
  | SOLUSDT | 796 (99,5%) | 0 | 4 | 19 | 42 |

  Exemplo real de explicação gerada (BTCUSDT, 20/10/2026, 14h UTC): "O Nox sugere MANTER BTCUSDT, com confiança 7 de 100. No gráfico, o RSI está em 57, numa faixa neutra (entre 40 e 60), e o MACD acabou de cruzar para cima, um sinal de que a alta está ganhando força. Os sinais apontam levemente para alta, mas a confiança está abaixo de 60, o mínimo para o Nox sugerir comprar ou vender. Este cálculo não usou o sentimento de mercado nem a previsão de Machine Learning."

  Os 42 testes automatizados do backend passam. As evidências estão em `experimentos/exp4_indicadores/evidencias/`.

- **Aprendizados:**
  - A diferença apontada na revisão do protótipo se confirmou na prática. Começar a média pelo primeiro preço (como faz a biblioteca `ta`) ou pela média simples (como faz o Nox) muda o RSI em até 6 pontos nas primeiras velas. Depois de cerca de 200 velas as duas formas coincidem. Por isso, o mínimo de 15 preços da RNE-004 permite calcular o RSI, mas não garante um valor estável, e o Nox passou a exigir 200 velas antes de gerar um sinal.
  - Na tabela da StockCharts os preços aparecem com duas casas, mas o cálculo usa quatro; com os preços arredondados, o primeiro RSI dá 70,46. Valores de referência precisam vir com a precisão original.
  - O RSI e o MACD costumam discordar. O RSI, na leitura clássica, aponta reversão ("caiu demais, pode voltar"); o MACD aponta a tendência ("a queda tem força"). Numa queda forte os dois se anulam, e isso aconteceu em cerca de 17% a 19% das horas. O efeito é desejável para o público iniciante: o Nox não manda vender no fundo nem comprar enquanto o preço ainda cai, e o sinal técnico só fica forte quando os dois concordam (por exemplo, RSI baixo com o MACD virando para cima).
  - A primeira versão usava a força do RSI em linha reta, (50 − RSI) / 20. O teste com dados reais mostrou uma explicação contraditória: o texto dizia que o RSI de 57 estava neutro e que o MACD tinha cruzado para cima, mas concluía que os sinais apontavam para baixa, porque o RSI de 57 já contava como força de queda. A faixa neutra entre 40 e 60 corrigiu isso. A explicação precisa usar exatamente as mesmas faixas do cálculo.
  - Com esses parâmetros o Nox é muito conservador: em 97% a 99,5% das horas a sugestão é "manter". Os sinais de comprar ou vender apareceram de 4 a 27 vezes em 800 horas, conforme o ativo. Isso combina com a RNE-008, mas pode ser conservador demais; o equilíbrio certo só pode ser medido com backtesting.
  - Quando há sentimento, o componente técnico sozinho não alcança 60: mesmo com força 0,9, o score fica em 56 se o sentimento for neutro. Na prática, comprar ou vender passa a exigir confirmação de mais de uma fonte, o que precisa ficar claro no Modo Explicativo.
  - O MACD está na unidade do preço (centenas para o BTC, centésimos para o SOL). Dividir o histograma pela sua variação recente resolveu a normalização e deu valores comparáveis entre os ativos.

- **Limitações identificadas:**
  - A comparação com uma plataforma de gráficos (por exemplo, TradingView) ainda não foi feita; a referência usada foi uma biblioteca.
  - O sentimento e o ML entraram só nos cenários, com valores escolhidos à mão: ainda não existe coleta de sentimento (RF-004) nem modelo treinado.
  - Os pesos, os limites e o fator r não têm calibração. Indicadores descrevem o passado, e esta prova de conceito não mostra se as recomendações acertam; isso exige backtesting em períodos posteriores.
  - O texto do Modo Explicativo é montado a partir de frases fixas. A forma definitiva de gerá-lo ainda será definida (RF-005).

- **Próximos passos:** conferir alguns valores com uma plataforma de gráficos; levar o formato do sinal para a tela do Modo Explicativo (Experimentação 3); planejar o backtesting para calibrar pesos, limiar e fator r.
