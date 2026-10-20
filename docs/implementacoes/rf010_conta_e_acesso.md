# RF-010 – Conta, login, verificação em duas etapas e recuperação de senha

Situação: **Implementado e testado** (20/10/2026). Antes era "Em desenvolvimento".

Também atende a RNE-005 e ao RNF-003, e a parte de direitos do titular do RNF-007.

- **Objetivo:** permitir criar conta, entrar com e-mail e senha, ativar a verificação em duas etapas e recuperar a senha, protegendo os dados pessoais (RNE-005, RNF-003). Além disso, corrigir as falhas apontadas na revisão do protótipo de referência (Experimentação 5).

- **O que foi feito:**
  - **Backend** em Python, nas camadas da seção 19.1:
    - regras de conta na camada domain (`nox/domain/contas.py`);
    - fluxo de autenticação na application (`nox/application/autenticacao.py`);
    - hash, cifra, tokens e TOTP na infrastructure (`seguranca.py`);
    - armazenamento no PostgreSQL (`contas_repo.py`);
    - rotas da API em `nox/api/contas.py`.
  - **Frontend:** telas Entrar, Criar conta, Código de verificação, Esqueci a senha, Senha nova e Conta. A tela Conta reúne a ativação do 2FA, a saída e a exclusão da conta.
  - **Tabelas novas no PostgreSQL:** `usuario`, `sessao`, `desafio` e `auditoria`.

- **Como cada exigência foi atendida:**

  | Exigência | Como foi feito |
  | --- | --- |
  | Senhas só como hash (RNF-003) | Argon2id, o algoritmo recomendado hoje, com 64 MB de memória por hash. O hash é refeito automaticamente se os parâmetros mudarem. |
  | Verificação em duas etapas (RNF-003) | Código TOTP (RFC 6238), compatível com Google Authenticator, Microsoft Authenticator e Authy. A ativação mostra um QR code e só é concluída depois que o usuário digita um código válido. |
  | Falha do protótipo: 2FA liberava acesso só com e-mail e código | O login tem dois passos. A senha certa gera um desafio de uso único, válido por 5 minutos, e só esse desafio somado ao código abre a sessão. |
  | Falha do protótipo: código incompatível com aplicativos | O padrão TOTP é o mesmo dos aplicativos autenticadores. Aceita 30 s de diferença no relógio do celular, e um código já usado não vale de novo. |
  | Dados sensíveis cifrados (RNE-005) | O segredo do 2FA é cifrado no banco (Fernet: AES-128 com HMAC), com a chave fora do código, no arquivo `.env`. O perfil de risco (RF-011) vai usar a mesma cifra. |
  | Coleta mínima (seção 18.2) | Só nome, e-mail e senha. Sem CPF. |
  | Sessão segura | Token aleatório de 256 bits num cookie httpOnly e SameSite=Strict: o JavaScript da página não lê o cookie e outros sites não conseguem usá-lo. O banco guarda só o resumo SHA-256 dos tokens. |
  | Força bruta | 5 senhas erradas em 15 minutos bloqueiam a conta por 15 minutos. 5 códigos errados invalidam o desafio. |
  | Não revelar quem tem conta | Mesma mensagem e tempo de resposta parecido para e-mail inexistente e senha errada. O pedido de recuperação responde igual exista a conta ou não. |
  | Recuperação de senha | Link de uso único, válido por 30 minutos. Ao trocar a senha, todas as sessões abertas são encerradas. |
  | Auditoria (seção 18.2) | Registro de conta criada, sessão aberta, login com falha, 2FA ativado ou desativado, recuperação e exclusão, sem dados pessoais no registro. |
  | Direitos do titular (LGPD) | O usuário vê os próprios dados na tela Conta e pode excluir a conta com a senha. Os dados são apagados, e a auditoria fica anônima. |

- **Como foi testado:**
  1. **75 testes automatizados com Pytest**, entre eles:
     - regras de senha;
     - cadastro com e-mail repetido;
     - mesma mensagem de erro para e-mail inexistente e senha errada;
     - bloqueio após 5 erros e liberação após 15 minutos;
     - expiração da sessão;
     - login em dois passos;
     - código sem ter passado pela senha;
     - código reutilizado;
     - desafio expirado e cinco códigos errados;
     - relógio do celular atrasado;
     - link de recuperação usado duas vezes e expirado;
     - exclusão da conta.

     O tempo é simulado nos testes, o que permite verificar expirações sem esperar.
  2. Testes do armazenamento contra o PostgreSQL real (`tests/test_contas_postgres.py`).
  3. **Teste de ponta a ponta no navegador** (`frontend/e2e/conta.mjs`): o Chrome, controlado pelo Playwright, preenche os formulários e clica como um usuário, com 19 verificações. Ele percorre dois roteiros:
     - criar conta, ativar o 2FA lendo a chave da tela, sair, entrar com senha e código;
     - criar outra conta, recuperar a senha pelo link, entrar com a senha nova e excluir a conta.

- **Resultado ou evidência:**
  - Os 75 testes automatizados e as 19 verificações de ponta a ponta passam.
  - O teste de ponta a ponta confirmou no navegador que só a senha não abre sessão quando o 2FA está ativo, que o cookie de sessão não é visível ao JavaScript e que não houve erros de JavaScript.
  - As capturas de tela estão em `experimentos/conta_rf010/evidencias/`.

- **Aprendizados:**
  - O teste de ponta a ponta achou um defeito que os testes de unidade não pegaram: o QR code não aparecia. A biblioteca gerava um SVG próprio para colocar direto no HTML, sem a declaração de namespace que o navegador exige quando o SVG é usado como imagem. Foi corrigido, e os dois tipos de teste passaram a conferir isso.
  - Separar o login em dois passos com um desafio de uso único resolve a falha do protótipo antigo sem complicar a tela: para o usuário são só dois formulários.
  - Simular o relógio nos testes foi essencial para testar expirações (5 minutos, 15 minutos, 30 minutos, 7 dias) sem esperar.

- **Limitações identificadas:**
  - Ainda não há envio real de e-mail: em desenvolvimento, o link de recuperação aparece no log do backend. É preciso escolher um serviço de envio.
  - O bloqueio por tentativas vale por conta, e não por endereço de IP. Um ataque que tente muitas contas diferentes precisa de limite por IP, que fica para quando houver servidor publicado.
  - Não há códigos de recuperação para quem perder o celular com o aplicativo autenticador.
  - O HTTPS (RNF-003) depende do servidor de produção. O cookie já está preparado para exigir HTTPS (`NOX_COOKIE_SEGURO=1`).
  - O login com Apple, Google ou Facebook, que aparecia no protótipo antigo, não foi feito.

- **Próximos passos:**
  - perfil de risco e preferências de alerta (RF-011), usando a cifra já pronta;
  - lista de ativos acompanhados (RF-015);
  - códigos de recuperação do 2FA;
  - escolha do serviço de e-mail.
