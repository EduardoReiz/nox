import { useState } from 'react'
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { Botao, Campo, Mensagem, Titulo } from '../componentes/Formulario'
import { Carregando } from '../componentes/Partes'
import { conta } from '../dados/conta'
import { useEnvio } from '../dados/useEnvio'
import { useConta } from '../dados/ContaContexto'
import { horario } from '../dados/formato'

function DoisFatores({ ativo, aoMudar }) {
  const [config, setConfig] = useState(null)
  const [codigo, setCodigo] = useState('')
  const [senha, setSenha] = useState('')

  const [iniciar, inicio] = useEnvio(async () => setConfig(await conta.iniciar2fa()))
  const [ativar, ativacao] = useEnvio(async () => {
    await conta.ativar2fa(codigo)
    setConfig(null)
    aoMudar()
  })
  const [desativar, desativacao] = useEnvio(async () => {
    await conta.desativar2fa(senha)
    setSenha('')
    aoMudar()
  })

  if (ativo) {
    return (
      <form onSubmit={desativar} className="space-y-4">
        <p className="text-[15px] leading-relaxed">
          <span className="font-semibold text-alta">Ativa.</span> Para entrar, além da senha, o Nox pede o código do
          seu aplicativo autenticador.
        </p>
        <details className="text-sm">
          <summary className="cursor-pointer text-nevoa">Desativar a verificação em duas etapas</summary>
          <div className="mt-4 space-y-4">
            <Campo rotulo="Confirme com a sua senha" tipo="password" value={senha}
              onChange={(e) => setSenha(e.target.value)} autoComplete="current-password" required />
            <Mensagem erro={desativacao.erro} />
            <Botao secundario carregando={desativacao.carregando} type="submit">Desativar</Botao>
          </div>
        </details>
      </form>
    )
  }

  if (!config) {
    return (
      <div className="space-y-4">
        <p className="text-[15px] leading-relaxed text-nevoa">
          Proteja a conta com um código que muda a cada 30 segundos no seu celular. Mesmo que alguém descubra sua
          senha, não consegue entrar sem ele.
        </p>
        <Mensagem erro={inicio.erro} />
        <Botao carregando={inicio.carregando} onClick={iniciar}>Ativar a verificação em duas etapas</Botao>
      </div>
    )
  }

  return (
    <form onSubmit={ativar} className="space-y-5">
      <ol className="list-decimal space-y-2 pl-5 text-[15px] leading-relaxed">
        <li>Instale um aplicativo autenticador, como Google Authenticator ou Microsoft Authenticator.</li>
        <li>No aplicativo, adicione uma conta lendo este QR code.</li>
        <li>Digite o código de 6 números que aparecer.</li>
      </ol>
      <img src={config.qr} alt="QR code para o aplicativo autenticador" width="200" height="200"
        className="rounded-lg" />
      <p className="text-sm text-nevoa">
        Não consegue ler o QR code? Digite esta chave no aplicativo:{' '}
        <code className="break-all text-luar">{config.segredo}</code>
      </p>
      <Campo rotulo="Código do aplicativo" value={codigo}
        onChange={(e) => setCodigo(e.target.value.replace(/\D/g, '').slice(0, 6))}
        inputMode="numeric" autoComplete="one-time-code" placeholder="000000" required />
      <Mensagem erro={ativacao.erro} />
      <Botao carregando={ativacao.carregando} type="submit">Confirmar e ativar</Botao>
    </form>
  )
}

function Excluir() {
  const navegar = useNavigate()
  const { setUsuario } = useConta()
  const [senha, setSenha] = useState('')
  const [excluir, { carregando, erro }] = useEnvio(async () => {
    await conta.excluir(senha)
    setUsuario(null)
    navegar('/')
  })
  return (
    <details className="text-sm">
      <summary className="cursor-pointer text-nevoa">Excluir minha conta</summary>
      <form onSubmit={excluir} className="mt-4 space-y-4">
        <p className="text-[15px] leading-relaxed">
          Seu nome, e-mail, senha e preferências são apagados de vez. Não dá para desfazer.
        </p>
        <Campo rotulo="Confirme com a sua senha" tipo="password" value={senha}
          onChange={(e) => setSenha(e.target.value)} autoComplete="current-password" required />
        <Mensagem erro={erro} />
        <button
          disabled={carregando}
          className="w-full rounded-full border border-queda px-5 py-3 text-[15px] font-semibold text-queda hover:bg-queda hover:text-ceu disabled:opacity-60"
        >
          {carregando ? 'Aguarde...' : 'Excluir conta'}
        </button>
      </form>
    </details>
  )
}

export default function Conta() {
  const { usuario, recarregar, sair } = useConta()
  const navegar = useNavigate()
  const [parametros] = useSearchParams()

  if (usuario === undefined) return <Carregando />
  if (usuario === null) return <Navigate to="/entrar" replace />

  return (
    <div className="px-5 pb-10 pt-9">
      <Titulo sub={parametros.get('nova') ? 'Conta criada. Que tal ativar a verificação em duas etapas agora?' : undefined}>
        {usuario.nome}
      </Titulo>
      <dl className="divide-y divide-linha border-y border-linha text-[15px]">
        <div className="flex justify-between py-3">
          <dt className="text-nevoa">E-mail</dt>
          <dd>{usuario.email}</dd>
        </div>
        <div className="flex justify-between py-3">
          <dt className="text-nevoa">Conta criada em</dt>
          <dd>{horario(usuario.criado_em)}</dd>
        </div>
      </dl>

      <section className="mt-9">
        <h2 className="mb-4 font-serif text-xl">Verificação em duas etapas</h2>
        <DoisFatores ativo={usuario.dois_fatores} aoMudar={recarregar} />
      </section>

      <section className="mt-9 space-y-5 border-t border-linha pt-6">
        <Botao secundario onClick={async () => { await sair(); navegar('/') }}>Sair da conta</Botao>
        <Excluir />
      </section>
    </div>
  )
}
