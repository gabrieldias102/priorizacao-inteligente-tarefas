import type { Categoria, Prioridade, Status } from './tipos'

export const NOMES_PRIORIDADE: Record<Prioridade, string> = { baixa: 'Baixa', media: 'Média', alta: 'Alta' }
export const NOMES_STATUS: Record<Status, string> = {
  aberta: 'Aberta',
  em_andamento: 'Em andamento',
  concluida: 'Concluída',
  cancelada: 'Cancelada',
}
export const NOMES_CATEGORIA: Record<Categoria, string> = {
  estudo: 'Estudo',
  trabalho: 'Trabalho',
  pessoal: 'Pessoal',
  saude: 'Saúde',
  casa: 'Casa',
}

export const PRIORIDADES: Prioridade[] = ['alta', 'media', 'baixa']

export const CORES_PRIORIDADE: Record<Prioridade, string> = {
  alta: 'bg-red-100 text-red-800 ring-red-200',
  media: 'bg-amber-100 text-amber-800 ring-amber-200',
  baixa: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
}

const DIA = 24 * 60 * 60 * 1000

/** "Vence hoje", "Vence amanhã", "Vence em 5 dias", "Venceu há 2 dias". */
export function prazoRelativo(prazo: string, agora: Date = new Date()): string {
  const fim = new Date(prazo)
  const inicioHoje = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate())
  const inicioPrazo = new Date(fim.getFullYear(), fim.getMonth(), fim.getDate())
  const dias = Math.round((inicioPrazo.getTime() - inicioHoje.getTime()) / DIA)
  if (dias === 0) return 'Vence hoje'
  if (dias === 1) return 'Vence amanhã'
  if (dias > 1) return `Vence em ${dias} dias`
  if (dias === -1) return 'Venceu ontem'
  return `Venceu há ${-dias} dias`
}

export function dataCurta(prazo: string): string {
  return new Date(prazo).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Converte o valor de um <input type="datetime-local"> para ISO com fuso, e vice-versa. */
export function localParaIso(valor: string): string | null {
  return valor ? new Date(valor).toISOString() : null
}

export function isoParaLocal(iso: string | null): string {
  if (!iso) return ''
  const data = new Date(iso)
  const ajuste = data.getTimezoneOffset() * 60000
  return new Date(data.getTime() - ajuste).toISOString().slice(0, 16)
}
