import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Lua from '../componentes/Lua'
import { Acao, AvisoRisco, Carregando, Erro, Termo } from '../componentes/Partes'
import { conta } from '../dados/conta'
import { useConta } from '../dados/ContaContexto'
import { buscarSinais } from '../dados/fonte'
import { dolar, horario, porcentagem, simbolo } from '../dados/formato'
import { useDados } from '../dados/useDados'

// Feed de Sinais (RF-009): o sinal mais recente de cada ativo, do mais
// confiante ao menos confiante, com o aviso de risco à vista (RF-013). Quem
// tem conta marca os ativos que acompanha (RF-015), que aparecem primeiro.

function Estrela({ nome, marcada, aoTrocar }) {
  return (
    <button
      type="button"
      onClick={aoTrocar}
      aria-pressed={marcada}
      aria-label={marcada ? `Deixar de acompanhar ${nome}` : `Acompanhar ${nome}`}
      className="flex size-11 shrink-0 items-center justify-center rounded-full text-nevoa hover:bg-ceu-alto hover:text-luar"
    >
      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"
        fill={marcada ? 'var(--color-luar)' : 'none'} stroke={marcada ? 'var(--color-luar)' : 'currentColor'}
        strokeWidth="1.6" strokeLinejoin="round">
        <path d="M12 3.5l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.8l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z" />
      </svg>
    </button>
  )
}

function Linha({ s, estrela }) {
  const conteudo = (
    <>
      <Lua score={s.disponivel ? s.score : 0} acao={s.acao} tamanho={48} />
      <div className="min-w-0 flex-1">
        <p className="font-semibold">
          {s.nome} <span className="font-normal text-nevoa">{simbolo(s.ativo)}</span>
        </p>
        {s.preco && (
          <p className="text-sm text-nevoa">
            {dolar(s.preco.ultimo)}{' '}
            <span className={s.preco.variacao_24h_pct >= 0 ? 'text-alta' : 'text-queda'}>
              {porcentagem(s.preco.variacao_24h_pct)}
            </span>
          </p>
        )}
        {s.divergencia && (
          <p className="mt-1 text-sm text-aviso">Gráfico e notícias discordam, confiança reduzida</p>
        )}
        {!s.disponivel && <p className="mt-1 text-sm text-nevoa">Sem sinal agora: {s.motivo}.</p>}
      </div>
      {s.disponivel && (
        <div className="text-right">
          <Acao acao={s.acao} className="text-lg" />
          <p className="text-sm text-nevoa">{s.score} de 100</p>
        </div>
      )}
    </>
  )
  return (
    <li className="flex items-center border-b border-linha pr-2">
      {s.disponivel ? (
        <Link to={`/sinais/${s.ativo}`} className="flex flex-1 items-center gap-4 py-4 pl-5 pr-2 hover:bg-ceu-alto/60">
          {conteudo}
        </Link>
      ) : (
        <div className="flex flex-1 items-center gap-4 py-4 pl-5 pr-2">{conteudo}</div>
      )}
      {estrela}
    </li>
  )
}

// Lista de acompanhamento do usuário, salva no servidor a cada toque.
function useLista(usuario) {
  const [lista, setLista] = useState([])
  const [erro, setErro] = useState('')

  useEffect(() => {
    if (!usuario) return
    let vivo = true
    conta.lista().then((r) => vivo && setLista(r.ativos), () => {})
    return () => {
      vivo = false
    }
  }, [usuario])

  const trocar = async (ativo) => {
    const anterior = lista
    const nova = lista.includes(ativo) ? lista.filter((a) => a !== ativo) : [...lista, ativo]
    setLista(nova)
    setErro('')
    try {
      setLista((await conta.salvarLista(nova)).ativos)
    } catch (e) {
      setLista(anterior)
      setErro(e.message)
    }
  }

  return { lista: usuario ? lista : [], trocar, erro }
}

export default function Feed() {
  const { usuario } = useConta()
  const { dados, erro, carregando } = useDados(buscarSinais)
  const { lista, trocar, erro: erroLista } = useLista(usuario)
  const ordenados = dados ? [...dados].sort((a, b) => (b.score ?? -1) - (a.score ?? -1)) : []
  const meus = ordenados.filter((s) => lista.includes(s.ativo))
  const outros = ordenados.filter((s) => !lista.includes(s.ativo))
  const gerado = dados?.find((s) => s.gerado_em)?.gerado_em

  const linhas = (sinais) =>
    sinais.map((s) => (
      <Linha
        key={s.ativo}
        s={s}
        estrela={usuario && <Estrela nome={s.nome} marcada={lista.includes(s.ativo)} aoTrocar={() => trocar(s.ativo)} />}
      />
    ))

  return (
    <>
      <div className="px-5 pb-5 pt-9">
        <h1 className="font-serif text-[2.1rem] font-medium leading-tight tracking-tight">Sinais</h1>
        <p className="mt-2 text-[15px] leading-relaxed text-nevoa">
          Do mais ao menos confiante. Abaixo de 60 de <Termo id="score">confiança</Termo>, a leitura é sempre
          neutra. Toque num ativo para ver o porquê.
        </p>
        {usuario === null && (
          <p className="mt-3 text-sm text-nevoa">
            <Link to="/entrar" className="underline underline-offset-4 hover:text-luar">Entre na sua conta</Link> para
            marcar os ativos que você acompanha.
          </p>
        )}
        {usuario && lista.length === 0 && (
          <p className="mt-3 text-sm text-nevoa">Toque na estrela de um ativo para acompanhá-lo. Ele passa a aparecer primeiro.</p>
        )}
        {erroLista && <p className="mt-3 text-sm text-queda" aria-live="polite">{erroLista}</p>}
      </div>
      {carregando && <Carregando />}
      {erro && <Erro erro={erro} />}
      {dados && (
        <>
          {meus.length > 0 && (
            <section aria-labelledby="meus">
              <h2 id="meus" className="px-5 pb-2 font-serif text-lg">Seus ativos</h2>
              <ul className="border-t border-linha">{linhas(meus)}</ul>
              <h2 className="px-5 pb-2 pt-7 font-serif text-lg">Outros ativos</h2>
            </section>
          )}
          <ul className="border-t border-linha">{linhas(outros)}</ul>
          <div className="space-y-4 px-5 py-7">
            {gerado && <p className="text-xs text-nevoa">Calculados em {horario(gerado)}, horário de Brasília.</p>}
            <AvisoRisco texto={dados.find((s) => s.aviso_risco)?.aviso_risco ?? ''} />
          </div>
        </>
      )}
    </>
  )
}
