export type Prioridade = 'baixa' | 'media' | 'alta'
export type Status = 'aberta' | 'em_andamento' | 'concluida' | 'cancelada'
export type Categoria = 'estudo' | 'trabalho' | 'pessoal' | 'saude' | 'casa'

export type Usuario = { id: string; nome: string; email: string }
export type Token = { access_token: string; token_type: 'bearer'; usuario: Usuario }

export type Fator = { atributo: string; valor: number | string; descricao: string; peso: number }

export type Sugestao = {
  prioridade_sugerida: Prioridade
  probabilidades: Record<Prioridade, number> | null
  fatores: Fator[] | null
  modelo_versao: string
  aceita: boolean | null
  util: boolean | null
  criado_em: string
}

export type Tarefa = {
  id: string
  titulo: string
  descricao: string | null
  prazo: string | null
  categoria: Categoria
  impacto: number
  complexidade: number
  esforco_estimado: number
  prioridade_sugerida: Prioridade | null
  prioridade_confirmada: Prioridade | null
  status: Status
  modelo_versao: string | null
  criado_em: string
  atualizado_em: string
  concluida_em: string | null
  sugestao: Sugestao | null
}

export type DadosTarefa = {
  titulo: string
  descricao: string | null
  prazo: string | null
  categoria: Categoria
  impacto: number
  complexidade: number
  esforco_estimado: number
}

export type Filtros = { status?: Status; categoria?: Categoria; prioridade?: Prioridade }

export type Estatisticas = {
  total: number
  por_status: Record<Status, number>
  por_prioridade: Record<Prioridade, number>
  sugestoes: number
  sugestoes_aceitas: number
  sugestoes_ajustadas: number
  taxa_aceitacao: number | null
}
