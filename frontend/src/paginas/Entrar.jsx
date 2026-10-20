import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Botao, Campo, Mensagem, Titulo } from '../componentes/Formulario'
import { conta } from '../dados/conta'
import { useEnvio } from '../dados/useEnvio'
import { useConta } from '../dados/ContaContexto'

// Login em dois passos quando a verificação em duas etapas está ativa:
// primeiro e-mail e senha, depois o código do aplicativo autenticador.
export default function Entrar() {
  const navegar = useNavigate()
  const { setUsuario } = useConta()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [desafio, setDesafio] = useState(null)
  const [codigo, setCodigo] = useState('')

  const [entrar, passo1] = useEnvio(async () => {
    const r = await conta.entrar(email, senha)
    if (r.precisa_codigo) {
      setDesafio(r.desafio)
      setSenha('')
    } else {
      setUsuario(r.usuario)
      navegar('/')
    }
  })

  const [confirmar, passo2] = useEnvio(async () => {
    setUsuario(await conta.confirmarCodigo(desafio, codigo))
    navegar('/')
  })

  if (desafio) {
    return (
      <form onSubmit={confirmar} className="space-y-5 px-5 pb-10 pt-9">
        <Titulo sub="Abra o aplicativo autenticador no celular e digite o código de 6 números que aparece para o Nox.">
          Código de verificação
        </Titulo>
        <Campo
          rotulo="Código"
          value={codigo}
          onChange={(e) => setCodigo(e.target.value.replace(/\D/g, '').slice(0, 6))}
          inputMode="numeric"
          autoComplete="one-time-code"
          placeholder="000000"
          autoFocus
          required
        />
        <Mensagem erro={passo2.erro} />
        <Botao carregando={passo2.carregando} type="submit">Confirmar e entrar</Botao>
        <button
          type="button"
          onClick={() => setDesafio(null)}
          className="block text-sm text-nevoa underline underline-offset-4 hover:text-luar"
        >
          Entrar com outra conta
        </button>
      </form>
    )
  }

  return (
    <form onSubmit={entrar} className="space-y-5 px-5 pb-10 pt-9">
      <Titulo sub="Com uma conta você acompanha seus ativos e recebe alertas.">Entrar</Titulo>
      <Campo rotulo="E-mail" tipo="email" value={email} onChange={(e) => setEmail(e.target.value)}
        autoComplete="email" required />
      <Campo rotulo="Senha" tipo="password" value={senha} onChange={(e) => setSenha(e.target.value)}
        autoComplete="current-password" required />
      <Mensagem erro={passo1.erro} />
      <Botao carregando={passo1.carregando} type="submit">Entrar</Botao>
      <div className="flex justify-between text-sm">
        <Link to="/esqueci-senha" className="text-nevoa underline underline-offset-4 hover:text-luar">
          Esqueci a senha
        </Link>
        <Link to="/criar-conta" className="text-nevoa underline underline-offset-4 hover:text-luar">
          Criar conta
        </Link>
      </div>
    </form>
  )
}
