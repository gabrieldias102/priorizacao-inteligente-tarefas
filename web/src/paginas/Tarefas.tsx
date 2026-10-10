import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../api'
import CartaoTarefa, { type AcoesTarefa } from '../componentes/CartaoTarefa'
import FormTarefa from '../componentes/FormTarefa'
import { Alerta, Botao, Selecao } from '../componentes/ui'
import { NOMES_CATEGORIA, NOMES_PRIORIDADE, NOMES_STATUS } from '../formato'
import { useSessao } from '../sessao'
import type { Categoria, DadosTarefa, Filtros, Prioridade, Status, Tarefa } from '../tipos'

function Resumo() {
  const { data } = useQuery({ queryKey: ['estatisticas'], queryFn: api.estatisticas })
  if (!data) return null
  const abertas = data.por_status.aberta + data.por_status.em_andamento
  const itens = [
    { rotulo: 'Em aberto', valor: String(abertas) },
    { rotulo: 'Concluídas', valor: String(data.por_status.concluida) },
    {
      rotulo: 'Sugestões aceitas',
      valor: data.taxa_aceitacao === null ? '—' : `${Math.round(data.taxa_aceitacao * 100)}%`,
    },
  ]
  return (
    <dl className="grid grid-cols-3 gap-3">
      {itens.map((item) => (
        <div key={item.rotulo} className="rounded-xl bg-white p-3 shadow-sm ring-1 ring-slate-200">
          <dt className="text-xs text-slate-500">{item.rotulo}</dt>
          <dd className="text-xl font-semibold">{item.valor}</dd>
        </div>
      ))}
    </dl>
  )
}

function BarraFiltros({ filtros, aoMudar }: { filtros: Filtros; aoMudar: (f: Filtros) => void }) {
  return (
    <div className="grid gap-2 sm:grid-cols-3" aria-label="Filtros">
      <Selecao
        aria-label="Filtrar por status"
        value={filtros.status ?? ''}
        onChange={(e) => aoMudar({ ...filtros, status: (e.target.value || undefined) as Status | undefined })}
      >
        <option value="">Todos os status</option>
        {Object.entries(NOMES_STATUS).map(([v, n]) => (
          <option key={v} value={v}>
            {n}
          </option>
        ))}
      </Selecao>
      <Selecao
        aria-label="Filtrar por categoria"
        value={filtros.categoria ?? ''}
        onChange={(e) => aoMudar({ ...filtros, categoria: (e.target.value || undefined) as Categoria | undefined })}
      >
        <option value="">Todas as categorias</option>
        {Object.entries(NOMES_CATEGORIA).map(([v, n]) => (
          <option key={v} value={v}>
            {n}
          </option>
        ))}
      </Selecao>
      <Selecao
        aria-label="Filtrar por prioridade"
        value={filtros.prioridade ?? ''}
        onChange={(e) => aoMudar({ ...filtros, prioridade: (e.target.value || undefined) as Prioridade | undefined })}
      >
        <option value="">Todas as prioridades</option>
        {Object.entries(NOMES_PRIORIDADE).map(([v, n]) => (
          <option key={v} value={v}>
            {n}
          </option>
        ))}
      </Selecao>
    </div>
  )
}

export default function Tarefas() {
  const { usuario, sair } = useSessao()
  const queryClient = useQueryClient()
  const [filtros, setFiltros] = useState<Filtros>({})
  const [formulario, setFormulario] = useState<'novo' | Tarefa | null>(null)
  const [erroAcao, setErroAcao] = useState<string | null>(null)

  const lista = useQuery({ queryKey: ['tarefas', filtros], queryFn: () => api.listar(filtros) })

  const atualizarTudo = () => {
    queryClient.invalidateQueries({ queryKey: ['tarefas'] })
    queryClient.invalidateQueries({ queryKey: ['estatisticas'] })
  }

  const salvar = useMutation({
    mutationFn: (dados: DadosTarefa) =>
      formulario && formulario !== 'novo' ? api.atualizar(formulario.id, dados) : api.criar(dados),
    onSuccess: () => {
      setFormulario(null)
      atualizarTudo()
    },
  })

  const acao = useMutation({
    mutationFn: (fazer: () => Promise<unknown>) => fazer(),
    onMutate: () => setErroAcao(null),
    onSuccess: atualizarTudo,
    onError: (erro) => setErroAcao(erro.message),
  })

  function acoesDe(tarefa: Tarefa): AcoesTarefa {
    return {
      confirmar: (p) => acao.mutate(() => api.confirmarPrioridade(tarefa.id, p)),
      pedirSugestao: () => acao.mutate(() => api.novaSugestao(tarefa.id)),
      avaliar: (util) => acao.mutate(() => api.avaliar(tarefa.id, util)),
      mudarStatus: (status) => acao.mutate(() => api.atualizar(tarefa.id, { status })),
      editar: () => {
        salvar.reset()
        setFormulario(tarefa)
      },
      excluir: () => {
        if (window.confirm(`Excluir "${tarefa.titulo}"?`)) acao.mutate(() => api.excluir(tarefa.id))
      },
    }
  }

  const filtrando = Object.values(filtros).some(Boolean)

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5 px-4 py-6">
      <header className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Minhas tarefas</h1>
          <p className="text-sm text-slate-500">Olá, {usuario?.nome}</p>
        </div>
        <Botao variante="discreto" onClick={sair}>
          Sair
        </Botao>
      </header>

      <Resumo />

      {formulario ? (
        <FormTarefa
          key={formulario === 'novo' ? 'novo' : formulario.id}
          inicial={formulario === 'novo' ? undefined : formulario}
          aoSalvar={(dados) => salvar.mutate(dados)}
          aoCancelar={() => setFormulario(null)}
          salvando={salvar.isPending}
          erro={salvar.error?.message}
        />
      ) : (
        <Botao
          className="self-start"
          onClick={() => {
            salvar.reset()
            setFormulario('novo')
          }}
        >
          + Nova tarefa
        </Botao>
      )}

      <BarraFiltros filtros={filtros} aoMudar={setFiltros} />

      {erroAcao && <Alerta>{erroAcao}</Alerta>}

      {lista.isPending && <p className="text-center text-sm text-slate-500">Carregando tarefas...</p>}
      {lista.isError && <Alerta>Não foi possível carregar as tarefas: {lista.error.message}</Alerta>}
      {lista.data && lista.data.length === 0 && (
        <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
          {filtrando ? 'Nenhuma tarefa com esses filtros.' : 'Nenhuma tarefa ainda. Adicione a primeira para ver a sugestão de prioridade.'}
        </p>
      )}
      <div className="flex flex-col gap-3">
        {lista.data?.map((tarefa) => (
          <CartaoTarefa key={tarefa.id} tarefa={tarefa} acoes={acoesDe(tarefa)} ocupado={acao.isPending} />
        ))}
      </div>
    </div>
  )
}
