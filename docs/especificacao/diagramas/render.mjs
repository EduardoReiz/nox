// Gera os PNG das figuras a partir dos HTML desta pasta (Chrome do sistema).
import { chromium } from '../../../frontend/node_modules/playwright-core/index.mjs'
import { readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const aqui = path.dirname(fileURLToPath(import.meta.url))
const alvos = process.argv.slice(2).length ? process.argv.slice(2) : readdirSync(aqui).filter((f) => f.endsWith('.html'))
const navegador = await chromium.launch({ channel: 'chrome', headless: true })
try {
  const pagina = await navegador.newPage({ deviceScaleFactor: 2 })
  for (const arquivo of alvos) {
    await pagina.goto('file://' + path.join(aqui, arquivo))
    const saida = path.join(aqui, '..', 'figuras', arquivo.replace('.html', '.png'))
    await pagina.locator('svg').screenshot({ path: saida })
    console.log('gerado', path.basename(saida))
  }
} finally {
  await navegador.close()
}
