# Experimentação 2 – Organização e consulta de séries temporais

Situação: **Realizado** (execução em 20/10/2026). A decisão final de persistência está proposta ao fim e depende da confirmação da equipe.

- **Objetivo:** confirmar se o InfluxDB atende melhor que uma tabela no PostgreSQL às consultas de que o Nox precisa e definir a política de retenção do histórico.

- **O que foi testado:**
  - a gravação em ordem cronológica;
  - a unicidade de cada observação (ativo, intervalo e instante);
  - a detecção de lacunas;
  - a consulta por período.

  As duas implementações ficam em `backend/nox/infrastructure/series.py` e oferecem as mesmas operações: gravar, últimas N velas, período, média diária e lacunas. Assim os dois bancos responderam exatamente às mesmas perguntas, e o resto do sistema não depende de qual for escolhido.

- **Como foi testado:** o script `experimentos/exp2_series_temporais/executar.py` seguiu o procedimento previsto.
  1. Subiu PostgreSQL 16 e InfluxDB 2.7 com Docker Compose (`docker-compose.yml`). As senhas são geradas num arquivo `.env`, que não vai para o repositório.
  2. Gravou nos dois bancos o mesmo conjunto: as velas de 1 hora da Experimentação 1 mais o histórico do BTCUSDT desde 01/01/2026, num total de 9020 velas. Gravou também uma série de teste com três velas removidas de propósito, formando duas lacunas conhecidas.
  3. Executou as quatro consultas 30 vezes em cada banco e registrou a mediana do tempo:
     - últimas 200 velas de um ativo;
     - velas de um dia específico;
     - média por dia de um mês;
     - verificação de intervalos faltantes.
  4. Regravou uma vela já existente com outro preço, para ver se o banco duplica o registro ou o substitui.
  5. Repetiu tudo em escala: 90 dias de velas de **1 minuto** do BTCUSDT (129.601 velas). É o cenário de uso contínuo que motivou a escolha do InfluxDB.

- **Resultado ou evidência:**

  Correção: os dois bancos devolveram exatamente os mesmos resultados nas duas escalas, com a mesma quantidade de velas, as mesmas médias diárias (diferença 0,0) e as mesmas lacunas. Os dois acharam as duas lacunas plantadas na série de teste e nenhuma lacuna nos dados reais. Ao regravar uma vela, os dois mantiveram um único registro com o valor novo.

  Tempo das consultas (mediana, em milissegundos):

  | Consulta | PostgreSQL (9 mil velas de 1h) | InfluxDB (9 mil velas de 1h) | PostgreSQL (130 mil velas de 1m) | InfluxDB (130 mil velas de 1m) |
  | --- | --- | --- | --- | --- |
  | Últimas 200 velas | 0,5 | 10,4 | 1,0 | 28,3 |
  | Velas de um dia | 0,2 | 4,1 | 3,3 | 18,2 |
  | Média por dia de um mês | 0,4 | 3,5 | 12,4 | **8,5** |
  | Lacunas (histórico inteiro) | 2,4 | 19,1 | 43,6 | 247,9 |

  Escrita, espaço e memória:

  | Aspecto | PostgreSQL | InfluxDB |
  | --- | --- | --- |
  | Gravação de 130 mil velas | 1,9 s (68 mil por segundo) | 1,7 s (75 mil por segundo) |
  | Espaço em disco com 140 mil velas | 23 MB | 11,3 MB |
  | Memória do contêiner em uso | 48 MB | 200 MB |
  | Linguagem de consulta | SQL | Flux |
  | Retenção automática | não tem; exige rotina de limpeza ou particionamento | nativa, por bucket |

  Os números completos estão em `experimentos/exp2_series_temporais/evidencias/resumo.json`.

- **Aprendizados:**
  - No volume do Nox, o PostgreSQL foi mais rápido em quase todas as consultas, inclusive com 130 mil velas de 1 minuto. O InfluxDB só venceu na média por dia, que é a operação em que ele é especializado (`aggregateWindow`). Todas as consultas, nos dois bancos, ficaram muito abaixo da meta de 500 ms do RNF-002.
  - O InfluxDB usou metade do espaço em disco, graças à compressão de séries, e grava um pouco mais rápido. Essa vantagem cresce com o volume e pode pesar quando houver muitos ativos e anos de dados de minuto.
  - O InfluxDB usou cerca de quatro vezes mais memória. Num servidor pequeno ou num computador com 8 GB, como o usado nos testes, isso conta.
  - Escrever a consulta no Flux exige cuidado. Na primeira versão, a consulta "últimas 200 velas" levava 34 ms; cortar cada campo antes de juntar os campos (`tail` antes de `pivot`) baixou para 10 ms. No PostgreSQL a consulta óbvia já é a rápida, porque a chave primária (ativo, intervalo, instante) serve de índice.
  - A unicidade funciona nos dois, de formas diferentes. No PostgreSQL ela vem da chave primária e do `ON CONFLICT`. No InfluxDB, um ponto com as mesmas tags e o mesmo instante substitui o anterior sem aviso, então uma regravação com erro apaga o valor certo silenciosamente.
  - O Flux é uma linguagem própria e está sendo abandonado: o InfluxDB 3 voltou a usar SQL. O SQL do PostgreSQL já é trabalhado na disciplina de Banco de Dados.

- **Comparação com os critérios da seção 19.1:**

  | Critério | PostgreSQL | InfluxDB |
  | --- | --- | --- |
  | Consultar uma janela de tempo e agregar por período | fácil (SQL com `date_trunc` e funções de janela) | fácil (`range` e `aggregateWindow`), mas consultas de linha inteira exigem `pivot` |
  | Integração com Python | boa (psycopg) | boa (cliente oficial) |
  | Execução local simples em Docker | sim, 48 MB | sim, 200 MB |
  | Custo zero no ambiente acadêmico | sim | sim |
  | Curva de aprendizado da equipe | baixa, já vista em aula | maior (Flux, tags e campos, buckets) |

- **Decisão proposta:** usar só o PostgreSQL neste período e no próximo, inclusive para as séries de mercado, e rever a escolha quando o volume crescer. O ponto de revisão seria, por exemplo, muitos ativos com anos de dados de 1 minuto. Nesse momento as opções seriam o InfluxDB ou a extensão TimescaleDB, que acrescenta ao PostgreSQL compressão e retenção automática sem trocar de banco. A separação de responsabilidades da seção 18.2 continua valendo, porque as séries ficam numa tabela própria, com acesso isolado na camada infrastructure. A troca de banco, se vier, fica restrita a um arquivo, como esta experimentação mostrou.

- **Política de retenção proposta:** velas de 1 minuto por 30 dias e velas de 1 hora sem prazo (um ano de velas de 1 hora tem 8760 registros por ativo). A limpeza das velas de 1 minuto seria uma rotina diária. A política será confirmada quando o modelo de ML definir quanto histórico precisa.

- **Limitações identificadas:**
  - Os testes rodaram num único computador, com uma consulta por vez, sem carga concorrente nem gravação contínua durante as leituras.
  - O espaço do InfluxDB foi medido antes da compactação completa dos arquivos, e pode diminuir com o tempo.
  - Não foi testado o TimescaleDB.

- **Próximos passos:** confirmar a decisão com a equipe e com o orientador; atualizar a seção 18.2 se a decisão for mantida; ligar a coleta da Experimentação 1 à gravação no banco escolhido.
