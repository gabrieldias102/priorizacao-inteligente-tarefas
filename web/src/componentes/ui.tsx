import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'

const BOTOES = {
  primario: 'bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300',
  secundario: 'bg-white text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50',
  perigo: 'bg-white text-red-700 ring-1 ring-red-200 hover:bg-red-50',
  discreto: 'text-slate-600 hover:bg-slate-100',
}

export function Botao({
  variante = 'primario',
  className = '',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variante?: keyof typeof BOTOES }) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition disabled:cursor-not-allowed ${BOTOES[variante]} ${className}`}
      {...props}
    />
  )
}

export function Campo({ rotulo, children, ajuda }: { rotulo: string; children: ReactNode; ajuda?: string }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-slate-700">{rotulo}</span>
      {children}
      {ajuda && <span className="text-xs text-slate-500">{ajuda}</span>}
    </label>
  )
}

const ENTRADA =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200'

export function Entrada(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={ENTRADA} {...props} />
}

export function Selecao(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={ENTRADA} {...props} />
}

export function Alerta({ children }: { children: ReactNode }) {
  return (
    <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">
      {children}
    </p>
  )
}
