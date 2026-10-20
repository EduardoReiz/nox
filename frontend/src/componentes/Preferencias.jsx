import { useEffect, useState } from 'react'
import { conta } from '../dados/conta'
import { useEnvio } from '../dados/useEnvio'
import { Botao, Campo, Mensagem } from './Formulario'

// Perfil de investidor e alertas (RF-011). O perfil ainda não muda as
// recomendações: o documento deixa isso para os próximos períodos.

const PERFIS = [
  { id: 'conservador', nome: 'Conservador', texto: 'Prefiro perder pouco, mesmo ganhando menos. Uma queda forte me tiraria o sono.' },
  { id: 'moderado', nome: 'Moderado', texto: 'Aceito algumas quedas no caminho se, no longo prazo, puder ganhar mais.' },
  { id: 'arrojado', nome: 'Arrojado', texto: 'Aguento grandes oscilações e sei que posso perder boa parte do que investi.' },
]

const FREQUENCIAS = [
  { id: 'cada_sinal', nome: 'A cada sinal novo' },
  { id: 'resumo_diario', nome: 'Um resumo por dia' },
]

function Opcao({ nome, grupo, valor, marcado, aoEscolher, titulo, texto }) {
  return (
    <label
      className={`flex cursor-pointer gap-3 rounded-lg border p-4 transition-colors ${
        marcado ? 'border-luar bg-ceu-alto' : 'border-linha hover:border-nevoa'
      }`}
    >
      <input type="radio" name={grupo} value={valor} checked={marcado} onChange={() => aoEscolher(valor)}
        className="mt-1 accent-[var(--color-luar)]" />
      <span>
        <span className="block font-semibold">{titulo ?? nome}</span>
        {texto && <span className="mt-0.5 block text-sm leading-relaxed text-nevoa">{texto}</span>}
      </span>
    </label>
  )
}

function Interruptor({ rotulo, ligado, aoMudar }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-4 py-3">
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

export default function Preferencias() {
  const [prefs, setPrefs] = useState(null)
  const [salvo, setSalvo] = useState('')

  useEffect(() => {
    let vivo = true
    conta.preferencias().then((p) => vivo && setPrefs(p))
    return () => {
      vivo = false
    }
  }, [])

  const [salvar, { carregando, erro }] = useEnvio(async () => {
    setSalvo('')
    setPrefs(await conta.salvarPreferencias(prefs))
    setSalvo('Preferências salvas.')
  })

  if (!prefs) return null

  const mudar = (parte) => {
    setSalvo('')
    setPrefs((p) => ({ ...p, ...parte }))
  }
  const mudarCanal = (canal, parte) =>
    mudar({ canais: { ...prefs.canais, [canal]: { ...prefs.canais[canal], ...parte } } })

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
          Avisos quando surgir um sinal para os ativos que você acompanha. O envio começa na próxima etapa do Nox; suas
          escolhas já ficam salvas.
        </p>
        <div className="divide-y divide-linha border-y border-linha">
          <Interruptor rotulo="Notificação no celular ou navegador" ligado={prefs.canais.push.ativo}
            aoMudar={(v) => mudarCanal('push', { ativo: v })} />
          <Interruptor rotulo="Mensagem no Telegram" ligado={prefs.canais.telegram.ativo}
            aoMudar={(v) => mudarCanal('telegram', { ativo: v })} />
        </div>
        {prefs.canais.telegram.ativo && (
          <div className="mt-4">
            <Campo rotulo="Seu usuário do Telegram" placeholder="@seu_usuario"
              value={prefs.canais.telegram.usuario ?? ''} autoComplete="off"
              onChange={(e) => mudarCanal('telegram', { usuario: e.target.value })} />
          </div>
        )}
        <p className="mb-3 mt-6 text-sm font-semibold">Com que frequência?</p>
        <div className="grid grid-cols-2 gap-3">
          {FREQUENCIAS.map((f) => (
            <Opcao key={f.id} grupo="frequencia" valor={f.id} nome={f.nome}
              marcado={prefs.frequencia === f.id} aoEscolher={(v) => mudar({ frequencia: v })} />
          ))}
        </div>
      </fieldset>

      <div className="space-y-4">
        <Mensagem erro={erro} sucesso={salvo} />
        <Botao carregando={carregando} type="submit">Salvar preferências</Botao>
      </div>
    </form>
  )
}
