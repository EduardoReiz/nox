// Teste de ponta a ponta do RF-010 no navegador: cadastro, verificação em
// duas etapas, login em dois passos, recuperação de senha e exclusão da conta.
//
// Precisa do PostgreSQL, da API (com o log em NOX_LOG_API) e do frontend no ar:
//   NOX_LOG_API=/caminho/api.log node e2e/conta.mjs
// Usa o Chrome instalado no computador, sem baixar outro navegador.

import { readFileSync } from 'node:fs'
import { mkdirSync } from 'node:fs'
import { chromium } from 'playwright-core'
import * as OTPAuth from 'otpauth'

const URL = process.env.NOX_URL ?? 'http://localhost:5173'
const LOG_API = process.env.NOX_LOG_API
const FOTOS = new globalThis.URL('../../experimentos/conta_rf010/evidencias/', import.meta.url).pathname
mkdirSync(FOTOS, { recursive: true })

const id = Date.now().toString(36)
const SENHA = 'lua-cheia-sobre-o-mar'
let passo = 0

function ok(cond, mensagem) {
  if (!cond) throw new Error(`FALHOU: ${mensagem}`)
  console.log(`  ok  ${mensagem}`)
}

async function foto(pagina, nome) {
  passo += 1
  await pagina.screenshot({ path: `${FOTOS}${String(passo).padStart(2, '0')}_${nome}.png`, fullPage: true })
}

const navegador = await chromium.launch({ channel: 'chrome', headless: true })
const contexto = await navegador.newContext({
  viewport: { width: 400, height: 880 },
  deviceScaleFactor: 2,
  reducedMotion: 'reduce',
})
const p = await contexto.newPage()
// Na primeira carga de módulos novos o Vite recarrega a página e interrompe a
// navegação em andamento (ERR_ABORTED). Nesse caso, tenta mais uma vez.
const irPara = p.goto.bind(p)
p.goto = async (url, op) => {
  try {
    return await irPara(url, op)
  } catch (e) {
    if (!String(e.message).includes('ERR_ABORTED')) throw e
    await p.waitForLoadState()
    return irPara(url, op)
  }
}
const erros = []
p.on('pageerror', (e) => erros.push(e.message))

