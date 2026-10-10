import type { Tarefa } from '../tipos'

type Rota = { metodo: string; caminho: RegExp; responder: (corpo: unknown) => { status?: number; json?: unknown } }

/** Substitui o fetch global por uma API em memória e registra as chamadas. */
export function apiFalsa(rotas: Rota[]) {
  const chamadas: { metodo: string; caminho: string; corpo: unknown }[] = []
  globalThis.fetch = (async (entrada: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(entrada).replace(/^\/api/, '')
    const metodo = init.method ?? 'GET'
    let corpo: unknown = init.body
    if (typeof init.body === 'string') corpo = JSON.parse(init.body)
    else if (init.body instanceof URLSearchParams) corpo = Object.fromEntries(init.body)
    chamadas.push({ metodo, caminho: url, corpo })
    const rota = rotas.find((r) => r.metodo === metodo && r.caminho.test(url))
    if (!rota) return new Response(JSON.stringify({ detail: `sem rota para ${metodo} ${url}` }), { status: 404 })
    const { status = 200, json } = rota.responder(corpo)
    return new Response(status === 204 ? null : JSON.stringify(json), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  }) as typeof fetch
  return chamadas
}

export function tarefaExemplo(parcial: Partial<Tarefa> = {}): Tarefa {
  return {
    id: 't1',
    titulo: 'Entregar relatório',
    descricao: null,
    prazo: null,
    categoria: 'trabalho',
    impacto: 4,
    complexidade: 3,
    esforco_estimado: 2,
    prioridade_sugerida: 'alta',
    prioridade_confirmada: null,
    status: 'aberta',
    modelo_versao: 'v1',
    criado_em: '2026-10-10T12:00:00Z',
    atualizado_em: '2026-10-10T12:00:00Z',
    concluida_em: null,
    sugestao: {
      prioridade_sugerida: 'alta',
      probabilidades: { alta: 0.82, media: 0.15, baixa: 0.03 },
      fatores: [
        { atributo: 'prazo', valor: 1, descricao: 'Prazo em 1 dia', peso: 0.9 },
        { atributo: 'impacto', valor: 4, descricao: 'Impacto 4 de 5', peso: 0.4 },
        { atributo: 'esforco_estimado', valor: 2, descricao: 'Esforço de 2 h', peso: -0.1 },
        { atributo: 'categoria', valor: 'trabalho', descricao: 'Categoria trabalho', peso: 0.001 },
      ],
      modelo_versao: 'v1',
      aceita: null,
      util: null,
      criado_em: '2026-10-10T12:00:00Z',
    },
    ...parcial,
  }
}
