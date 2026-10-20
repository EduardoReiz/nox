import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Botao, Campo, Mensagem, Titulo } from '../componentes/Formulario'
import { conta } from '../dados/conta'
import { useEnvio } from '../dados/useEnvio'
import { useConta } from '../dados/ContaContexto'

export default function CriarConta() {
  const navegar = useNavigate()
  const { setUsuario } = useConta()
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')

  const [criar, { carregando, erro }] = useEnvio(async () => {
    setUsuario(await conta.cadastrar(nome, email, senha))
    navegar('/conta?nova=1')
  })

  const faltam = Math.max(0, 10 - senha.length)

  return (
    <form onSubmit={criar} className="space-y-5 px-5 pb-10 pt-9">
      <Titulo sub="Pedimos só nome, e-mail e senha. Nada de CPF, endereço ou dados do banco.">Criar conta</Titulo>
      <Campo rotulo="Nome" value={nome} onChange={(e) => setNome(e.target.value)} autoComplete="name"
        maxLength={80} required />
      <Campo rotulo="E-mail" tipo="email" value={email} onChange={(e) => setEmail(e.target.value)}
        autoComplete="email" required />
      <Campo
        rotulo="Senha"
        tipo="password"
        value={senha}
        onChange={(e) => setSenha(e.target.value)}
        autoComplete="new-password"
        maxLength={128}
        required
        dica={
          faltam > 0
            ? `Pelo menos 10 caracteres. Faltam ${faltam}. Uma frase curta é fácil de lembrar e difícil de adivinhar.`
            : 'Tamanho bom. Evite senhas que você usa em outros sites.'
        }
      />
      <Mensagem erro={erro} />
      <Botao carregando={carregando} type="submit">Criar conta</Botao>
      <p className="text-sm text-nevoa">
        Já tem conta?{' '}
        <Link to="/entrar" className="underline underline-offset-4 hover:text-luar">
          Entrar
        </Link>
      </p>
    </form>
  )
}