try {
  console.log('Conta A: cadastro e verificação em duas etapas')
  const emailA = `ana.${id}@teste.nox`
  await p.goto(`${URL}/criar-conta`)
  await foto(p, 'criar_conta')
  await p.getByLabel('Nome').fill('Ana Teste')
  await p.getByLabel('E-mail').fill(emailA)
  await p.getByLabel('Senha').fill('curta')
  await p.getByRole('button', { name: 'Criar conta' }).click()
  // O navegador barra o envio? Não: o mínimo de 10 é regra do servidor.
  await p.getByText('pelo menos 10 caracteres', { exact: false }).last().waitFor()
  ok(true, 'senha curta recusada com mensagem')
  await p.getByLabel('Senha').fill(SENHA)
  await p.getByRole('button', { name: 'Criar conta' }).click()
  await p.waitForURL('**/conta?nova=1')
  await p.getByRole('heading', { name: 'Ana Teste' }).waitFor()
  ok(true, 'conta criada e sessão aberta')
  await p.getByRole('link', { name: /Sua conta, Ana Teste/ }).waitFor()
  ok(true, 'cabeçalho mostra a inicial')

  await p.getByRole('button', { name: 'Ativar a verificação em duas etapas' }).click()
  const segredo = (await p.locator('code').textContent()).trim()
  const qr = p.getByRole('img', { name: 'QR code para o aplicativo autenticador' })
  await qr.waitFor()
  ok(await qr.evaluate((img) => img.complete && img.naturalWidth > 0), 'QR code carregou como imagem')
  await foto(p, 'ativar_2fa')
  const totp = new OTPAuth.TOTP({ secret: OTPAuth.Secret.fromBase32(segredo) })
  await p.getByLabel('Código do aplicativo').fill('123456')
  await p.getByRole('button', { name: 'Confirmar e ativar' }).click()
  await p.getByText('Código incorreto ou expirado.').waitFor()
  ok(true, 'código errado não ativa o 2FA')
  await p.getByLabel('Código do aplicativo').fill(totp.generate())
  await p.getByRole('button', { name: 'Confirmar e ativar' }).click()
  await p.getByText('Ativa.').waitFor()
  ok(true, '2FA ativado com o código do aplicativo')
  await foto(p, '2fa_ativo')

  await p.getByRole('button', { name: 'Sair da conta' }).click()
  await p.getByRole('link', { name: 'Entrar' }).waitFor()
  ok(true, 'saiu da conta')

  console.log('Conta A: login em dois passos')
  await p.goto(`${URL}/entrar`)
  await p.getByLabel('E-mail').fill(emailA)
  await p.getByLabel('Senha').fill('senha-errada-123')
  await p.getByRole('button', { name: 'Entrar', exact: true }).click()
  await p.getByText('E-mail ou senha incorretos.').waitFor()
  ok(true, 'senha errada recusada')
  await foto(p, 'entrar_erro')
  await p.getByLabel('Senha').fill(SENHA)
  await p.getByRole('button', { name: 'Entrar', exact: true }).click()
  await p.getByRole('heading', { name: 'Código de verificação' }).waitFor()
  await foto(p, 'codigo_verificacao')
  const semSessao = await p.evaluate(() => fetch('/api/conta/eu').then((r) => r.status))
  ok(semSessao === 401, 'só a senha não abre sessão (o protótipo antigo abria)')
  // O código usado na ativação não vale de novo; usa o do próximo intervalo de 30 s.
  await p.getByLabel('Código').fill(totp.generate({ timestamp: Date.now() + 30_000 }))
  await p.getByRole('button', { name: 'Confirmar e entrar' }).click()
  await p.waitForURL(`${URL}/`)
  await p.getByRole('link', { name: /Sua conta/ }).waitFor()
  ok(true, 'entrou com senha e código')
  const cookies = await contexto.cookies()
  const sessao = cookies.find((c) => c.name === 'nox_sessao')
  ok(sessao?.httpOnly && sessao.sameSite === 'Strict', 'cookie de sessão httpOnly e SameSite=Strict')
  ok(!(await p.evaluate(() => document.cookie)).includes('nox_sessao'), 'o JavaScript da página não vê a sessão')

  console.log('Conta A: perfil e alertas (RF-011, RF-012)')
  await p.goto(`${URL}/conta`)
  await p.getByRole('radio', { name: /Moderado/ }).check()
  await p.getByRole('radio', { name: 'Um resumo por dia' }).check()
  await p.getByRole('button', { name: 'Salvar preferências' }).click()
  await p.getByText('Preferências salvas.').waitFor()
  await p.reload()
  await p.getByRole('radio', { name: /Moderado/ }).waitFor()
  ok(await p.getByRole('radio', { name: /Moderado/ }).isChecked(), 'perfil continua salvo depois de recarregar')
  ok(await p.getByRole('radio', { name: 'Um resumo por dia' }).isChecked(), 'frequência continua salva')
  await p.getByText('O bot do Nox no Telegram ainda está sendo criado').waitFor()
  ok(true, 'sem bot configurado, o Telegram avisa em vez de quebrar')

  // O Chrome headless não tem serviço de push: a inscrição falha. Serve para
  // conferir que o erro chega ao usuário em português.
  await contexto.grantPermissions(['notifications'], { origin: URL })
  await p.getByRole('button', { name: 'Conectar notificações' }).click()
  await p.getByText('O navegador não conseguiu ativar as notificações').waitFor({ timeout: 20_000 })
  ok(true, 'falha do navegador ao inscrever vira mensagem clara em português')

  // Uma inscrição de mentira, como a que o navegador entregaria, cadastrada
  // pela API: confere o caminho do servidor e da tela.
  const inscricao = { endpoint: 'https://push.invalid/e2e', keys: { p256dh: 'BOr_teste', auth: 'auth_teste' } }
  const cadastro = await p.evaluate((dados) => fetch('/api/conta/push', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dados),
  }).then((r) => r.status), inscricao)
  ok(cadastro === 204, 'API aceita a inscrição de notificação')
  await p.reload()
  const pushLigado = p.getByRole('switch', { name: 'Notificações' })
  await pushLigado.waitFor()
  ok(await pushLigado.isChecked(), 'canal de notificação aparece conectado e ligado')
  await p.getByRole('button', { name: 'Enviar um alerta de teste' }).click()
  const resultado = p.getByText(/^Notificação: /)
  await resultado.waitFor({ timeout: 30_000 })
  ok((await resultado.textContent()).startsWith('Notificação: falhou'),
    'endereço de push inexistente: o teste mostra a falha sem quebrar a tela')
  await foto(p, 'preferencias')

  console.log('Conta A: lista de ativos (RF-015)')
  await p.goto(`${URL}/sinais`)
  await p.getByRole('button', { name: 'Acompanhar Ethereum' }).click()
  await p.getByRole('heading', { name: 'Seus ativos' }).waitFor()
  await p.reload()
  await p.getByRole('button', { name: 'Deixar de acompanhar Ethereum' }).waitFor()
  ok(true, 'ativo acompanhado continua marcado depois de recarregar')
  await foto(p, 'sinais_com_lista')

  const meusDados = await p.evaluate(() => fetch('/api/conta/meus-dados').then((r) => r.json()))
  ok(meusDados.perfil_de_risco === 'moderado' && meusDados.ativos_acompanhados[0].ativo === 'ETHUSDT',
    'baixar meus dados traz perfil e lista')
  ok(!JSON.stringify(meusDados).includes('argon2'), 'arquivo de dados não traz o hash da senha')

  console.log('Conta B: recuperação de senha e exclusão')
  await contexto.clearCookies()
  const emailB = `bruno.${id}@teste.nox`
  await p.goto(`${URL}/criar-conta`)
  await p.getByLabel('Nome').fill('Bruno Teste')
  await p.getByLabel('E-mail').fill(emailB)
  await p.getByLabel('Senha').fill(SENHA)
  await p.getByRole('button', { name: 'Criar conta' }).click()
  await p.waitForURL('**/conta?nova=1')
  await contexto.clearCookies()

  await p.goto(`${URL}/esqueci-senha`)
  await p.getByLabel('E-mail').fill(emailB)
  await p.getByRole('button', { name: 'Enviar link' }).click()
  await p.getByText('Se houver uma conta com esse e-mail').waitFor()
  await foto(p, 'esqueci_senha')
  ok(true, 'pedido de recuperação com resposta neutra')

  const log = readFileSync(LOG_API, 'utf8')
  const link = [...log.matchAll(/(http\S+redefinir-senha\?token=\S+)/g)].at(-1)[1]
  await p.goto(link)
  await p.getByLabel('Senha nova').fill('estrela-do-sul-2027')
  await p.getByRole('button', { name: 'Salvar senha nova' }).click()
  await p.getByRole('heading', { name: 'Senha alterada' }).waitFor()
  ok(true, 'senha redefinida pelo link do e-mail')
  await p.goto(link)
  await p.getByLabel('Senha nova').fill('outra-senha-boa-2028')
  await p.getByRole('button', { name: 'Salvar senha nova' }).click()
  await p.getByText('Este link expirou ou já foi usado').waitFor()
  ok(true, 'o mesmo link não funciona duas vezes')

  await p.goto(`${URL}/entrar`)
  await p.getByLabel('E-mail').fill(emailB)
  await p.getByLabel('Senha').fill('estrela-do-sul-2027')
  await p.getByRole('button', { name: 'Entrar', exact: true }).click()
  await p.waitForURL(`${URL}/`)
  ok(true, 'entrou com a senha nova')

  await p.goto(`${URL}/conta`)
  await p.getByText('Excluir minha conta').click()
  await foto(p, 'excluir_conta')
  await p.getByLabel('Confirme com a sua senha').fill('estrela-do-sul-2027')
  await p.getByRole('button', { name: 'Excluir conta' }).click()
  await p.waitForURL(`${URL}/`)
  await p.goto(`${URL}/entrar`)
  await p.getByLabel('E-mail').fill(emailB)
  await p.getByLabel('Senha').fill('estrela-do-sul-2027')
  await p.getByRole('button', { name: 'Entrar', exact: true }).click()
  await p.getByText('E-mail ou senha incorretos.').waitFor()
  ok(true, 'conta excluída não entra mais')

  ok(erros.length === 0, `nenhum erro de JavaScript na página${erros.length ? ': ' + erros.join('; ') : ''}`)
  console.log('\nTudo certo.')
} catch (e) {
  await foto(p, 'falha').catch(() => {})
  console.error(e.message)
  process.exitCode = 1
} finally {
  await navegador.close()
}
