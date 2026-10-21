// Executa o RSI e o MACD do protótipo antigo sobre as velas da Experimentação 1.
//   cd prototipo/backend && npx tsx ../../testes/indicadores.ts ../../../exp1_ingestao_binance/evidencias/velas_BTCUSDT_1h.csv
import { readFileSync, writeFileSync } from 'node:fs'
import { computeRSI, computeMACD } from '../prototipo/backend/src/signals/indicators.ts'

const linhas = readFileSync(process.argv[2], 'utf8').trim().split('\n')
const coluna = linhas[0].split(',').indexOf('fechamento')
const fechamentos = linhas.slice(1).map((l) => Number(l.split(',')[coluna]))
const macd = computeMACD(fechamentos)
writeFileSync(new URL('../evidencias/indicadores_antigo.json', import.meta.url), JSON.stringify({
  rsi: computeRSI(fechamentos), macd: macd.macd, hist: macd.hist, cruzamento: macd.cross,
}))
