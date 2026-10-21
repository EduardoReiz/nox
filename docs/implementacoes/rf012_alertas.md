# RF-012 – Alertas de novos sinais

Situação: **Implementado e testado** (20/10/2026), com uma parte pendente de configuração. As notificações push estão completas. O Telegram está pronto no código e espera a criação do bot (ver "Como ativar o Telegram").

Também atende o RF-008 (o Sinal de Recomendação passa a ser gravado), o RF-013 (aviso de risco nos alertas) e o RNF-005 (rastreabilidade).

- **Objetivo:** avisar o usuário, pelos canais escolhidos, quando surgir um sinal novo para um ativo que ele acompanha. A mensagem traz ativo, ação, score, acesso à explicação e o aviso de risco.

- **O que foi feito:**
  - **Worker** (`python -m nox.worker`): um processo em segundo plano que calcula os sinais a cada minuto. É o "sistema" que dispara a geração de sinais no diagrama de casos de uso.
  - **Sinal de Recomendação no PostgreSQL** (tabela `sinal`): cada vela de 1 hora fechada gera no máximo um sinal por ativo, com componentes do score, divergência e texto explicativo. Assim a explicação mostrada é sempre a do cálculo que gerou a recomendação (RNF-005).
  - **Regra de alerta** (`nox/domain/alertas.py`): o alerta sai quando **a leitura muda**, por exemplo de neutro para sinal de alta ou de sinal de alta para neutro. Repetir a cada hora o mesmo "manter" faria o usuário ignorar os alertas. É uma decisão provisória, a validar com usuários.
  - **Entrega** (`nox/application/alertas.py`): para quem tem o ativo na lista (RF-015) e algum canal ligado (RF-011). Pode ser na hora ou num resumo diário às 9h, conforme a preferência. Cada envio fica registrado na tabela `alerta`, com sucesso ou falha.
  - **Notificações push** (padrão Web Push do W3C): o service worker (`frontend/public/sw.js`) mostra a notificação mesmo com o site fechado, e o toque abre a explicação do sinal. Funciona no Chrome, Edge e Firefox, e no Safari do iPhone com o Nox adicionado à tela de início. Não depende de conta em serviço externo, só de um par de chaves VAPID do próprio Nox, no `.env`.
  - **Telegram:** a pessoa toca em "Conectar Telegram". O Nox abre o bot com um código de uso único (válido por 15 minutos), e ao tocar em "Começar" o bot liga a conta ao chat. O identificador do chat fica cifrado (RNE-005).
  - **Alerta de teste:** botão na tela Conta para a pessoa conferir que os alertas chegam.
  - **Conteúdo** (RF-013):
    - na notificação: "Bitcoin: o Nox vê sinal de alta", "Confiança 72 de 100. Toque para ver por quê. Informativo, não é recomendação nem consultoria. O Nox não opera por você.";
    - no Telegram: a explicação completa, o link e o aviso de risco inteiro.

- **Como foi testado:**
  1. **112 testes automatizados com Pytest**, todos executados com o PostgreSQL ligado. Os novos cobrem:
     - a regra de quando um sinal vira alerta (6 casos);
     - alerta só para quem acompanha o ativo;
     - a mesma vela não gera sinal nem alerta duas vezes;
     - sinal gravado com a explicação;
     - resumo diário acumulado e enviado uma vez;
     - inscrição de push cancelada pelo navegador, que desconecta o canal;
     - quem não tem canal ligado não recebe;
     - o "/start" no bot liga a conta ao chat;
     - código de vínculo de uso único e com prazo;
     - alerta de teste e rotas da API.
  2. **Criptografia do push de ponta a ponta:** um receptor local faz o papel do navegador e decifra a mensagem com as chaves dele (RFC 8291). Isso prova que o conteúdo chega íntegro, e que só aquele navegador consegue ler.
  3. **Teste no navegador** (`frontend/e2e/conta.mjs`, 29 verificações). Ele confere:
     - sem bot configurado, a tela avisa em vez de quebrar;
     - um erro do navegador ao ativar as notificações vira uma mensagem clara em português;
     - a inscrição é aceita, e o canal aparece conectado e ligado;
     - o alerta de teste mostra a falha de entrega sem quebrar a tela.
  4. **Rodada do worker com dados reais:** os seis sinais reais foram gravados. Como todos estavam em "manter", corretamente nenhum alerta foi gerado, nem na segunda rodada.

- **Resultado ou evidência:**
  - Todos os testes passam.
  - A captura `experimentos/conta_rf010/evidencias/06_preferencias.png` mostra a tela de alertas.

- **Aprendizados:**
  - O Telegram não permite que um bot escreva para alguém só pelo @usuario: a pessoa precisa iniciar a conversa. Por isso o campo de @ do RF-011 foi trocado por "Conectar Telegram" com um código de uso único, que também prova que o chat pertence a quem está conectado no Nox.
  - O Chrome em modo headless, usado nos testes automáticos, não tem serviço de push. A falha mostrou que o erro do navegador chegava ao usuário em inglês e técnico; agora vira uma orientação em português.
  - Gravar o sinal com a vela que o gerou (ativo + instante, sem repetição) resolveu de uma vez a rastreabilidade (RNF-005) e a duplicidade de alertas.

- **Limitações identificadas:**
  - **Telegram aguardando o bot:** a criação do bot exige a conta do Telegram de alguém da equipe.
  - **Inscrição push num navegador comum:** não foi feita automaticamente, por causa do headless. O envio e a cifra foram provados pelo teste do receptor local; falta o teste manual de um minuto descrito abaixo.
  - **Um aparelho por pessoa:** a inscrição de push vale para um aparelho por pessoa. Ao conectar outro, o anterior deixa de receber.
  - **Execução contínua:** o worker precisa ficar rodando num servidor para os alertas saírem a qualquer hora.

- **Como ativar o Telegram** (cerca de 2 minutos, com o celular):
  1. No Telegram, abrir o **@BotFather** e enviar `/newbot`.
  2. Dar um nome (por exemplo, `Nox Alertas`) e um usuário terminado em `bot` (por exemplo, `NoxAlertasBot`).
  3. Copiar o token que o BotFather responde e colar no `.env`:
     ```
     NOX_TELEGRAM_TOKEN=<token>
     NOX_TELEGRAM_BOT=NoxAlertasBot
     ```
  4. Reiniciar a API e o worker. A tela Conta passa a mostrar "Conectar Telegram".

- **Teste manual das notificações** (cerca de 1 minuto): com a API, o worker e o frontend no ar, abrir o Nox no Chrome normal, entrar, ir em Conta, tocar em "Conectar notificações", permitir e tocar em "Enviar um alerta de teste". A notificação deve aparecer no canto da tela.

- **Próximos passos:**
  - criar o bot do Telegram e fazer os dois testes manuais acima;
  - colocar API e worker num servidor (o servidor de casa ou um serviço gratuito);
  - medir com usuários se "avisar na mudança de sugestão" é a frequência certa.
