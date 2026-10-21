// Lê o PDF gerado e anota em que página começa cada título, para o sumário.
import { execFileSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import { META, conteudo } from './conteudo.mjs'

const normalizar = (t) => t.replace(/\s+/g, ' ').trim()
const pdf = `${META.arquivo}.pdf`
const total = Number(/Pages:\s+(\d+)/.exec(execFileSync('pdfinfo', [pdf], { encoding: 'utf8' }))[1])
const textos = []
for (let n = 1; n <= total; n++) {
  textos[n] = execFileSync('pdftotext', ['-f', String(n), '-l', String(n), pdf, '-'], { encoding: 'utf8' })
    .split('\n').map(normalizar).filter(Boolean)
}
// Pula a capa e o sumário: começa na primeira página depois da que tem "Sumário".
let pagina = textos.findIndex((linhas) => linhas?.includes('Sumário')) + 1
while (textos[pagina]?.some((l) => l.includes('....'))) pagina++
const paginas = {}
for (const [tipo, texto] of conteudo) {
  if (!['parte', 'secao', 'sub'].includes(tipo)) continue
  const inicio = normalizar(texto).slice(0, 28)
  let achou = pagina
  while (achou <= total && !textos[achou].some((l) => l.startsWith(inicio))) achou++
  if (achou > total) throw new Error(`título não encontrado no PDF: ${texto}`)
  paginas[texto] = achou
  pagina = achou
}
writeFileSync('paginas.json', JSON.stringify(paginas, null, 2) + '\n')
console.log(`sumário com ${Object.keys(paginas).length} títulos`)
