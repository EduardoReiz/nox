// Gera o Documento de Especificação do Nox em Word (.docx), no formato do
// modelo da UniEVANGÉLICA usado nas versões anteriores. O texto fica em
// conteudo.mjs; este arquivo só cuida da formatação.
//
//   npm install && node gerar.mjs
//
// O sumário é montado com os números de página lidos do PDF anterior
// (paginas.json); exportar_pdf.sh gera o PDF duas vezes para acertá-los.
import {
  AlignmentType, BorderStyle, Document, Footer, Header, HeadingLevel, HorizontalPositionRelativeFrom,
  ImageRun, LevelFormat, Packer, PageBreak, Paragraph, ShadingType, Tab, Table, TableCell, TabStopType,
  TableRow, TextRun, VerticalAlign, VerticalPositionRelativeFrom, WidthType,
} from 'docx'
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { META, conteudo } from './conteudo.mjs'

const aqui = path.dirname(fileURLToPath(import.meta.url))
const figura = (nome) => readFileSync(path.join(aqui, 'figuras', nome))

const FONTE = 'Arial'
const AZUL = '0070C0'
const BORDA = { style: BorderStyle.SINGLE, size: 4, color: '7F7F7F' }
const BORDAS = { top: BORDA, bottom: BORDA, left: BORDA, right: BORDA }
const LARGURA_UTIL = 9071 // A4 com margens de 3 cm e 2,5 cm, em DXA
const EMU_POR_PX = 9525

// Texto com **negrito** e _itálico_ simples.
function runs(texto, base = {}) {
  return texto.split(/(\*\*[^*]+\*\*|_[^_]+_)/).filter(Boolean).map((parte) => {
    if (parte.startsWith('**')) return new TextRun({ text: parte.slice(2, -2), bold: true, font: FONTE, ...base })
    if (parte.startsWith('_') && parte.endsWith('_') && parte.length > 2) return new TextRun({ text: parte.slice(1, -1), italics: true, font: FONTE, ...base })
    return new TextRun({ text: parte, font: FONTE, ...base })
  })
}

const corpo = { size: 24 }
const espacoCorpo = { line: 360, after: 120 }

function p(texto, opcoes = {}) {
  return new Paragraph({ children: runs(texto, corpo), alignment: AlignmentType.JUSTIFIED, spacing: espacoCorpo, ...opcoes })
}

function celula(texto, largura, { cabecalho = false, negrito = false, alinhamento, span, fundo, manter = cabecalho } = {}) {
  const linhas = Array.isArray(texto) ? texto : [texto]
  return new TableCell({
    borders: BORDAS,
    width: { size: largura, type: WidthType.DXA },
    columnSpan: span,
    verticalAlign: VerticalAlign.CENTER,
    shading: cabecalho ? { fill: AZUL, type: ShadingType.CLEAR, color: 'auto' } : fundo ? { fill: fundo, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 80, bottom: 80, left: 110, right: 110 },
    children: linhas.map((l) => new Paragraph({
      keepNext: manter,
      alignment: cabecalho ? AlignmentType.CENTER : alinhamento ?? AlignmentType.LEFT,
      spacing: { line: 264, after: 0 },
      children: runs(l, { size: 20, bold: cabecalho || negrito, color: cabecalho ? 'FFFFFF' : undefined }),
    })),
  })
}

function tabela(cabecalho, linhas, pesos, { primeiraNegrito = true, centralizar = [] } = {}) {
  const total = pesos.reduce((a, b) => a + b, 0)
  const larguras = pesos.map((w) => Math.round((w / total) * LARGURA_UTIL))
  larguras[larguras.length - 1] += LARGURA_UTIL - larguras.reduce((a, b) => a + b, 0)
  return new Table({
    width: { size: LARGURA_UTIL, type: WidthType.DXA },
    columnWidths: larguras,
    rows: [
      new TableRow({ tableHeader: true, children: cabecalho.map((c, i) => celula(c, larguras[i], { cabecalho: true })) }),
      ...linhas.map((linha) => new TableRow({
        cantSplit: true,
        children: linha.map((c, i) => celula(c, larguras[i], {
          negrito: primeiraNegrito && i === 0,
          alinhamento: centralizar.includes(i) ? AlignmentType.CENTER : undefined,
        })),
      })),
    ],
  })
}

