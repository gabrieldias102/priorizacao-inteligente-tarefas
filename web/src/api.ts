import type { DadosTarefa, Estatisticas, Filtros, Prioridade, Status, Tarefa, Token, Usuario } from './tipos'

const CHAVE_TOKEN = 'tarefas.token'

export class ErroApi extends Error {
  readonly status: number
  constructor(status: number, mensagem: string) {
    super(mensagem)
    this.status = status
  }
}

export function lerToken(): string | null {
  try {
    return localStorage.getItem(CHAVE_TOKEN)
  } catch {
    return null
  }
}

export function salvarToken(token: string | null) {
  try {
    if (token) localStorage.setItem(CHAVE_TOKEN, token)
    else localStorage.removeItem(CHAVE_TOKEN)
  } catch {
    // Sem armazenamento (modo privado): a sessão dura só até recarregar a página.
  }
}

// Avisado pelo AuthProvider para encerrar a sessão quando a API responde 401.
let aoExpirar: () => void = () => {}
export function quandoSessaoExpirar(callback: () => void) {
  aoExpirar = callback
}

async function mensagemDeErro(resposta: Response): Promise<string> {
  try {
    const corpo = await resposta.json()
    if (typeof corpo.detail === 'string') return corpo.detail
    if (Array.isArray(corpo.detail)) return 'Confira os campos do formulário'
  } catch {
    // corpo vazio ou não JSON
  }
  return `Erro ${resposta.status}`
}

async function chamar<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = lerToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body && typeof init.body === 'string') headers.set('Content-Type', 'application/json')

  const resposta = await fetch(`/api${caminho}`, { ...init, headers })
  if (resposta.status === 401 && token) aoExpirar()
  if (!resposta.ok) throw new ErroApi(resposta.status, await mensagemDeErro(resposta))
  if (resposta.status === 204) return undefined as T
  return resposta.json()
}

export const api = {
  registrar: (nome: string, email: string, senha: string) =>
    chamar<Token>('/auth/registrar', { method: 'POST', body: JSON.stringify({ nome, email, senha }) }),

  entrar: (email: string, senha: string) =>
    chamar<Token>('/auth/entrar', {
      method: 'POST',
      body: new URLSearchParams({ username: email, password: senha }),
    }),

  eu: () => chamar<Usuario>('/auth/eu'),

  listar: (filtros: Filtros = {}) => {
    const params = new URLSearchParams(Object.entries(filtros).filter(([, valor]) => Boolean(valor)))
    const consulta = params.toString()
    return chamar<Tarefa[]>(`/tarefas${consulta ? `?${consulta}` : ''}`)
  },

  criar: (dados: DadosTarefa) => chamar<Tarefa>('/tarefas', { method: 'POST', body: JSON.stringify(dados) }),

  atualizar: (id: string, dados: Partial<DadosTarefa> & { status?: Status }) =>
    chamar<Tarefa>(`/tarefas/${id}`, { method: 'PATCH', body: JSON.stringify(dados) }),

  excluir: (id: string) => chamar<void>(`/tarefas/${id}`, { method: 'DELETE' }),

  confirmarPrioridade: (id: string, prioridade: Prioridade) =>
    chamar<Tarefa>(`/tarefas/${id}/prioridade`, { method: 'POST', body: JSON.stringify({ prioridade }) }),

  novaSugestao: (id: string) => chamar<Tarefa>(`/tarefas/${id}/sugestao`, { method: 'POST' }),

  avaliar: (id: string, util: boolean) =>
    chamar<void>(`/tarefas/${id}/avaliacao`, { method: 'POST', body: JSON.stringify({ util }) }),

  estatisticas: () => chamar<Estatisticas>('/estatisticas'),
}
