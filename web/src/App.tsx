import { useEffect, useState } from 'react'
import { getHealth, type Health } from './api'

type Estado = { tipo: 'carregando' } | { tipo: 'ok'; health: Health } | { tipo: 'erro'; mensagem: string }

export default function App() {
  const [estado, setEstado] = useState<Estado>({ tipo: 'carregando' })

  useEffect(() => {
    getHealth()
      .then((health) => setEstado({ tipo: 'ok', health }))
      .catch((erro: Error) => setEstado({ tipo: 'erro', mensagem: erro.message }))
  }, [])

  return (
    <main>
      <h1>Priorização Inteligente de Tarefas</h1>
      {estado.tipo === 'carregando' && <p>Verificando a API...</p>}
      {estado.tipo === 'ok' && (
        <p>
          API: {estado.health.status} · Serviço de ML: {estado.health.ml ?? 'desconhecido'}
        </p>
      )}
      {estado.tipo === 'erro' && <p role="alert">API indisponível: {estado.mensagem}</p>}
    </main>
  )
}
