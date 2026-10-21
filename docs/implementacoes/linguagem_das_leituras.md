# Linguagem das leituras: de "comprar e vender" para "sinal de alta, sinal de queda e neutro"

Situação: **Implementado** nas telas, na explicação e nos alertas (21/10/2026). O documento oficial mantém os termos da especificação até a conversa com os orientadores.

- **Objetivo:** evitar que o Nox seja confundido com uma corretora ou com uma consultoria de investimentos. A análise e a recomendação de investimentos são atividades reguladas pela CVM (seção 9 do documento), e um aviso no rodapé não basta se a tela diz "venda" ou "compre".

- **O que mudou:**
  - Na interface, a ação `comprar` aparece como **sinal de alta**, `vender` como **sinal de queda** e `manter` como **neutro**.
  - A explicação passou de "O Nox sugere comprar BTC" para "Leitura do Nox para BTC: sinal de alta, com confiança 74 de 100".
  - Os alertas dizem "Bitcoin: o Nox vê sinal de alta" e "Bitcoin: voltou ao neutro".
  - O aviso de risco diz que a leitura é informativa, que não é recomendação nem consultoria e que o Nox não diz o que a pessoa deve fazer.
  - O perfil de risco **não altera** o sinal: o Nox mostra a mesma leitura a todas as pessoas. Adequar o sinal ao perfil se aproximaria de consultoria.
  - A aba Aprender ganhou o tema "O que é o Nox, e o que não é": não é corretora, não guarda dinheiro, não compra nem vende, não é consultoria.

- **O que não mudou:** o cálculo do score, o limiar de 60 e o contrato do sinal. O campo `acao` mantém os códigos `comprar`, `vender` e `manter` (RF-008, RNE-008), e a mudança fica na camada que mostra o texto (`LEITURAS`, em `backend/nox/domain/score.py`, e `ACOES`, em `frontend/src/dados/formato.js`).

- **Como foi testado:** 116 testes do backend (os de texto foram atualizados), 29 verificações de ponta a ponta no navegador e conferência visual das telas (`experimentos/exp3_interface/evidencias`).

- **Limitações:**
  - O documento ainda usa "recomendação de comprar, vender ou manter" no RF-008 e na descrição do produto. Foi acrescentada uma nota no RF-008 explicando a diferença; a mudança dos termos no documento depende dos orientadores.
  - Mudar as palavras reduz o risco de interpretação, mas não o elimina: o aviso legal e o comportamento do produto continuam sendo o que conta. Um parecer de quem entenda de regulação do mercado seria o ideal.
  - Falta medir quanto os sinais acertam (backtesting) para mostrar ao usuário um histórico honesto.

- **Próximos passos:** levar a mudança aos orientadores; fazer o backtesting; mostrar o histórico de acertos e erros na tela.
