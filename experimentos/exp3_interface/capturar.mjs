// Captura as telas do Nox para as evidências da Experimentação 3 e do documento.
//   API e frontend no ar (npm run dev, porta 5173) e, para os simulados,
//   VITE_FONTE=simulado npx vite --port 5174.   node experimentos/exp3_interface/capturar.mjs
import { chromium } from '../../frontend/node_modules/playwright-core/index.mjs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const aqui = path.dirname(fileURLToPath(import.meta.url))
const evidencias = path.join(aqui, 'evidencias')
const figuras = path.join(aqui, '..', '..', 'docs', 'especificacao', 'figuras')
const SIMULADO_DIVERGENTE = process.env.ATIVO_COM_DIVERGENCIA ?? 'SOLUSDT'

const navegador = await chromium.launch({ channel: 'chrome', headless: true, args: ['--force-prefers-reduced-motion'] })
async function abrir(contexto, url) {
  const pagina = await contexto.newPage()
  for (let i = 0; i < 3; i++) {
    try { await pagina.goto(url, { waitUntil: 'networkidle' }); break } catch { await pagina.waitForTimeout(1500) }
  }
  await pagina.waitForTimeout(2000)
  return pagina
}
try {
  const celular = await navegador.newContext({ viewport: { width: 500, height: 900 }, deviceScaleFactor: 2 })
  const telas = [
    ['real_hoje', 'http://localhost:5173/'], ['real_sinais', 'http://localhost:5173/sinais'],
    ['real_explicacao_btc', 'http://localhost:5173/sinais/BTCUSDT'], ['aprender', 'http://localhost:5173/aprendizado'],
    ['simulado_hoje', 'http://localhost:5174/'], ['simulado_sinais', 'http://localhost:5174/sinais'],
    ['simulado_explicacao_divergencia', `http://localhost:5174/sinais/${SIMULADO_DIVERGENTE}`],
  ]
  for (const [nome, url] of telas) {
    const pagina = await abrir(celular, url)
    await pagina.screenshot({ path: path.join(evidencias, `${nome}.png`), fullPage: true })
    if (nome === 'real_hoje') await pagina.screenshot({ path: path.join(figuras, 'fig2_hoje.png'), clip: { x: 0, y: 0, width: 500, height: 900 } })
    if (nome === 'real_explicacao_btc') await pagina.screenshot({ path: path.join(figuras, 'fig3_explicacao.png'), clip: { x: 0, y: 0, width: 500, height: 900 } })
    await pagina.close()
    console.log('capturado', nome)
  }
} finally {
  await navegador.close()
}
