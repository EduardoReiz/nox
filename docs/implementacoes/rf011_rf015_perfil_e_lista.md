# RF-011 e RF-015 – Perfil de risco, preferências de alerta e lista de ativos acompanhados

Situação: **Implementado e testado** (20/10/2026). Os dois requisitos estavam como "Proposto" e "Em análise".

- **Objetivo:**
  - RF-011: o usuário cadastra e altera o perfil de risco e as preferências de alerta.
  - RF-015: o usuário monta e edita a lista de ativos que acompanha.

  Os dois alimentam os alertas (RF-012) e o feed personalizado, sempre com coleta mínima e armazenamento protegido (RNE-005).

- **O que foi feito:**
  - **Modelo de dados** da seção 18.1 no PostgreSQL:
    - tabelas `ativo`, `lista_acompanhamento` e `preferencia_alerta`;
    - coluna `frequencia_alerta` no usuário.

    A entidade Ativo recebe automaticamente os ativos acompanhados pelo sistema.
  - **Ativos acompanhados:** passaram de três para seis (BTC, ETH, SOL, BNB, XRP e ADA), para a lista de acompanhamento ter escolha.
  - **Backend:** regras de perfil, frequência e usuário do Telegram em `nox/domain/contas.py`; serviço em `nox/application/perfil.py`.
  - **Rotas da API:** `GET/PUT /api/conta/preferencias`, `GET/PUT /api/conta/lista`, `GET /api/conta/meus-dados` e `GET /api/ativos`.
  - **Frontend:**
    - na tela Conta: perfil de investidor (três frases, uma por perfil), alertas (notificação e Telegram, a cada sinal ou resumo diário) e "Baixar meus dados";
    - na tela Sinais: uma estrela em cada ativo para acompanhar, e os ativos acompanhados aparecem primeiro, em "Seus ativos".

- **Como cada exigência foi atendida:**

  | Exigência | Como foi feito |
  | --- | --- |
  | Perfil de risco: conservador, moderado ou arrojado (RF-011) | Escolha por frases do dia a dia ("Prefiro perder pouco, mesmo ganhando menos..."), mais fáceis para o iniciante que os nomes técnicos. |
  | Canais de alerta push e Telegram (RF-011) | Um interruptor por canal; o Telegram pede o usuário (@nome), que é validado e normalizado. |
  | Frequência dos alertas (RF-012) | A cada sinal novo ou um resumo por dia. |
  | Dados pessoais protegidos (RNE-005) | O perfil de risco e o usuário do Telegram ficam cifrados no banco, com a mesma cifra do segredo do 2FA. |
  | Coleta restrita ao necessário (RNE-005) | Só o que os alertas exigem. Nada de saldo, carteira ou dados bancários. |
  | Lista vinculada ao usuário, escolhida entre os ativos do sistema (RF-015) | A lista só aceita ativos que o Nox acompanha. Quem continua na lista mantém a data em que foi adicionado. Limite de 20 ativos. |
  | Destaque no feed (RF-015) | Na tela Sinais, os ativos acompanhados aparecem primeiro. |
  | Direito de consultar os dados (LGPD, seção 18.2) | "Baixar meus dados" gera um arquivo JSON com conta, perfil, alertas e lista, já decifrados. O hash da senha e o segredo do 2FA ficam de fora, porque não servem ao titular e enfraqueceriam a conta se o arquivo vazasse. |
  | Direito de excluir (LGPD) | A exclusão da conta (RF-010) apaga também perfil, preferências e lista. |

- **Como foi testado:**
  1. **94 testes automatizados com Pytest** (19 novos), todos executados com o PostgreSQL ligado. Os novos cobrem:
     - valores padrão;
     - perfil e Telegram cifrados no banco;
     - perfil, frequência e canal inválidos;
     - Telegram ligado sem usuário;
     - formatos de usuário do Telegram;
     - lista com repetidos e ativos que o Nox não acompanha;
     - preservação da data de inclusão;
     - conteúdo do "Baixar meus dados";
     - limpeza na exclusão da conta;
     - rotas da API;
     - as tabelas no PostgreSQL.
  2. **Teste de ponta a ponta no navegador** (`frontend/e2e/conta.mjs`), agora com 26 verificações. Ele escolhe o perfil, liga o Telegram (primeiro com um usuário inválido), muda a frequência, salva e confere que tudo continua salvo depois de recarregar a página. Também marca um ativo na tela Sinais, recarrega e baixa os dados pelo mesmo endereço do botão.

- **Resultado ou evidência:**
  - Os 94 testes passam.
  - As 26 verificações de ponta a ponta passam, sem erros de JavaScript.
  - As capturas de tela estão em `experimentos/conta_rf010/evidencias/` (`06_preferencias.png` e `07_sinais_com_lista.png`).

- **Aprendizados:**
  - Descrever cada perfil com uma frase de comportamento ("uma queda forte me tiraria o sono") evita que o iniciante escolha "arrojado" só porque o nome soa melhor.
  - Guardar a data em que cada ativo entrou na lista, em vez de apagar e regravar tudo, preserva uma informação útil para os alertas e para análises futuras.
  - O teste de ponta a ponta precisou tolerar um detalhe do servidor de desenvolvimento: ao carregar módulos novos pela primeira vez, o Vite recarrega a página e interrompe a navegação. Isso não acontece na versão publicada.

- **Limitações identificadas:**
  - O perfil ainda não muda as recomendações; o documento deixa essa definição para os próximos períodos.
  - Os alertas não são enviados: as preferências ficam prontas para o RF-012. O push vai precisar da inscrição do navegador (Web Push), e o Telegram de um bot do Nox. Só com o usuário (@nome) não é possível mandar mensagem; quando o bot existir, a pessoa vai precisar iniciar a conversa com ele.
  - A lista tem só os seis ativos acompanhados pelo sistema.

- **Próximos passos:**
  - RF-012: bot do Telegram e notificações push, usando a lista e as preferências;
  - definir com a equipe como o perfil de risco vai ajustar o limiar de ação (por exemplo, um limiar maior para o perfil conservador).
