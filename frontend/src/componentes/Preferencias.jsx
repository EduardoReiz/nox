import { useEffect, useRef, useState } from 'react'
import { conta, configAlertas } from '../dados/conta'
import { cancelarPush, inscreverPush } from '../dados/push'
import { useEnvio } from '../dados/useEnvio'
import { Botao, Mensagem } from './Formulario'

// Perfil de investidor (RF-011) e alertas (RF-011, RF-012). O perfil ainda não
// muda as recomendações: o documento deixa isso para os próximos períodos.

const PERFIS = [
  { id: 'conservador', nome: 'Conservador', texto: 'Prefiro perder pouco, mesmo ganhando menos. Uma queda forte me tiraria o sono.' },
  { id: 'moderado', nome: 'Moderado', texto: 'Aceito algumas quedas no caminho se, no longo prazo, puder ganhar mais.' },
  { id: 'arrojado', nome: 'Arrojado', texto: 'Aguento grandes oscilações e sei que posso perder boa parte do que investi.' },
]

const FREQUENCIAS = [
  { id: 'cada_sinal', nome: 'A cada mudança' },
  { id: 'resumo_diario', nome: 'Um resumo por dia' },
]

function Opcao({ grupo, valor, marcado, aoEscolher, titulo, texto }) {
  return (
    <label
      className={`flex cursor-pointer gap-3 rounded-lg border p-4 transition-colors ${
        marcado ? 'border-luar bg-ceu-alto' : 'border-linha hover:border-nevoa'
      }`}
    >
      <input type="radio" name={grupo} value={valor} checked={marcado} onChange={() => aoEscolher(valor)}
        className="mt-1 accent-[var(--color-luar)]" />
      <span>
        <span className="block font-semibold">{titulo}</span>
        {texto && <span className="mt-0.5 block text-sm leading-relaxed text-nevoa">{texto}</span>}
      </span>
    </label>
  )
}

function Interruptor({ rotulo, ligado, aoMudar }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-4">
      <span className="text-[15px]">{rotulo}</span>
      <input type="checkbox" role="switch" checked={ligado} onChange={(e) => aoMudar(e.target.checked)}
        className="peer sr-only" />
      <span
        aria-hidden="true"
        className="relative h-6 w-11 shrink-0 rounded-full bg-linha transition-colors peer-checked:bg-alta peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-luar after:absolute after:left-0.5 after:top-0.5 after:size-5 after:rounded-full after:bg-luar after:transition-transform peer-checked:after:translate-x-5"
      />
    </label>
  )
}

function BotaoTexto({ children, ...props }) {
  return (
    <button type="button" className="text-sm text-nevoa underline underline-offset-4 hover:text-luar disabled:opacity-60" {...props}>
      {children}
    </button>
  )
}

// Um canal: primeiro conectar (permissão do navegador ou conversa com o bot),
// depois ligar ou desligar.
function Canal({ nome, explicacao, estado, indisponivel, aoConectar, aoDesconectar, aoLigar, conectando, erro }) {
  return (
    <div className="py-4">
      {estado.conectado ? (
        <>
          <Interruptor rotulo={nome} ligado={estado.ativo} aoMudar={aoLigar} />
          <BotaoTexto onClick={aoDesconectar}>Desconectar</BotaoTexto>
        </>
      ) : (
        <>
          <p className="text-[15px]">{nome}</p>
          <p className="mt-1 text-sm leading-relaxed text-nevoa">{indisponivel ?? explicacao}</p>
          {!indisponivel && (
            <button
              type="button"
              onClick={aoConectar}
              disabled={conectando}
              className="mt-3 rounded-full border border-linha px-4 py-2 text-sm font-semibold hover:bg-ceu-alto disabled:opacity-60"
            >
              {conectando ? 'Aguarde...' : `Conectar ${nome.toLowerCase()}`}
            </button>
          )}
        </>
      )}
      {erro && <p className="mt-2 text-sm text-queda" aria-live="polite">{erro}</p>}
    </div>
  )
}

