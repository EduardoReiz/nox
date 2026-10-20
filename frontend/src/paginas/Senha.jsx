import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Botao, Campo, Mensagem, Titulo } from '../componentes/Formulario'
import { conta } from '../dados/conta'
import { useEnvio } from '../dados/useEnvio'

export function EsqueciSenha() {
  const [email, setEmail] = useState('')
  const [resposta, setResposta] = useState('')
  const [enviar, { carregando, erro }] = useEnvio(async () => {
    setResposta((await conta.esqueci(email)).mensagem)
  })

  return (
    <form onSubmit={enviar} className="space-y-5 px-5 pb-10 pt-9">
      <Titulo sub="Digite o e-mail da sua conta. Vamos mandar um link para você criar uma senha nova.">
        Esqueci a senha
      </Titulo>
      <Campo rotulo="E-mail" tipo="email" value={email} onChange={(e) => setEmail(e.target.value)}
        autoComplete="email" required />
      <Mensagem erro={erro} sucesso={resposta} />
      <Botao carregando={carregando} type="submit">Enviar link</Botao>
      <Link to="/entrar" className="block text-sm text-nevoa underline underline-offset-4 hover:text-luar">
        Voltar para entrar
      </Link>
    </form>
  )
}

export function RedefinirSenha() {
  const [parametros] = useSearchParams()
  const token = parametros.get('token') ?? ''
  const [senha, setSenha] = useState('')
  const [pronto, setPronto] = useState('')
  const [salvar, { carregando, erro }] = useEnvio(async () => {
    setPronto((await conta.redefinir(token, senha)).mensagem)
  })

  if (pronto) {
    return (
      <div className="space-y-5 px-5 pb-10 pt-9">
        <Titulo sub={pronto}>Senha alterada</Titulo>
        <Link to="/entrar" className="inline-block rounded-full bg-luar px-5 py-3 text-[15px] font-semibold text-ceu">
          Entrar
        </Link>
      </div>
    )
  }

  return (
    <form onSubmit={salvar} className="space-y-5 px-5 pb-10 pt-9">
      <Titulo sub="Depois de salvar, quem estiver conectado com a senha antiga sai da conta.">Senha nova</Titulo>
      {!token && <Mensagem erro="Este endereço está incompleto. Abra o link que enviamos por e-mail." />}
      <Campo rotulo="Senha nova" tipo="password" value={senha} onChange={(e) => setSenha(e.target.value)}
        autoComplete="new-password" maxLength={128} required dica="Pelo menos 10 caracteres." />
      <Mensagem erro={erro} />
      <Botao carregando={carregando} type="submit" disabled={!token}>Salvar senha nova</Botao>
    </form>
  )
}
