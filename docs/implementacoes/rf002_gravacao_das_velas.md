# RF-002 – Gravação contínua das velas no PostgreSQL

Situação: **Implementado e testado** (21/10/2026). Antes era "Em desenvolvimento": a tabela e as consultas existiam (Experimentação 2), mas o sistema não gravava nada sozinho.

- **Objetivo:** guardar o histórico de mercado de cada ativo para consulta por período, como previsto no RF-002.

- **O que foi feito:** o serviço que calcula os sinais (`ServicoSinais`) passou a gravar, a cada ciclo, as velas fechadas de cada ativo que ainda não estão na tabela `observacao_mercado`. Uma vela fechada não muda, então só as novas são gravadas: na primeira vez, as 300 velas buscadas; depois, uma por hora. Se o banco falhar, o erro é registrado e o sinal continua sendo calculado.

- **Como foi testado:**
  1. 4 testes novos (`tests/test_gravacao_velas.py`): primeira gravação, gravação só da vela nova uma hora depois, falha do banco e serviço sem repositório;
  2. um ciclo real do processo agendado contra o PostgreSQL com a Binance: os seis ativos ficaram com as velas até a última hora fechada (11:00 UTC de 21/10/2026).

- **Resultado:** 116 testes passam. A tabela já tinha o histórico das Experimentações 1 e 2; as velas novas se somam a ele sem duplicar, porque a chave é (ativo, intervalo, instante).

- **Limitações:** o cálculo de cada ciclo ainda usa as 300 velas buscadas da Binance, e não as lidas do banco; a API do gráfico também. A retenção de velas de 1 minuto (30 dias) só vale quando houver essa coleta, que não existe: o Nox grava velas de 1 hora, sem prazo.

- **Próximos passos:** ler do banco o histórico longo (para o histórico de sinais e o backtesting) e coletar velas de 1 minuto pelo WebSocket, se o produto precisar.