// Quadro de requisito ou regra: uma linha de dados e o detalhamento ocupando a largura toda.
function quadro(cabecalho, valores, pesos, detalhamento) {
  const total = pesos.reduce((a, b) => a + b, 0)
  const larguras = pesos.map((w) => Math.round((w / total) * LARGURA_UTIL))
  larguras[larguras.length - 1] += LARGURA_UTIL - larguras.reduce((a, b) => a + b, 0)
  return [
    new Table({
      width: { size: LARGURA_UTIL, type: WidthType.DXA },
      columnWidths: larguras,
      rows: [
        new TableRow({ cantSplit: true, children: cabecalho.map((c, i) => celula(c, larguras[i], { cabecalho: true })) }),
        new TableRow({
          cantSplit: true,
          children: valores.map((v, i) => celula(v, larguras[i], { negrito: i === 0, manter: true, alinhamento: i === 1 ? AlignmentType.LEFT : AlignmentType.CENTER })),
        }),
        new TableRow({
          cantSplit: true,
          children: [new TableCell({
            borders: BORDAS,
            columnSpan: larguras.length,
            width: { size: LARGURA_UTIL, type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 110, right: 110 },
            children: [new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { line: 276, after: 0 }, children: runs('**Detalhamento:** ' + detalhamento, { size: 20 }) })],
          })],
        }),
      ],
    }),
    new Paragraph({ spacing: { after: 240 }, children: [] }),
  ]
}

function imagem(nome, larguraPx, alturaPx) {
  return new ImageRun({ type: 'png', data: figura(nome), transformation: { width: larguraPx, height: alturaPx } })
}

function imagemFlutuante(nome, larguraPx, alturaPx, topoPx) {
  return new ImageRun({
    type: 'png',
    data: figura(nome),
    transformation: { width: larguraPx, height: alturaPx },
    floating: {
      horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, offset: 0 },
      verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, offset: Math.round(topoPx * EMU_POR_PX) },
      behindDocument: true,
      allowOverlap: true,
    },
  })
}

function imagemCentral(nome, larguraPx, alturaPx, topoPx) {
  const esquerda = Math.round(((794 - larguraPx) / 2) * EMU_POR_PX)
  return new ImageRun({
    type: 'png',
    data: figura(nome),
    transformation: { width: larguraPx, height: alturaPx },
    floating: {
      horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, offset: esquerda },
      verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, offset: Math.round(topoPx * EMU_POR_PX) },
      behindDocument: true,
      allowOverlap: true,
    },
  })
}

// Cabeçalho e rodapé do modelo: faixa com os logotipos no topo, marca-d'água
// clara no meio da página e a faixa com o endereço no rodapé.
function cabecalho(marcaTopo, marcaLargura) {
  const altura = Math.round((marcaLargura * 210) / 750)
  return new Header({
    children: [new Paragraph({
      children: [
        imagemFlutuante('cabecalho.png', 794, 138, 0),
        imagemCentral('marca_dagua.png', marcaLargura, altura, marcaTopo),
      ],
    })],
  })
}

const rodape = new Footer({
  children: [new Paragraph({ children: [imagemFlutuante('rodape.png', 794, 88, 1123 - 88)] })],
})

