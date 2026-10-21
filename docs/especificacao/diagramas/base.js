// Desenha os diagramas do documento em SVG, no mesmo estilo das figuras
// das versões anteriores: caixas cinza-azuladas, destaque em azul e setas cinza.
const NS = 'http://www.w3.org/2000/svg'
const COR = { linha: '#5b6472', texto: '#1f2328', fraco: '#5b6472', fundo: '#f4f6fa', azul: '#2b5797', azulFundo: '#e6edf8', grupo: '#eef1f5' }

function svg(largura, altura) {
  const s = document.createElementNS(NS, 'svg')
  s.setAttribute('width', largura)
  s.setAttribute('height', altura)
  s.setAttribute('viewBox', `0 0 ${largura} ${altura}`)
  s.innerHTML = `<defs><marker id="seta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${COR.linha}"/></marker></defs>`
  document.body.appendChild(s)
  return s
}

function el(pai, tag, attrs, texto) {
  const e = document.createElementNS(NS, tag)
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v)
  if (texto !== undefined) e.textContent = texto
  pai.appendChild(e)
  return e
}

function texto(s, x, y, conteudo, { tamanho = 14, peso = 400, cor = COR.fraco, ancora = 'start' } = {}) {
  return el(s, 'text', { x, y, 'font-size': tamanho, 'font-weight': peso, fill: cor, 'text-anchor': ancora }, conteudo)
}

function titulo(s, conteudo) {
  texto(s, 24, 40, conteudo, { tamanho: 22, peso: 700, cor: COR.texto })
}

// Caixa com título e até duas linhas de apoio. tipo: normal, destaque, tracejada, grupo
function caixa(s, x, y, w, h, nome, linhas = [], tipo = 'normal') {
  const estilo = {
    normal: { fill: COR.fundo, stroke: COR.linha, 'stroke-width': 1.5 },
    destaque: { fill: COR.azulFundo, stroke: COR.azul, 'stroke-width': 2.5 },
    tracejada: { fill: '#ffffff', stroke: COR.linha, 'stroke-width': 1.5, 'stroke-dasharray': '6 5' },
    banco: { fill: '#ffffff', stroke: COR.azul, 'stroke-width': 2 },
  }[tipo]
  el(s, 'rect', { x, y, width: w, height: h, rx: 10, ...estilo })
  const total = 1 + linhas.length
  const topo = y + h / 2 - (total - 1) * 11 + 6
  texto(s, x + w / 2, topo, nome, { tamanho: 17, peso: 700, cor: COR.texto, ancora: 'middle' })
  linhas.forEach((l, i) => texto(s, x + w / 2, topo + 24 + i * 20, l, { tamanho: 14, ancora: 'middle' }))
}

// Bloco com título à esquerda e lista de itens (arquitetura)
function bloco(s, x, y, w, h, nome, itens, rodape) {
  el(s, 'rect', { x, y, width: w, height: h, rx: 10, fill: COR.fundo, stroke: COR.linha, 'stroke-width': 1.5 })
  texto(s, x + 18, y + 34, nome, { tamanho: 19, peso: 700, cor: COR.azul })
  let yy = y + 66
  for (const item of itens) {
    const partes = Array.isArray(item) ? item : [item]
    partes.forEach((p, i) => {
      texto(s, x + 18 + (i ? 14 : 0), yy, (i ? '' : '• ') + p, { tamanho: 15, cor: COR.texto })
      yy += 21
    })
    yy += 6
  }
  if (rodape) texto(s, x + 18, y + h - 18, rodape, { tamanho: 14 })
}

function grupo(s, x, y, w, h, nome) {
  el(s, 'rect', { x, y, width: w, height: h, rx: 14, fill: COR.grupo, stroke: '#c9ced6', 'stroke-width': 1.5 })
  texto(s, x + 24, y + 32, nome, { tamanho: 16, peso: 700 })
}

function seta(s, pontos, { tracejada = false, ponta = true, rotulo, rx, ry, ancora = 'middle' } = {}) {
  el(s, 'polyline', {
    points: pontos.map((p) => p.join(',')).join(' '), fill: 'none', stroke: COR.linha, 'stroke-width': 1.6,
    ...(tracejada ? { 'stroke-dasharray': '6 5' } : {}), ...(ponta ? { 'marker-end': 'url(#seta)' } : {}),
  })
  if (rotulo) texto(s, rx, ry, rotulo, { tamanho: 14, ancora })
}
