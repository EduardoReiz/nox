# Experimentação 4 – Indicadores técnicos e estrutura do score

Situação: **Parcialmente realizado.** Os indicadores foram implementados em Python, testados e comparados (20/10/2026). A estrutura do score e a planilha de cenários ainda serão feitas.

- **Objetivo:** garantir que o RSI e o MACD sejam calculados corretamente e testar se a composição do score (RNE-001), a redução por divergência (RNE-003) e o limiar de ação (RNE-008) produzem resultados coerentes.

- **O que foi testado:** as funções `rsi` (14 períodos, suavização de Wilder) e `macd` (12/26/9, com indicação de cruzamento de alta ou de baixa) em `backend/nox/domain/indicadores.py`, escritas à mão, sem biblioteca de análise técnica. As médias começam pela média simples dos primeiros períodos, o que corrige o ponto levantado na revisão do protótipo de referência.

- **Como foi testado:**
  1. as duas funções foram escritas em Python na camada domain, sem dependências externas;
  2. foram calculadas sobre as 999 velas de 1 hora de BTCUSDT, ETHUSDT e SOLUSDT obtidas na Experimentação 1;
  3. os valores foram comparados, vela a vela, com os da biblioteca de análise técnica `ta` (script `experimentos/exp4_indicadores/comparar.py`);
  4. foram escritos testes com Pytest para casos conhecidos: preços sempre em alta (RSI 100), sempre em baixa (RSI 0) e constantes (RSI 50 e MACD 0); a tabela de exemplo de RSI publicada pela StockCharts; cruzamentos de alta e de baixa; e a exigência mínima de 15 preços para o RSI e de 35 para o MACD (RNE-004).

- **Resultado ou evidência:**

  | Ativo | Maior diferença no RSI (primeiras velas) | Maior diferença no RSI (após 200 velas) | Maior diferença no MACD (após 200 velas) |
  | --- | --- | --- | --- |
  | BTCUSDT | 5,87 pontos | 0,000007 | 0,0003 |
  | ETHUSDT | 5,43 pontos | 0,000003 | 0,00001 |
  | SOLUSDT | 5,48 pontos | 0,000002 | 0,000001 |

  Os seis primeiros valores de RSI da tabela da StockCharts (70,53; 66,32; 66,55; 69,41; 66,36; 57,97) foram reproduzidos exatamente. Os 26 testes automatizados do backend passam. As comparações vela a vela estão em `experimentos/exp4_indicadores/evidencias/comparacao_*.csv`, e o resumo, em `resumo.json`.

- **Aprendizados:**
  - A diferença apontada na revisão do protótipo se confirmou na prática: começar a média pelo primeiro preço (como faz a biblioteca `ta`) ou pela média simples (como faz o Nox) muda o RSI em até 6 pontos nas primeiras velas. Depois de cerca de 200 velas as duas formas coincidem.
  - Por isso, o mínimo de 15 preços da RNE-004 permite calcular o RSI, mas não garante um valor estável. A proposta é exigir pelo menos 200 velas de histórico antes de gerar um sinal, o que a coleta da Experimentação 1 atende com folga.
  - Na tabela da StockCharts os preços aparecem com duas casas, mas o cálculo usa quatro; com os preços arredondados, o primeiro RSI dá 70,46 em vez de 70,53. Valores de referência precisam vir com a precisão original.
  - O MACD está na mesma unidade do preço (centenas para o BTC, centésimos para o SOL), por isso precisa ser normalizado antes de entrar no score, como já previsto.

- **Limitações identificadas:**
  - A comparação com uma plataforma de gráficos (por exemplo, TradingView) ainda não foi feita; a referência usada foi uma biblioteca.
  - A estrutura do score, a normalização do MACD, o critério de divergência crítica e o fator de redução ainda não foram implementados.
  - Sem modelo de ML treinado, o componente de ML do score não pode ser testado.

- **Próximos passos:** conferir alguns valores com uma plataforma de gráficos; implementar o cálculo do score com pesos provisórios, a normalização do MACD, a regra de divergência e o limiar de 60 (RNE-008), com testes; montar a planilha de cenários com e sem divergência.