// Tradução dos blocos de conteudo.mjs em elementos do Word.
const blocos = {
  parte: (t, { quebra = true } = {}) => [new Paragraph({
    heading: HeadingLevel.HEADING_1, pageBreakBefore: quebra, spacing: { before: 0, after: 240 },
    children: [new TextRun({ text: t, font: FONTE, bold: true, size: 28 })],
  })],
  secao: (t, criacao, atualizacao) => [
    new Paragraph({
      heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 240, after: 80 },
      children: [new TextRun({ text: t, font: FONTE, bold: true, size: 26 })],
    }),
    ...[criacao, atualizacao].filter(Boolean).map((linha, i, todas) => new Paragraph({
      keepNext: true, spacing: { after: i === todas.length - 1 ? 200 : 0 },
      children: [new TextRun({ text: linha, font: FONTE, italics: true, underline: {}, size: 20 })],
    })),
  ],
  sub: (t) => [new Paragraph({
    heading: HeadingLevel.HEADING_3, keepNext: true, spacing: { before: 200, after: 120 },
    children: [new TextRun({ text: t, font: FONTE, bold: true, size: 24 })],
  })],
  p: (t) => [p(t)],
  rotulo: (t) => [new Paragraph({ keepNext: true, spacing: { before: 120, after: 60 }, children: runs(`**${t}**`, corpo) })],
  titulo_tabela: (t) => [new Paragraph({ keepNext: true, spacing: { before: 120, after: 80 }, children: runs(`**${t}**`, corpo) })],
  lista: (itens) => itens.map((item) => new Paragraph({
    numbering: { reference: 'marcadores', level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 360, after: 80 },
    children: runs(item, corpo),
  })),
  sublista: (itens) => itens.map((item) => new Paragraph({
    numbering: { reference: 'marcadores', level: 1 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 300, after: 60 },
    children: runs(item, corpo),
  })),
  numerada: (itens, ref = 'numeros') => itens.map((item) => new Paragraph({
    numbering: { reference: ref, level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 360, after: 80 },
    children: runs(item, corpo),
  })),
  tabela: (cab, linhas, pesos, opcoes) => [tabela(cab, linhas, pesos, opcoes), new Paragraph({ spacing: { after: 200 }, children: [] })],
  requisito: (r) => quadro(['ID', 'Descrição', 'Status', 'Prioridade'], [r.id, r.descricao, r.status, r.prioridade], [12, 46, 22, 20], r.detalhamento),
  regra: (r) => quadro(['ID', 'Descrição', 'Requisitos Relacionados'], [r.id, r.descricao, r.relacionados], [12, 56, 32], r.detalhamento),
  formula: (linhas) => linhas.map((l) => new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: l, font: 'Cambria Math', italics: true, size: 22 })],
  })),
  figura: (nome, largura, altura, legenda) => [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 }, children: [imagem(nome, largura, altura)] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: legenda, font: FONTE, size: 20 })] }),
  ],
  figuras_lado: (itens) => {
    const larg = LARGURA_UTIL / itens.length
    return [new Table({
      width: { size: LARGURA_UTIL, type: WidthType.DXA },
      columnWidths: itens.map(() => larg),
      borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE }, insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE } },
      rows: [new TableRow({
        cantSplit: true,
        children: itens.map(([nome, w, h, legenda]) => new TableCell({
          width: { size: larg, type: WidthType.DXA },
          borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
          children: [
            new Paragraph({ alignment: AlignmentType.CENTER, children: [imagem(nome, w, h)] }),
            new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80 }, children: [new TextRun({ text: legenda, font: FONTE, size: 20 })] }),
          ],
        })),
      })],
    }), new Paragraph({ spacing: { after: 200 }, children: [] })]
  },
  // Experimentação no formato Objetivo / O que foi testado / Como / Resultado / ...
  experimento: (e) => {
    const saida = [
      new Paragraph({ keepNext: true, spacing: { before: 280, after: 80 }, children: runs(`**${e.titulo}**`, corpo) }),
      p(`**Situação:** ${e.situacao}`),
    ]
    for (const [rotulo, partes] of e.itens) {
      const lista = Array.isArray(partes) ? partes : [partes]
      lista.forEach((parte, i) => {
        if (typeof parte === 'string') {
          saida.push(new Paragraph({
            numbering: i === 0 ? { reference: 'marcadores', level: 0 } : undefined,
            indent: i === 0 ? undefined : { left: 720 },
            alignment: AlignmentType.JUSTIFIED, spacing: { line: 360, after: 100 },
            children: runs(i === 0 ? `**${rotulo}:** ${parte}` : parte, corpo),
          }))
        } else if (parte.numerada) {
          saida.push(...parte.numerada.map((item) => new Paragraph({
            numbering: { reference: parte.ref ?? 'numeros', level: 1 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 300, after: 60 },
            children: runs(item, corpo),
          })))
        } else if (parte.lista) {
          saida.push(...parte.lista.map((item) => new Paragraph({
            numbering: { reference: 'marcadores', level: 1 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 300, after: 60 },
            children: runs(item, corpo),
          })))
        } else if (parte.tabela) {
          const [cab, linhas, pesos, opcoes] = parte.tabela
          if (parte.titulo) saida.push(new Paragraph({ keepNext: true, indent: { left: 720 }, spacing: { before: 80, after: 80 }, children: runs(parte.titulo, { size: 22 }) }))
          saida.push(tabela(cab, linhas, pesos, opcoes), new Paragraph({ spacing: { after: 160 }, children: [] }))
        } else if (parte.formula) {
          saida.push(...blocos.formula(parte.formula))
        }
      })
    }
    return saida
  },
  sumario: () => {
    const arquivoPaginas = path.join(aqui, 'paginas.json')
    const paginas = existsSync(arquivoPaginas) ? JSON.parse(readFileSync(arquivoPaginas, 'utf8')) : {}
    const titulos = conteudo.filter(([tipo]) => ['parte', 'secao', 'sub'].includes(tipo))
    return [
      new Paragraph({ spacing: { after: 240 }, children: [new TextRun({ text: 'Sumário', font: FONTE, bold: true, size: 28 })] }),
      ...titulos.map(([tipo, texto]) => {
        const nivel = { parte: 0, secao: 1, sub: 2 }[tipo]
        return new Paragraph({
          tabStops: [{ type: TabStopType.RIGHT, position: LARGURA_UTIL, leader: 'dot' }],
          indent: { left: nivel * 280, hanging: 0 },
          spacing: { after: nivel === 0 ? 100 : 60, before: nivel === 0 ? 100 : 0 },
          children: [new TextRun({ font: FONTE, size: 22, bold: nivel === 0, children: [texto, new Tab(), String(paginas[texto] ?? '')] })],
        })
      }),
    ]
  },
}

