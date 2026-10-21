# Experimentação 5 – protótipo de referência (setembro de 2025)

- `prototipo/`: cópia, sem alterações, do protótipo full-stack feito no 2º Período (pasta `nox-fullstack-linked`
  do Drive da equipe): backend em TypeScript (Fastify, Prisma, PostgreSQL) e frontend em React.
- `testes/`: os scripts desta experimentação. Nada em `prototipo/` foi modificado; as correções necessárias
  para o servidor subir foram feitas numa cópia descartável (ver `docs/experimentacoes/exp5_prototipo_antigo.md`).
- `evidencias/`: saídas reais das execuções.

Como repetir (precisa do PostgreSQL do `docker-compose.yml` da raiz no ar):

```bash
# 1. validação do schema (esperado: 30 erros)
cd experimentos/exp5_prototipo_antigo/prototipo/backend && npm install
DATABASE_URL=postgresql://x npx prisma validate

# 2. com o schema corrigido, servidor com @fastify/cors@9 e @fastify/helmet@11, e os testes de segurança
npx prisma db push --schema ../../testes/schema_corrigido.prisma
JWT_SECRET=teste npx tsx src/index.ts &
node ../../testes/rodar.mjs

# 3. indicadores
npx tsx ../../testes/indicadores.ts ../../../exp1_ingestao_binance/evidencias/velas_BTCUSDT_1h.csv
../../../../backend/.venv/bin/python ../../testes/comparar_indicadores.py
```
