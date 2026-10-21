# Experimentação 5 – Protótipo de referência full-stack e modelo físico de dados

Situação: **Realizado** (21/10/2026). Antes era "Parcialmente realizado": só havia revisão de código, e o sistema nunca tinha sido executado.

- **Objetivo:** visualizar o funcionamento completo do Nox (tela, API e banco) antes de definir a implementação final e transformar o modelo conceitual em tabelas reais.

- **O que foi testado:** o protótipo de referência de setembro de 2025 (`experimentos/exp5_prototipo_antigo/prototipo`): backend em TypeScript com Fastify, Prisma e PostgreSQL, e frontend em React com Vite. Desta vez ele foi executado, e não só lido.

- **Como foi testado:** o script `testes/rodar.mjs` e os comandos do README da experimentação executaram:
  1. a validação do schema do Prisma, com o código exatamente como estava;
  2. a instalação das dependências e a subida do servidor;
  3. as proteções de segurança contra um PostgreSQL real: rota de preços, login com verificação em duas etapas e compatibilidade do código com aplicativos autenticadores;
  4. o RSI e o MACD do protótipo sobre as 999 velas reais de BTCUSDT da Experimentação 1, comparados com os do núcleo Python;
  5. o build do frontend e a leitura das telas.

  Para o servidor subir, foram necessárias correções numa cópia descartável (o protótipo original ficou intacto): schema reformatado e completado, e duas dependências trocadas de versão.

- **Resultado ou evidência:**

  | Item | Resultado |
  | --- | --- |
  | Validação do schema do Prisma | **falha, com 30 erros**: nenhuma tabela seria criada e o backend não iniciaria |
  | Causa 1 | os blocos `generator`, `datasource` e os `enum` foram escritos numa linha só, sintaxe que o Prisma não aceita; os 30 erros vêm em cascata disso |
  | Causa 2 (após reformatar) | o campo `@index` é inválido (deveria ser `@@index`) |
  | Causa 3 (após corrigir o índice) | 5 relações sem o campo oposto: Ativo não declara Posição, Transação, Sinal e Item de Lista, e o log de auditoria não tem relação com o Usuário |
  | Histórico de migrações | não existe; `prisma migrate deploy`, o comando do contêiner da API, responde "No migration found" e não cria tabela |
  | Testes automatizados | nenhum arquivo, embora o Vitest esteja configurado |
  | Subir o servidor com as dependências declaradas | **falha**: `@fastify/cors` 10 e `@fastify/helmet` 13 exigem Fastify 5, e o projeto usa Fastify 4; funcionou com `cors` 9 e `helmet` 11 |
  | Rota de recebimento de preços | **aceita qualquer chamada sem login** (204) e criou um ativo falso ("FALSO"); sem validação, um preço negativo sem data devolveu erro 500 |
  | Verificação em duas etapas | `/auth/verify-2fa` **entregou os tokens de acesso só com e-mail e código, sem senha** (200) |
  | 2FA no cadastro | a rota de configuração marca a verificação como ativa **antes** de o usuário confirmar um código, o que pode trancá-lo fora da conta |
  | Compatibilidade com aplicativos autenticadores | **incompatível**: com o mesmo segredo, o servidor esperava 178806 e o aplicativo mostrava 216518; o código do aplicativo foi recusado (401). O servidor usa o texto do segredo como chave, e os aplicativos decodificam o segredo em base32 |
  | Detalhe do QR code | o nome da conta no QR é o identificador interno do usuário, e não o e-mail |
  | Notícias e sinais | a coleta de notícias é uma função vazia e nenhuma rota cria sinais: a lista de sinais ficou vazia |
  | Sessões | o token de renovação é emitido, mas nenhuma rota o usa, e o erro ao gravar a sessão é ignorado |
  | Cabeçalhos de segurança | o Helmet foi ligado com a política de conteúdo (CSP) desligada |
  | Frontend | compila (2733 módulos, 709 kB de JavaScript). Login e cadastro são simulados com uma espera fixa de 400 ms, o gráfico usa preços gerados por `Math.random`, o assistente devolve sempre a mesma resposta; só a tela do código de duas etapas chama a API. A tela pede senha de 6 caracteres, e o backend exige 8 |

  Indicadores do protótipo, calculados sobre as mesmas 999 velas:

  | Comparação com o núcleo Python | Maior diferença |
  | --- | --- |
  | RSI, todas as velas | 0,005 (só o arredondamento de 2 casas do protótipo) |
  | Linha do MACD, todas as velas | 185,66 |
  | Linha do MACD, após 200 velas | 0,0003 |
  | Histograma do MACD, todas as velas | 41,72 |
  | Histograma do MACD, após 200 velas | 0,0001 |
  | Último RSI e último histograma | iguais (57,05 e 9,49257379); mesmo cruzamento de alta |

  Os arquivos estão em `experimentos/exp5_prototipo_antigo/evidencias/`.

- **Aprendizados:**
  - A revisão de código registrada na versão 3.1 do documento acertou os problemas que apontou: o schema não passa na validação, não há migrações nem testes, a rota de preços não tem autenticação nem validação, o 2FA libera o acesso sem a senha e com código incompatível, a coleta de notícias está vazia e o modelo não tem perfil de risco nem preferências de alerta. A execução mostrou que o problema do schema era mais amplo do que o apontado (sintaxe dos blocos) e achou três falhas novas: as versões incompatíveis do Fastify, o 2FA ativado antes da confirmação e o QR com o identificador interno.
  - O RSI do protótipo estava certo: coincide com o do núcleo Python até o arredondamento. Só o MACD diverge no começo da série, porque a média exponencial parte do primeiro preço, e não da média simples. A diferença some depois de cerca de 200 velas, o que confirma, com a mesma conclusão da Experimentação 4, que o Nox deve exigir esse histórico antes de gerar um sinal.
  - Uma rotina que nunca foi executada esconde erros que a leitura não pega. Por isso o núcleo Python nasceu com testes automatizados para cada regra (RNF-008) e com um teste de ponta a ponta no navegador.
  - O campo de detalhes do Sinal antecipou a necessidade de guardar a justificativa junto com a recomendação; as lacunas do modelo motivaram a ligação entre Sentimento e Ativo e a entidade Preferência de Alerta da seção 18.1; e gravar preços no PostgreSQL deu origem à comparação da Experimentação 2.

- **Limitações identificadas:**
  - O protótipo foi executado com correções mínimas numa cópia descartável; o comportamento de uma instalação "do jeito que está" é o das falhas da tabela, ou seja, não sobe.
  - O Redis e as filas (BullMQ) constam das dependências, mas nenhum código as usa; não foram testados.
  - Não foi medido o limite de 300 requisições por minuto, nem foram feitos testes de carga.
  - O protótipo está em outra linguagem e não será aproveitado como código final.

- **Próximos passos:** o núcleo Python do Nox já corrige cada problema desta lista (RF-010, RNF-003, RNF-008). Falta publicar o sistema em servidor com HTTPS e repetir esta verificação de segurança contra o sistema publicado.
