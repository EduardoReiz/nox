import { useId, useState } from 'react'

// Peças dos formulários de conta: campo com rótulo, botão e mensagens.

export function Campo({ rotulo, dica, tipo = 'text', ...props }) {
  const id = useId()
  const [visivel, setVisivel] = useState(false)
  const senha = tipo === 'password'
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-semibold">
        {rotulo}
      </label>
      <div className="relative mt-1.5">
        <input
          id={id}
          type={senha && visivel ? 'text' : tipo}
          aria-describedby={dica ? `${id}-dica` : undefined}
          className="w-full rounded-lg border border-linha bg-ceu-alto px-3.5 py-3 text-[16px] text-luar placeholder:text-nevoa/70 focus:border-luar focus:outline-none"
          {...props}
        />
        {senha && (
          <button
            type="button"
            onClick={() => setVisivel((v) => !v)}
            className="absolute inset-y-0 right-2 my-auto h-9 rounded-md px-2 text-sm text-nevoa hover:text-luar"
          >
            {visivel ? 'Ocultar' : 'Mostrar'}
          </button>
        )}
      </div>
      {dica && (
        <p id={`${id}-dica`} className="mt-1.5 text-sm text-nevoa">
          {dica}
        </p>
      )}
    </div>
  )
}

export function Botao({ carregando, children, secundario = false, ...props }) {
  return (
    <button
      disabled={carregando}
      className={`w-full rounded-full px-5 py-3 text-[15px] font-semibold transition-colors disabled:opacity-60 ${
        secundario ? 'border border-linha text-luar hover:bg-ceu-alto' : 'bg-luar text-ceu hover:bg-white'
      }`}
      {...props}
    >
      {carregando ? 'Aguarde...' : children}
    </button>
  )
}

export function Mensagem({ erro, sucesso }) {
  if (!erro && !sucesso) return <p aria-live="polite" className="sr-only" />
  return (
    <p
      aria-live="polite"
      className={`border-l-2 pl-3 text-[15px] leading-relaxed ${erro ? 'border-queda text-queda' : 'border-alta text-alta'}`}
    >
      {erro || sucesso}
    </p>
  )
}

export function Titulo({ children, sub }) {
  return (
    <div className="mb-7">
      <h1 className="font-serif text-[2.1rem] font-medium leading-tight tracking-tight">{children}</h1>
      {sub && <p className="mt-2 text-[15px] leading-relaxed text-nevoa">{sub}</p>}
    </div>
  )
}