export default function Preferencias() {
  const [prefs, setPrefs] = useState(null)
  const [config, setConfig] = useState(null)
  const [salvo, setSalvo] = useState('')
  const [erroCanal, setErroCanal] = useState({})
  const [conectando, setConectando] = useState('')
  const [aguardaTelegram, setAguardaTelegram] = useState(false)
  const [teste, setTeste] = useState('')
  const vivo = useRef(true)

  useEffect(() => {
    vivo.current = true
    Promise.all([conta.preferencias(), configAlertas()]).then(([p, c]) => {
      if (vivo.current) {
        setPrefs(p)
        setConfig(c)
      }
    })
    return () => {
      vivo.current = false
    }
  }, [])

  // Enquanto a pessoa está no Telegram, confere a cada 3 s se o bot já ligou a conta.
  useEffect(() => {
    if (!aguardaTelegram) return
    const fim = Date.now() + 3 * 60_000
    const id = setInterval(async () => {
      const p = await conta.preferencias().catch(() => null)
      if (p?.canais.telegram.conectado || Date.now() > fim) {
        clearInterval(id)
        setAguardaTelegram(false)
        if (p && vivo.current) setPrefs((atual) => ({ ...atual, canais: p.canais }))
      }
    }, 3000)
    return () => clearInterval(id)
  }, [aguardaTelegram])

  const [salvar, { carregando, erro }] = useEnvio(async () => {
    setSalvo('')
    setPrefs(await conta.salvarPreferencias(prefs))
    setSalvo('Preferências salvas.')
  })

  if (!prefs || !config) return null

  const mudar = (parte) => {
    setSalvo('')
    setPrefs((p) => ({ ...p, ...parte }))
  }
  const ligar = (canal, ativo) => mudar({ canais: { ...prefs.canais, [canal]: { ...prefs.canais[canal], ativo } } })

  const recarregarCanais = async () => {
    const p = await conta.preferencias()
    setPrefs((atual) => ({ ...atual, canais: p.canais }))
  }

  const comErro = (canal, acao) => async () => {
    setErroCanal({})
    setConectando(canal)
    try {
      await acao()
    } catch (e) {
      setErroCanal({ [canal]: e.message })
    } finally {
      setConectando('')
    }
  }

  const conectarPush = comErro('push', async () => {
    await conta.conectarPush(await inscreverPush(config.push_chave_publica))
    await recarregarCanais()
  })
  const desconectarPush = comErro('push', async () => {
    await cancelarPush()
    await conta.desconectarPush()
    await recarregarCanais()
  })
  const conectarTelegram = comErro('telegram', async () => {
    const { link } = await conta.conectarTelegram()
    window.open(link, '_blank', 'noopener')
    setAguardaTelegram(true)
  })
  const desconectarTelegram = comErro('telegram', async () => {
    await conta.desconectarTelegram()
    await recarregarCanais()
  })

  const algumLigado = Object.values(prefs.canais).some((c) => c.conectado && c.ativo)

  const testar = async () => {
    setTeste('')
    try {
      const r = await conta.testarAlertas()
      const nomes = { push: 'Notificação', telegram: 'Telegram' }
      setTeste(Object.entries(r).map(([c, s]) => `${nomes[c]}: ${s === 'enviado' ? 'enviado' : s}`).join('. ') + '.')
    } catch (e) {
      setTeste(e.message)
    }
  }

  return (
    <form onSubmit={salvar} className="space-y-9">
      <fieldset>
        <legend className="font-serif text-xl">Seu perfil de investidor</legend>
        <p className="mb-4 mt-1 text-sm leading-relaxed text-nevoa">
          Qual frase combina mais com você? Isso fica guardado de forma cifrada e, nas próximas versões, vai ajustar as
          sugestões ao seu jeito de investir.
        </p>
        <div className="space-y-3">
          {PERFIS.map((p) => (
            <Opcao key={p.id} grupo="perfil" valor={p.id} titulo={p.nome} texto={p.texto}
              marcado={prefs.perfil_risco === p.id} aoEscolher={(v) => mudar({ perfil_risco: v })} />
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="font-serif text-xl">Alertas</legend>
        <p className="mb-2 mt-1 text-sm leading-relaxed text-nevoa">
          O Nox avisa quando a sugestão de um ativo que você acompanha muda, por exemplo de manter para comprar.
        </p>
        <div className="divide-y divide-linha border-y border-linha">
          <Canal
            nome="Notificações"
            explicacao="Avisos neste celular ou computador, mesmo com o Nox fechado. O navegador vai pedir sua permissão."
            indisponivel={!config.push_chave_publica ? 'As notificações ainda não foram configuradas no servidor do Nox.' : null}
            estado={prefs.canais.push}
            conectando={conectando === 'push'}
            erro={erroCanal.push}
            aoConectar={conectarPush}
            aoDesconectar={desconectarPush}
            aoLigar={(v) => ligar('push', v)}
          />
          <Canal
            nome="Telegram"
            explicacao={aguardaTelegram
              ? 'No Telegram, toque em Começar. Esta tela atualiza sozinha quando a conexão terminar.'
              : 'Mensagens com a explicação completa do sinal. Abre o Telegram para você iniciar a conversa com o bot do Nox.'}
            indisponivel={!config.telegram_bot ? 'O bot do Nox no Telegram ainda está sendo criado. Use as notificações por enquanto.' : null}
            estado={prefs.canais.telegram}
            conectando={conectando === 'telegram' || aguardaTelegram}
            erro={erroCanal.telegram}
            aoConectar={conectarTelegram}
            aoDesconectar={desconectarTelegram}
            aoLigar={(v) => ligar('telegram', v)}
          />
        </div>
        <p className="mb-3 mt-6 text-sm font-semibold">Com que frequência?</p>
        <div className="grid grid-cols-2 gap-3">
          {FREQUENCIAS.map((f) => (
            <Opcao key={f.id} grupo="frequencia" valor={f.id} titulo={f.nome}
              marcado={prefs.frequencia === f.id} aoEscolher={(v) => mudar({ frequencia: v })} />
          ))}
        </div>
        {algumLigado && (
          <div className="mt-5">
            <BotaoTexto onClick={testar}>Enviar um alerta de teste</BotaoTexto>
            {teste && <p className="mt-2 text-sm text-nevoa" aria-live="polite">{teste}</p>}
          </div>
        )}
      </fieldset>

      <div className="space-y-4">
        <Mensagem erro={erro} sucesso={salvo} />
        <Botao carregando={carregando} type="submit">Salvar preferências</Botao>
      </div>
    </form>
  )
}
