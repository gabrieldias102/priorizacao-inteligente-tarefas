import { NOMES_PRIORIDADE } from '../formato'
import type { Fator, Prioridade } from '../tipos'

/** Os fatores que mais pesaram na sugestão (valores de Shapley vindos do modelo). */
export default function Fatores({ fatores, prioridade }: { fatores: Fator[]; prioridade: Prioridade }) {
  const principais = fatores.filter((f) => Math.abs(f.peso) >= 0.01).slice(0, 3)
  if (principais.length === 0) {
    return <p className="text-sm text-slate-500">Nenhum atributo se destacou nesta sugestão.</p>
  }
  const maior = Math.max(...principais.map((f) => Math.abs(f.peso)))
  return (
    <ul className="flex flex-col gap-2" aria-label="Fatores da sugestão">
      {principais.map((f) => {
        const aFavor = f.peso > 0
        return (
          <li key={f.atributo} className="text-sm">
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-medium text-slate-800">{f.descricao}</span>
              <span className={aFavor ? 'text-indigo-700' : 'text-slate-500'}>
                {aFavor ? 'a favor de' : 'contra'} {NOMES_PRIORIDADE[prioridade]}
              </span>
            </div>
            <div className="mt-1 h-1.5 rounded-full bg-slate-100">
              <div
                className={`h-1.5 rounded-full ${aFavor ? 'bg-indigo-500' : 'bg-slate-400'}`}
                style={{ width: `${Math.max(6, (Math.abs(f.peso) / maior) * 100)}%` }}
              />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