function capa() {
  const centro = (texto, tamanho, extra = {}) => new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: texto, font: FONTE, size: tamanho, ...extra })],
  })
  return [
    new Paragraph({ spacing: { before: 3600 }, children: [] }),
    centro('Documento de Especificação de Projeto Integrador', 32),
    centro(META.produto, 56, { bold: true, color: '1F4E9C' }),
    centro(META.subtitulo, 24),
    new Paragraph({ spacing: { before: 4200 }, children: [] }),
    centro(`Engenharia de Software – ${META.periodo} – ${META.fase}`, 24),
    centro(`Versão ${META.versao} – Anápolis, ${META.ano}`, 24),
    new Paragraph({ children: [new PageBreak()] }),
  ]
}

const filhos = [...capa()]
for (const [tipo, ...args] of conteudo) {
  if (!blocos[tipo]) throw new Error(`bloco desconhecido: ${tipo}`)
  filhos.push(...blocos[tipo](...args))
}

const doc = new Document({
  creator: 'Equipe Nox',
  title: `Documento de Especificação de Projeto Integrador – ${META.produto}`,
  description: `Versão ${META.versao}`,
  styles: {
    default: { document: { run: { font: FONTE, size: 24 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONTE, size: 28, bold: true, color: '000000' }, paragraph: { outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONTE, size: 26, bold: true, color: '000000' }, paragraph: { outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONTE, size: 24, bold: true, color: '000000' }, paragraph: { outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      {
        reference: 'marcadores',
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
          { level: 1, format: LevelFormat.BULLET, text: '◦', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1260, hanging: 360 } } } },
        ],
      },
      ...['numeros', 'numeros2', 'numeros3', 'numeros4', 'numeros5', 'numeros6', 'numeros7'].map((reference) => ({
        reference,
        levels: [
          { level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
          { level: 1, format: LevelFormat.DECIMAL, text: '%2.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1260, hanging: 360 } } } },
        ],
      })),
    ],
  },
  sections: [{
    properties: {
      titlePage: true,
      page: { margin: { top: 2268, bottom: 1985, left: 1701, right: 1418, header: 0, footer: 0 } },
    },
    headers: { first: cabecalho(260, 794), default: cabecalho(420, 640) },
    footers: { first: rodape, default: rodape },
    children: filhos,
  }],
})

const saida = path.join(aqui, `${META.arquivo}.docx`)
writeFileSync(saida, await Packer.toBuffer(doc))
console.log('gerado', path.basename(saida))
