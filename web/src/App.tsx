import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Acesso from './paginas/Acesso'
import Tarefas from './paginas/Tarefas'
import { ProvedorSessao } from './ProvedorSessao'
import { useSessao } from './sessao'

function Protegida({ children }: { children: ReactNode }) {
  const { usuario, carregando } = useSessao()
  if (carregando) return <p className="p-8 text-center text-slate-500">Carregando...</p>
  return usuario ? children : <Navigate to="/entrar" replace />
}

/** Rotas da aplicação. O roteador e o QueryClient ficam em main.tsx (e nos testes). */
export default function App() {
  return (
    <ProvedorSessao>
      <Routes>
        <Route path="/entrar" element={<Acesso modo="entrar" />} />
        <Route path="/cadastro" element={<Acesso modo="cadastro" />} />
        <Route
          path="/"
          element={
            <Protegida>
              <Tarefas />
            </Protegida>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ProvedorSessao>
  )
}
