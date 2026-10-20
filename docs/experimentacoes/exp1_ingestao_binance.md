# Experimentação 1 – Ingestão de dados de mercado da Binance em Python

Situação: **Realizado** (execução em 20/10/2026).

- **Objetivo:** verificar se é viável obter preço e volume de criptoativos pela API pública da Binance usando Python e quais restrições isso impõe ao bloco de Ingestão.

- **O que foi testado:** o fluxo completo previsto: requisição de um ativo e intervalo, recebimento da resposta, conversão para o formato interno e validação dos registros. Também foram testados o histórico longo em várias páginas, a conexão contínua por WebSocket e o comportamento diante de quedas de rede e de limite de requisições.

- **Como foi testado:** o script `experimentos/exp1_ingestao_binance/executar.py` executou os seis passos do procedimento:
  1. consultou as últimas 1000 velas de 1 hora de BTCUSDT, ETHUSDT e SOLUSDT pelo endpoint `/api/v3/klines`, sem chave de API;
  2. gravou o início e o fim da resposta crua de cada ativo (`resposta_bruta_*.json`);
  3. converteu cada vela para a estrutura ativo, intervalo, instante, abertura, máxima, mínima, fechamento, volume e fonte (`velas_*_1h.csv`);
  4. verificou valores inválidos, duplicidades, ordem temporal e lacunas; além disso, baixou o histórico do BTCUSDT desde 01/01/2026 em páginas de 1000 velas;
  5. manteve uma conexão WebSocket com o stream de velas de 1 minuto do BTCUSDT por 3 minutos (`websocket_BTCUSDT_1m.jsonl`);
  6. simulou falhas: queda de rede (endereço que recusa conexão), duas respostas HTTP 429 com `Retry-After` antes da resposta real e perda da conexão WebSocket.

  O código validado já foi transformado no primeiro módulo da camada infrastructure (`backend/nox/infrastructure/binance.py` e `binance_ws.py`). As regras de validação ficaram na camada domain (`backend/nox/domain/mercado.py`). Os dois têm testes automatizados com Pytest.

- **Resultado ou evidência:**

  | Item | Resultado |
  | --- | --- |
  | Velas por ativo | 1000 recebidas, 999 fechadas aproveitadas (08/09 a 20/10/2026) |
  | Tempo de cada requisição | entre 0,6 s e 1,4 s |
  | Inválidas, duplicadas, fora de ordem, lacunas | nenhuma nos três ativos |
  | Histórico desde 01/01/2026 (BTCUSDT) | 7022 velas em 8 páginas, 4,8 s, sem lacunas |
  | Peso de requisição consumido | 28 de 6000 por minuto, ao fim da coleta |
  | WebSocket (3 min) | 89 mensagens (cerca de uma a cada 2 s) e 3 velas fechadas |
  | Queda de rede | 4 tentativas com espera de 0,5 s, 1 s e 2 s; desistência em 3,5 s com erro registrado |
  | HTTP 429 simulado | o cliente esperou o tempo do `Retry-After` duas vezes e obteve os dados na terceira requisição |
  | Queda do WebSocket | reconexão automática com espera de 1, 2, 4 e 8 s |

  Os arquivos estão em `experimentos/exp1_ingestao_binance/evidencias/`; o `resumo.json` reúne os números e o `execucao.log` registra as tentativas e os erros.

- **Aprendizados:**
  - A resposta da Binance é uma lista de listas, sem nomes de campos, e os preços chegam como texto, para não perder casas decimais. A conversão para o formato interno precisa ser feita antes da gravação, como previsto.
  - O horário vem em milissegundos desde 1970, em UTC. O Nox guarda todos os instantes em UTC e só converte para o horário de Brasília na tela.
  - A última vela da resposta ainda está aberta e muda até o fim do intervalo. Se ela fosse gravada, o RSI e o MACD seriam calculados sobre um preço provisório. O cliente descarta essa vela; no WebSocket, cada mensagem informa se a vela já fechou.
  - Na primeira execução, a porta 9443 do WebSocket, a mais citada na documentação, estava bloqueada na rede usada. A porta 443 funcionou na hora. O Nox passou a usar a 443, e a reconexão automática foi testada de verdade nessa falha.
  - Os limites de requisição não são problema neste volume: a coleta inteira usou menos de 1% do limite por minuto. O cabeçalho `x-mbx-used-weight-1m` permite acompanhar o consumo.

- **Limitações identificadas:**
  - O erro 429 foi simulado, porque provocar um 429 real exigiria abusar da API e poderia bloquear o IP (HTTP 418).
  - O WebSocket ficou ligado por minutos, e não por horas. A Binance encerra cada conexão após 24 horas, e isso ainda precisa ser observado numa execução longa.
  - Lacunas causadas por manutenção da exchange não apareceram no período coletado. O validador as detecta, mas ainda não foi definido como preenchê-las.
  - Só a Binance foi testada; nomes de ativos em outras exchanges continuam como ponto a avaliar.

- **Próximos passos:** gravar as velas coletadas no InfluxDB e no PostgreSQL (Experimentação 2) e usar a mesma série nos indicadores (Experimentação 4).
