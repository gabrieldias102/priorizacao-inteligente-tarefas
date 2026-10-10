import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, lerToken, quandoSessaoExpirar, salvarToken } from './api'
import { ContextoSessao, type Sessao } from './sessao'
import type { Token, Usuario } from './tipos'

export function ProvedorSessao({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [carregando, setCarregando] = useState(() => lerToken() !== null)

  const sair = useCallback(() => {
    salvarToken(null)
    setUsuario(null)
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    quandoSessaoExpirar(sair)
    if (!lerToken()) return
    api
      .eu()
      .then(setUsuario)
      .catch(() => sair())
      .finally(() => setCarregando(false))
  }, [sair])

  const iniciar = useCallback((token: Token) => {
    salvarToken(token.access_token)
    setUsuario(token.usuario)
  }, [])

  const sessao = useMemo<Sessao>(
    () => ({
      usuario,
      carregando,
      entrar: async (email, senha) => iniciar(await api.entrar(email, senha)),
      registrar: async (nome, email, senha) => iniciar(await api.registrar(nome, email, senha)),
      sair,
    }),
    [usuario, carregando, iniciar, sair],
  )

  return <ContextoSessao.Provider value={sessao}>{children}</ContextoSessao.Provider>
}
