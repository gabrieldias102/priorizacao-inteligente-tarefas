import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import { salvarToken } from './api'
import { apiFalsa, tarefaExemplo } from './testes/apiFalsa'
import { renderizarApp } from './testes/renderizar'
import type { Tarefa } from './tipos'

const usuario = { id: 'u1', nome: 'Ana', email: 'ana@exemplo.com' }
const estatisticas = {
  total: 1,
  por_status: { aberta: 1, em_andamento: 0, concluida: 0, cancelada: 0 },
  por_prioridade: { alta: 0, media: 0, baixa: 0 },
  sugestoes: 1,
  sugestoes_aceitas: 0,
  sugestoes_ajustadas: 0,
  taxa_aceitacao: null,
}

afterEach(() => salvarToken(null))

describe('App', () => {
  it('sem sessão manda para o login, entra e lista as tarefas', async () => {
    const chamadas = apiFalsa([
      { metodo: 'POST', caminho: /^\/auth\/entrar$/, responder: () => ({ json: { access_token: 'tk', token_type: 'bearer', usuario } }) },
      { metodo: 'GET', caminho: /^\/tarefas$/, responder: () => ({ json: [tarefaExemplo()] }) },
      { metodo: 'GET', caminho: /^\/estatisticas$/, responder: () => ({ json: estatisticas }) },
    ])
    renderizarApp('/')
    await userEvent.type(await screen.findByLabelText('E-mail'), 'ana@exemplo.com')
    await userEvent.type(screen.getByLabelText('Senha'), 'segredo123')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('Entregar relatório')).toBeInTheDocument()
    expect(screen.getByText('Olá, Ana')).toBeInTheDocument()
    expect(chamadas[0].corpo).toEqual({ username: 'ana@exemplo.com', password: 'segredo123' })
  })

  it('mostra o erro da API quando o login falha', async () => {
    apiFalsa([
      { metodo: 'POST', caminho: /^\/auth\/entrar$/, responder: () => ({ status: 401, json: { detail: 'E-mail ou senha incorretos' } }) },
    ])
    renderizarApp('/entrar')
    await userEvent.type(screen.getByLabelText('E-mail'), 'ana@exemplo.com')
    await userEvent.type(screen.getByLabelText('Senha'), 'errada123')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha incorretos')
  })

  it('cria uma tarefa e mostra a sugestão do modelo', async () => {
    salvarToken('tk')
    let tarefas: Tarefa[] = []
    const chamadas = apiFalsa([
      { metodo: 'GET', caminho: /^\/auth\/eu$/, responder: () => ({ json: usuario }) },
      { metodo: 'GET', caminho: /^\/tarefas/, responder: () => ({ json: tarefas }) },
      { metodo: 'GET', caminho: /^\/estatisticas$/, responder: () => ({ json: estatisticas }) },
      {
        metodo: 'POST',
        caminho: /^\/tarefas$/,
        responder: (corpo) => {
          tarefas = [tarefaExemplo(corpo as Partial<Tarefa>)]
          return { status: 201, json: tarefas[0] }
        },
      },
    ])
    renderizarApp('/')
    expect(await screen.findByText(/Nenhuma tarefa ainda/)).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: '+ Nova tarefa' }))
    await userEvent.type(screen.getByLabelText('Título'), 'Estudar para a prova')
    await userEvent.selectOptions(screen.getByLabelText('Categoria'), 'estudo')
    await userEvent.click(within(screen.getByRole('radiogroup', { name: 'Impacto' })).getByRole('radio', { name: '5' }))
    await userEvent.click(screen.getByRole('button', { name: 'Adicionar e sugerir prioridade' }))

    expect(await screen.findByText('Estudar para a prova')).toBeInTheDocument()
    expect(screen.getByText(/O modelo sugere/)).toBeInTheDocument()
    const criacao = chamadas.find((c) => c.metodo === 'POST')
    expect(criacao?.corpo).toMatchObject({ titulo: 'Estudar para a prova', categoria: 'estudo', impacto: 5, prazo: null })
  })

  it('filtra pela prioridade', async () => {
    salvarToken('tk')
    const chamadas = apiFalsa([
      { metodo: 'GET', caminho: /^\/auth\/eu$/, responder: () => ({ json: usuario }) },
      { metodo: 'GET', caminho: /^\/tarefas/, responder: () => ({ json: [] }) },
      { metodo: 'GET', caminho: /^\/estatisticas$/, responder: () => ({ json: estatisticas }) },
    ])
    renderizarApp('/')
    await userEvent.selectOptions(await screen.findByLabelText('Filtrar por prioridade'), 'alta')
    expect(await screen.findByText('Nenhuma tarefa com esses filtros.')).toBeInTheDocument()
    expect(chamadas.some((c) => c.caminho === '/tarefas?prioridade=alta')).toBe(true)
  })
})
