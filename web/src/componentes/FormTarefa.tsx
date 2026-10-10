import { useState, type FormEvent } from 'react'
import { isoParaLocal, localParaIso, NOMES_CATEGORIA } from '../formato'
import type { Categoria, DadosTarefa, Tarefa } from '../tipos'
import { Alerta, Botao, Campo, Entrada, Selecao } from './ui'

function Nivel({
  valor,
  aoMudar,
  rotulo,
  baixo,
  alto,
}: {
  valor: number
  aoMudar: (n: number) => void
  rotulo: string
  baixo: string
  alto: string
}) {
  return (
    <fieldset className="flex flex-col gap-1 text-sm">
      <legend className="mb-1 font-medium text-slate-700">{rotulo}</legend>
      <div className="flex gap-1" role="radiogroup" aria-label={rotulo}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={valor === n}
            onClick={() => aoMudar(n)}
            className={`h-9 flex-1 rounded-lg text-sm font-medium ring-1 transition ${
              valor === n ? 'bg-indigo-600 text-white ring-indigo-600' : 'bg-white text-slate-700 ring-slate-300 hover:bg-slate-50'
            }`}
          >
            {n}
          </button>
        ))}
      </div>
      <div className="flex justify-between text-xs text-slate-500">
        <span>{baixo}</span>
        <span>{alto}</span>
      </div>
    </fieldset>
  )
}

export default function FormTarefa({
  inicial,
  aoSalvar,
  aoCancelar,
  salvando,
  erro,
}: {
  inicial?: Tarefa
  aoSalvar: (dados: DadosTarefa) => void
  aoCancelar: () => void
  salvando: boolean
  erro?: string | null
}) {
  const [titulo, setTitulo] = useState(inicial?.titulo ?? '')
  const [descricao, setDescricao] = useState(inicial?.descricao ?? '')
  const [prazo, setPrazo] = useState(isoParaLocal(inicial?.prazo ?? null))
  const [categoria, setCategoria] = useState<Categoria>(inicial?.categoria ?? 'trabalho')
  const [impacto, setImpacto] = useState(inicial?.impacto ?? 3)
  const [complexidade, setComplexidade] = useState(inicial?.complexidade ?? 3)
  const [esforco, setEsforco] = useState(String(inicial?.esforco_estimado ?? 1))

  function enviar(evento: FormEvent) {
    evento.preventDefault()
    aoSalvar({
      titulo: titulo.trim(),
      descricao: descricao.trim() || null,
      prazo: localParaIso(prazo),
      categoria,
      impacto,
      complexidade,
      esforco_estimado: Number(esforco),
    })
  }

  return (
    <form onSubmit={enviar} className="flex flex-col gap-4 rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <h2 className="text-base font-semibold">{inicial ? 'Editar tarefa' : 'Nova tarefa'}</h2>
      <Campo rotulo="Título">
        <Entrada value={titulo} onChange={(e) => setTitulo(e.target.value)} required maxLength={200} />
      </Campo>
      <Campo rotulo="Descrição (opcional)">
        <textarea
          value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
          rows={2}
          maxLength={5000}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
        />
      </Campo>
      <div className="grid gap-4 sm:grid-cols-3">
        <Campo rotulo="Prazo" ajuda="Deixe vazio se não houver.">
          <Entrada type="datetime-local" value={prazo} onChange={(e) => setPrazo(e.target.value)} />
        </Campo>
        <Campo rotulo="Categoria">
          <Selecao value={categoria} onChange={(e) => setCategoria(e.target.value as Categoria)}>
            {Object.entries(NOMES_CATEGORIA).map(([valor, nome]) => (
              <option key={valor} value={valor}>
                {nome}
              </option>
            ))}
          </Selecao>
        </Campo>
        <Campo rotulo="Esforço estimado (horas)">
          <Entrada
            type="number"
            min={0.25}
            max={200}
            step={0.25}
            value={esforco}
            onChange={(e) => setEsforco(e.target.value)}
            required
          />
        </Campo>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Nivel rotulo="Impacto" valor={impacto} aoMudar={setImpacto} baixo="Pouco importa" alto="Muito importa" />
        <Nivel rotulo="Complexidade" valor={complexidade} aoMudar={setComplexidade} baixo="Simples" alto="Difícil" />
      </div>
      {erro && <Alerta>{erro}</Alerta>}
      <div className="flex justify-end gap-2">
        <Botao variante="secundario" onClick={aoCancelar}>
          Cancelar
        </Botao>
        <Botao type="submit" disabled={salvando}>
          {salvando ? 'Salvando...' : inicial ? 'Salvar' : 'Adicionar e sugerir prioridade'}
        </Botao>
      </div>
    </form>
  )
}
