# RNF-009 – Aplicativo instalável (PWA)

Situação: **Implementado e verificado no Chrome** (21/10/2026). Falta testar no Safari, no Firefox e no iPhone.

- **Objetivo:** o público principal usa o celular. O Nox pode ser instalado na tela inicial, abre em tela cheia e não depende de uma loja de aplicativos. Um aplicativo nativo (React Native) fica para períodos posteriores.

- **O que foi feito:**
  - `frontend/public/manifest.webmanifest`: nome, cores, tela cheia, ícones e atalhos para Sinais e Aprender;
  - ícones da lua em 192 e 512 pixels, ícone adaptável do Android e ícone do iPhone (`frontend/scripts/gerar_icones.mjs`);
  - o service worker (`sw.js`) guarda só o esqueleto do site (página inicial, scripts e estilos), nunca dados de mercado, para que um preço antigo não apareça como atual (RNF-006). Sem internet, o aplicativo abre e a tela mostra o aviso de erro;
  - o mesmo service worker recebe os alertas push (RF-012).

- **Como foi testado:** no Chrome, o navegador não apontou nenhum erro de instalação (o único aviso foi o de estar em modo anônimo, do teste automático); o service worker passou a controlar a página; o cache foi criado; e a página Aprender abriu com a internet desligada.

- **Limitações:** não testado no iPhone, onde as notificações push só funcionam com o aplicativo instalado na tela inicial; a instalação em si é feita pelo navegador ("Adicionar à tela inicial").
