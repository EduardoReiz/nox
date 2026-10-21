// Gera os ícones do aplicativo (PWA) a partir de scripts/icone.html, com o Chrome do sistema.
//   node scripts/gerar_icones.mjs
import { chromium } from 'playwright-core'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const aqui = path.dirname(fileURLToPath(import.meta.url))
const publico = path.join(aqui, '..', 'public')
const saidas = [
  ['icone-192.png', 192, false], ['icone-512.png', 512, false],
  ['icone-maskable-512.png', 512, true], ['apple-touch-icon.png', 180, false],
]
const navegador = await chromium.launch({ channel: 'chrome', headless: true })
try {
  for (const [arquivo, tamanho, maskable] of saidas) {
    const pagina = await navegador.newPage({ viewport: { width: 512, height: 512 }, deviceScaleFactor: tamanho / 512 })
    await pagina.goto(`file://${path.join(aqui, 'icone.html')}${maskable ? '?m=1' : ''}`)
    await pagina.locator('#i').screenshot({ path: path.join(publico, arquivo) })
    await pagina.close()
    console.log('gerado', arquivo)
  }
} finally {
  await navegador.close()
}
