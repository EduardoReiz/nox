// Chamadas da API de conta. A sessão vai num cookie httpOnly que o navegador
// manda sozinho; o JavaScript nunca vê o token.

async function pedir(caminho, { metodo = 'POST', corpo } = {}) {
  let resposta
  try {
    resposta = await fetch(`/api/conta${caminho}`, {
      method: metodo,
      headers: corpo ? { 'Content-Type': 'application/json' } : undefined,
      body: corpo ? JSON.stringify(corpo) : undefined,
    })
  } catch {
    throw new Error('O Nox não respondeu. Verifique a conexão e tente de novo.')
  }
  if (resposta.status === 204) return null
  const dados = await resposta.json().catch(() => ({}))
  if (!resposta.ok) {
    const detalhe = typeof dados.detail === 'string' ? dados.detail : 'Confira os campos e tente de novo.'
    const erro = new Error(detalhe)
    erro.status = resposta.status
    throw erro
  }
  return dados
}

export const conta = {
  eu: () => pedir('/eu', { metodo: 'GET' }),
  cadastrar: (nome, email, senha) => pedir('/cadastro', { corpo: { nome, email, senha } }),
  entrar: (email, senha) => pedir('/entrar', { corpo: { email, senha } }),
  confirmarCodigo: (desafio, codigo) => pedir('/entrar/codigo', { corpo: { desafio, codigo } }),
  sair: () => pedir('/sair'),
  iniciar2fa: () => pedir('/2fa/iniciar'),
  ativar2fa: (codigo) => pedir('/2fa/ativar', { corpo: { codigo } }),
  desativar2fa: (senha) => pedir('/2fa/desativar', { corpo: { senha } }),
  esqueci: (email) => pedir('/senha/esqueci', { corpo: { email } }),
  redefinir: (token, senha) => pedir('/senha/redefinir', { corpo: { token, senha } }),
  excluir: (senha) => pedir('/excluir', { corpo: { senha } }),
}
