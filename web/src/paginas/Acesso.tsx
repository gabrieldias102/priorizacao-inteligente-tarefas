import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { Alerta, Botao, Campo, Entrada } from '../componentes/ui'
import { useSessao } from '../sessao'

export default function Acesso({ modo }: { modo: 'entrar' | 'cadastro' }) {
  const { usuario, entrar, registrar } = useSessao()
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  if (usuario) return <Navigate to="/" replace />

  const cadastro = modo === 'cadastro'

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      if (cadastro) await registrar(nome, email, senha)
      else await entrar(email, senha)
    } catch (e) {
      setErro((e as Error).message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4 py-12">
      <h1 className="text-2xl font-semibold">Priorização Inteligente de Tarefas</h1>
      <p className="mt-1 text-sm text-slate-600">
        {cadastro ? 'Crie sua conta para começar.' : 'Entre para ver suas tarefas.'}
      </p>
      <form onSubmit={enviar} className="mt-6 flex flex-col gap-4 rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        {cadastro && (
          <Campo rotulo="Nome">
            <Entrada value={nome} onChange={(e) => setNome(e.target.value)} required autoComplete="name" />
          </Campo>
        )}
        <Campo rotulo="E-mail">
          <Entrada type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        </Campo>
        <Campo rotulo="Senha" ajuda={cadastro ? 'Pelo menos 8 caracteres.' : undefined}>
          <Entrada
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            minLength={cadastro ? 8 : undefined}
            autoComplete={cadastro ? 'new-password' : 'current-password'}
          />
        </Campo>
        {erro && <Alerta>{erro}</Alerta>}
        <Botao type="submit" disabled={enviando}>
          {cadastro ? 'Criar conta' : 'Entrar'}
        </Botao>
      </form>
      <p className="mt-4 text-center text-sm text-slate-600">
        {cadastro ? (
          <>
            Já tem conta? <Link className="font-medium text-indigo-600" to="/entrar">Entrar</Link>
          </>
        ) : (
          <>
            Ainda não tem conta? <Link className="font-medium text-indigo-600" to="/cadastro">Criar conta</Link>
          </>
        )}
      </p>
    </main>
  )
}
