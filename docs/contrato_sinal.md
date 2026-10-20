# Formato de dados do Sinal de Recomendação

Contrato entre o backend (API) e o frontend, definido no passo 1 da Experimentação 3. Os sinais simulados (`frontend/src/dados/sinais_simulados.json`) e a API real (`GET /api/sinais`) seguem exatamente este formato.

## Endpoints

| Rota | Retorno |
| --- | --- |
| `GET /api/sinais` | lista com o sinal mais recente de cada ativo acompanhado (feed, RF-009) |
| `GET /api/sinais/{ativo}` | um sinal, para o Modo Explicativo (RF-005) |
| `GET /api/ativos/{ativo}/velas?quantidade=168` | `[{instante, fechamento}]` para o gráfico |

## Sinal disponível

```json
{
  "ativo": "SOLUSDT",
  "nome": "Solana",
  "disponivel": true,
  "preco": {
    "ultimo": 142.37,
    "variacao_24h_pct": 4.8,
    "atualizado_em": "2026-10-20T15:00:00+00:00"
  },
  "gerado_em": "2026-10-20T14:55:00+00:00",
  "acao": "manter",
  "score": 35,
  "direcao": "alta",
  "componentes": [
    {
      "nome": "tecnico",
      "rotulo": "Análise técnica",
      "forca": 0.8,
      "peso": 0.625,
      "pontuacao": 80,
      "detalhes": { "rsi": 31.0, "forca_rsi": 0.9, "forca_macd": 0.7, "cruzamento": null }
    },
    { "nome": "sentimento", "rotulo": "Sentimento do mercado", "forca": -0.7, "peso": 0.375, "pontuacao": 0, "detalhes": {} }
  ],
  "ausentes": ["Previsão de Machine Learning"],
  "divergencia": { "tecnico": "alta", "sentimento": "negativo", "score_antes": 50, "reducao": 0.3 },
  "explicacao": "O Nox sugere MANTER SOLUSDT, com confiança 35 de 100. ...",
  "aviso_risco": "Esta recomendação é apenas informativa e não constitui consultoria de investimentos. ..."
}
```

| Campo | Significado | Regra |
| --- | --- | --- |
| `acao` | `comprar`, `vender` ou `manter` | RF-008, RNE-008 |
| `score` | confiança de 0 a 100 | RNE-001 |
| `direcao` | `alta`, `baixa` ou `neutra` | lado da média ponderada das forças |
| `componentes[].forca` | de −1 (queda) a +1 (alta) | |
| `componentes[].peso` | peso já redistribuído entre os componentes presentes | soma 1 |
| `componentes[].pontuacao` | S, de 0 a 100: quanto o componente apoia a direção | |
| `ausentes` | componentes que não entraram no cálculo | RF-006 |
| `divergencia` | `null` ou os dados da redução aplicada | RNE-003 |
| `explicacao` | texto do Modo Explicativo, gerado junto com o sinal | RNE-002, RNF-005 |
| `aviso_risco` | aviso exibido junto ao sinal | RF-013, RNE-007 |
| `preco.atualizado_em` | fim da última vela fechada | RNF-006 |

Todos os instantes estão em UTC (ISO 8601); a tela converte para o horário de Brasília.

## Sem sinal (RNE-004)

```json
{ "ativo": "BTCUSDT", "nome": "Bitcoin", "disponivel": false, "motivo": "histórico insuficiente: 150 velas, o mínimo é 200" }
```
