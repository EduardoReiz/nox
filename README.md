# Nox

Assistente consultivo com Inteligência Artificial para o mercado de criptoativos.
Projeto Integrador de Engenharia de Software (UniEVANGÉLICA), 4º Período.

O Nox acompanha o mercado e combina indicadores técnicos (RSI e MACD), sentimento de notícias e, mais adiante, Machine Learning para recomendar comprar, vender ou manter cada ativo, com um score de confiança de 0 a 100 e uma explicação em linguagem simples (Modo Explicativo). O Nox não opera em nome do usuário: toda recomendação é informativa.

## Estrutura

```
backend/        núcleo em Python (camadas api, application, domain e infrastructure)
frontend/       interface web em React (Vite, Tailwind e Recharts)
experimentos/   scripts e evidências das experimentações da seção 19.2
docs/           registro das experimentações no formato do documento de especificação
```

## Como rodar

Requer Python 3.12 ou mais recente e Docker.

```bash
cp .env.exemplo .env   # troque as senhas e gere a NOX_CHAVE_DADOS (instrução no arquivo)
docker compose up -d postgres
```

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest

# Experimentação 1: coleta da Binance (180 s de WebSocket)
.venv/bin/python ../experimentos/exp1_ingestao_binance/executar.py 180

# Experimentação 2: InfluxDB x PostgreSQL (precisa do docker compose)
.venv/bin/python ../experimentos/exp2_series_temporais/executar.py

# Experimentação 4: comparação dos indicadores e cenários do score
.venv/bin/python ../experimentos/exp4_indicadores/comparar.py
.venv/bin/python ../experimentos/exp4_indicadores/cenarios.py
```

### Interface

```bash
cd backend && .venv/bin/uvicorn nox.api.app:app --port 8000   # API com dados reais
cd frontend && npm install && npm run dev                      # http://localhost:5173

# ou, sem backend, com os sinais simulados:
cd frontend && VITE_FONTE=simulado npm run dev

# teste de ponta a ponta da conta (precisa do banco, da API e do frontend no ar,
# com o log da API num arquivo para ler o link de recuperação)
cd frontend && NOX_LOG_API=/caminho/do/api.log node e2e/conta.mjs
```

## Requisitos implementados

| Requisito | Registro |
| --- | --- |
| RF-010 Conta, login, 2FA e recuperação de senha | `docs/implementacoes/rf010_conta_e_acesso.md` |
| RF-011 Perfil de risco e preferências de alerta | `docs/implementacoes/rf011_rf015_perfil_e_lista.md` |
| RF-015 Lista de ativos acompanhados | `docs/implementacoes/rf011_rf015_perfil_e_lista.md` |

## Situação das experimentações

| Nº | Tema | Situação |
| --- | --- | --- |
| 1 | Ingestão de dados da Binance em Python | Realizado |
| 2 | Séries temporais: InfluxDB x PostgreSQL | Realizado (decisão a confirmar) |
| 3 | Interface React e Modo Explicativo | Parcialmente realizado (falta a avaliação com participantes) |
| 4 | Indicadores RSI e MACD e estrutura do score | Realizado (parâmetros provisórios) |
