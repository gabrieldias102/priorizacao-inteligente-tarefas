import { useState } from 'react'
import { CORES_PRIORIDADE, dataCurta, NOMES_CATEGORIA, NOMES_PRIORIDADE, NOMES_STATUS, PRIORIDADES, prazoRelativo } from '../formato'
import type { Prioridade, Status, Tarefa } from '../tipos'
import Fatores from './Fatores'
import { Botao } from './ui'

export type AcoesTarefa = {
  confirmar: (prioridade: Prioridade) => void
  pedirSugestao: () => void
  avaliar: (util: boolean) => void
  mudarStatus: (status: Status) => void
  editar: () => void
  excluir: () => void
}

export function Selo({ prioridade, rotulo }: { prioridade: Prioridade; rotulo?: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${CORES_PRIORIDADE[prioridade]}`}>
      {rotulo ?? NOMES_PRIORIDADE[prioridade]}
    </span>
  )
}

function Prazo({ prazo, encerrada }: { prazo: string; encerrada: boolean }) {
  const texto = prazoRelativo(prazo)
  const urgente = !encerrada && (texto.startsWith('Venceu') || texto === 'Vence hoje')
  return (
    <span className={urgente ? 'font-medium text-red-700' : ''} title={dataCurta(prazo)}>
      {texto}
    </span>
  )
}

export default function CartaoTarefa({ tarefa, acoes, ocupado }: { tarefa: Tarefa; acoes: AcoesTarefa; ocupado: boolean }) {
  const [explicar, setExplicar] = useState(false)
  const { sugestao } = tarefa
  const encerrada = tarefa.status === 'concluida' || tarefa.status === 'cancelada'
  const pendente = sugestao !== null && tarefa.prioridade_confirmada === null && !encerrada
  const confianca = sugestao?.probabilidades?.[sugestao.prioridade_sugerida]

  return (
    <article className={`rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200 ${encerrada ? 'opacity-70' : ''}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className={`font-medium break-words ${tarefa.status === 'concluida' ? 'text-slate-500 line-through' : ''}`}>
            {tarefa.titulo}
          </h3>
          <p className="mt-0.5 flex flex-wrap gap-x-2 text-xs text-slate-500">
            <span>{NOMES_CATEGORIA[tarefa.categoria]}</span>
            <span aria-hidden>·</span>
            {tarefa.prazo ? <Prazo prazo={tarefa.prazo} encerrada={encerrada} /> : <span>Sem prazo</span>}
            <span aria-hidden>·</span>
            <span>{String(tarefa.esforco_estimado).replace('.', ',')} h</span>
            {tarefa.status !== 'aberta' && (
              <>
                <span aria-hidden>·</span>
                <span>{NOMES_STATUS[tarefa.status]}</span>
              </>
            )}
          </p>
        </div>
        {tarefa.prioridade_confirmada && <Selo prioridade={tarefa.prioridade_confirmada} />}
      </div>

      {tarefa.descricao && <p className="mt-2 text-sm text-slate-600 break-words">{tarefa.descricao}</p>}

      {pendente && sugestao && (
        <div className="mt-3 rounded-lg bg-indigo-50 p-3 ring-1 ring-indigo-100">
          <p className="text-sm text-slate-700">
            O modelo sugere <Selo prioridade={sugestao.prioridade_sugerida} />
            {confianca !== undefined && <span className="ml-1 text-xs text-slate-500">({Math.round(confianca * 100)}% de confiança)</span>}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Botao disabled={ocupado} onClick={() => acoes.confirmar(sugestao.prioridade_sugerida)}>
              Aceitar
            </Botao>
            <span className="text-xs text-slate-500">ou ajustar para</span>
            {PRIORIDADES.filter((p) => p !== sugestao.prioridade_sugerida).map((p) => (
              <Botao key={p} variante="secundario" disabled={ocupado} onClick={() => acoes.confirmar(p)}>
                {NOMES_PRIORIDADE[p]}
              </Botao>
            ))}
          </div>
        </div>
      )}

      {sugestao === null && !encerrada && (
        <div className="mt-3 flex items-center gap-2 text-sm text-slate-500">
          Sem sugestão do modelo.
          <Botao variante="secundario" disabled={ocupado} onClick={acoes.pedirSugestao}>
            Pedir sugestão
          </Botao>
        </div>
      )}

      {sugestao && (
        <div className="mt-3 text-sm">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-slate-500">
            {!pendente && (
              <span>
                Sugestão do modelo: {NOMES_PRIORIDADE[sugestao.prioridade_sugerida]}
                {sugestao.aceita === false && ' (você ajustou)'}
              </span>
            )}
            {sugestao.fatores && (
              <button
                type="button"
                className="font-medium text-indigo-600 hover:underline"
                aria-expanded={explicar}
                onClick={() => setExplicar(!explicar)}
              >
                {explicar ? 'Ocultar motivos' : 'Por que essa prioridade?'}
              </button>
            )}
          </div>
          {explicar && sugestao.fatores && (
            <div className="mt-2 rounded-lg bg-slate-50 p-3">
              <Fatores fatores={sugestao.fatores} prioridade={sugestao.prioridade_sugerida} />
            </div>
          )}
          {tarefa.prioridade_confirmada && sugestao.util === null && (
            <div className="mt-2 flex items-center gap-2 text-slate-500">
              A sugestão ajudou?
              <Botao variante="discreto" className="px-2 py-1" disabled={ocupado} onClick={() => acoes.avaliar(true)}>
                Sim
              </Botao>
              <Botao variante="discreto" className="px-2 py-1" disabled={ocupado} onClick={() => acoes.avaliar(false)}>
                Não
              </Botao>
            </div>
          )}
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3">
        {tarefa.status === 'aberta' && (
          <Botao variante="secundario" disabled={ocupado} onClick={() => acoes.mudarStatus('em_andamento')}>
            Iniciar
          </Botao>
        )}
        {!encerrada && (
          <Botao variante="secundario" disabled={ocupado} onClick={() => acoes.mudarStatus('concluida')}>
            Concluir
          </Botao>
        )}
        {encerrada && (
          <Botao variante="secundario" disabled={ocupado} onClick={() => acoes.mudarStatus('aberta')}>
            Reabrir
          </Botao>
        )}
        <Botao variante="discreto" disabled={ocupado} onClick={acoes.editar}>
          Editar
        </Botao>
        <Botao variante="discreto" className="ml-auto text-red-700 hover:bg-red-50" disabled={ocupado} onClick={acoes.excluir}>
          Excluir
        </Botao>
      </div>
    </article>
  )
}
