# Nox

Assistente consultivo com Inteligência Artificial para o mercado de criptoativos.
Projeto Integrador de Engenharia de Software (UniEVANGÉLICA), 4º Período.

O Nox acompanha o mercado e combina indicadores técnicos (RSI e MACD), sentimento de notícias e, mais adiante, Machine Learning para recomendar comprar, vender ou manter cada ativo, com um score de confiança de 0 a 100 e uma explicação em linguagem simples (Modo Explicativo). O Nox não opera em nome do usuário: toda recomendação é informativa.

## Estrutura

```
backend/        núcleo em Python (camadas api, application, domain e infrastructure)
experimentos/   scripts e evidências das experimentações da seção 19.2
docs/           registro das experimentações no formato do documento de especificação
```

## Como rodar

Requer Python 3.12 ou mais recente.

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest

# Experimentação 1: coleta da Binance (180 s de WebSocket)
.venv/bin/python ../experimentos/exp1_ingestao_binance/executar.py 180

# Experimentação 4: comparação dos indicadores e cenários do score
.venv/bin/python ../experimentos/exp4_indicadores/comparar.py
.venv/bin/python ../experimentos/exp4_indicadores/cenarios.py
```

## Situação das experimentações

| Nº | Tema | Situação |
| --- | --- | --- |
| 1 | Ingestão de dados da Binance em Python | Realizado |
| 2 | Séries temporais: InfluxDB x PostgreSQL | Proposto |
| 3 | Interface React e Modo Explicativo | Proposto |
| 4 | Indicadores RSI e MACD e estrutura do score | Realizado (parâmetros provisórios) |
