// Roda os testes da Experimentação 5 contra o protótipo antigo em execução.
import { createRequire } from 'node:module'
import crypto from 'node:crypto'
const { TOTP, Secret } = await import('../../../frontend/node_modules/otpauth/dist/otpauth.esm.js')

const base = 'http://localhost:3333'
const chamar = async (metodo, caminho, corpo, token) => {
  const r = await fetch(base + caminho, { method: metodo, headers: { 'content-type': 'application/json', ...(token ? { authorization: `Bearer ${token}` } : {}) }, body: corpo ? JSON.stringify(corpo) : metodo === 'POST' ? '{}' : undefined })
  let dados = null; try { dados = await r.json() } catch {}
  return { status: r.status, dados }
}
const resultado = {}

// 1. Rota de preços: sem autenticação e sem validação
resultado.precos_sem_login = (await chamar('POST', '/webhooks/prices', { symbol: 'FALSO', ts: '2026-10-21T12:00:00Z', price: 1 })).status
resultado.precos_sem_validacao = (await chamar('POST', '/webhooks/prices', { symbol: 'BTCUSDT', price: -5 })).status
resultado.precos_gravados = (await chamar('GET', '/assets')).dados

// 2. Cadastro, 2FA e login
const email = `teste${Date.now()}@exemplo.com`, senha = 'SenhaForte123'
const cad = await chamar('POST', '/auth/register', { email, password: senha, name: 'Teste' })
resultado.cadastro = cad.status
const token = cad.dados.accessToken
resultado.sinais_apos_cadastro = (await chamar('GET', '/signals', null, token)).dados
const setup = await chamar('POST', '/2fa/setup'.replace('/2fa', '/auth/2fa'), null, token)
const otpauth = setup.dados.otpauth
const segredo = new URL(otpauth).searchParams.get('secret')
resultado.segredo = { texto: segredo, tamanho: segredo.length, rotulo_no_qr: decodeURIComponent(new URL(otpauth).pathname) }
resultado.me_apos_setup = (await chamar('GET', '/users/me', null, token)).dados
const login = await chamar('POST', '/auth/login', { email, password: senha })
resultado.login_com_2fa = { status: login.status, corpo: login.dados }

// 3. O código que o servidor aceita x o código que um aplicativo autenticador mostra
const totpServidor = (s, janela = 0) => {
  const contador = Math.floor(Date.now() / 1000 / 30) + janela
  const msg = Buffer.alloc(8); msg.writeBigUInt64BE(BigInt(contador))
  const h = crypto.createHmac('sha1', Buffer.from(s, 'ascii')).update(msg).digest()
  const o = h[h.length - 1] & 0xf
  return ((h.readUInt32BE(o) & 0x7fffffff) % 1000000).toString().padStart(6, '0')
}
const codigoServidor = totpServidor(segredo)
const codigoApp = new TOTP({ secret: Secret.fromBase32(segredo), digits: 6, period: 30 }).generate()
resultado.codigos = { esperado_pelo_servidor: codigoServidor, mostrado_pelo_aplicativo: codigoApp, iguais: codigoServidor === codigoApp }
resultado.verificar_com_codigo_do_aplicativo = (await chamar('POST', '/auth/verify-2fa', { email, code: codigoApp })).status

// 4. Acesso só com e-mail e código, sem a senha
const sem_senha = await chamar('POST', '/auth/verify-2fa', { email, code: codigoServidor })
resultado.verify_2fa_sem_senha = { status: sem_senha.status, devolveu_tokens: Boolean(sem_senha.dados?.accessToken) }

// 5. Quantos segredos saem curtos
const tamanhos = []
for (let i = 0; i < 30; i++) {
  const c = await chamar('POST', '/auth/register', { email: `t${i}${Date.now()}@exemplo.com`, password: senha })
  const s = await chamar('POST', '/auth/2fa/setup', null, c.dados.accessToken)
  tamanhos.push(new URL(s.dados.otpauth).searchParams.get('secret').length)
}
resultado.tamanho_dos_segredos = { min: Math.min(...tamanhos), max: Math.max(...tamanhos), abaixo_de_16: tamanhos.filter((t) => t < 16).length, de: tamanhos.length }
console.log(JSON.stringify(resultado, null, 2))
