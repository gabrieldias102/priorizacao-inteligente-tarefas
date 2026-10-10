import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { tarefaExemplo } from '../testes/apiFalsa'
import type { Tarefa } from '../tipos'
import CartaoTarefa, { type AcoesTarefa } from './CartaoTarefa'

function renderizar(tarefa: Tarefa) {
  const acoes: AcoesTarefa = {
    confirmar: vi.fn(),
    pedirSugestao: vi.fn(),
    avaliar: vi.fn(),
    mudarStatus: vi.fn(),
    editar: vi.fn(),
    excluir: vi.fn(),
  }
  render(<CartaoTarefa tarefa={tarefa} acoes={acoes} ocupado={false} />)
  return acoes
}

describe('CartaoTarefa', () => {
  it('mostra a sugestão pendente com a confiança e aceita', async () => {
    const acoes = renderizar(tarefaExemplo())
    expect(screen.getByText(/O modelo sugere/)).toBeInTheDocument()
    expect(screen.getByText('(82% de confiança)')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Aceitar' }))
    expect(acoes.confirmar).toHaveBeenCalledWith('alta')
  })

  it('permite ajustar para outra prioridade', async () => {
    const acoes = renderizar(tarefaExemplo())
    expect(screen.queryByRole('button', { name: 'Alta' })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Baixa' }))
    expect(acoes.confirmar).toHaveBeenCalledWith('baixa')
  })

  it('explica a sugestão com os fatores que mais pesaram', async () => {
    renderizar(tarefaExemplo())
    expect(screen.queryByRole('list', { name: 'Fatores da sugestão' })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Por que essa prioridade?' }))
    const itens = screen.getAllByRole('listitem')
    expect(itens).toHaveLength(3)
    expect(itens[0]).toHaveTextContent('Prazo em 1 dia')
    expect(itens[0]).toHaveTextContent('a favor de Alta')
    expect(itens[2]).toHaveTextContent('contra Alta')
  })

  it('depois de confirmada pede a avaliação da sugestão', async () => {
    const base = tarefaExemplo()
    const acoes = renderizar({
      ...base,
      prioridade_confirmada: 'media',
      sugestao: { ...base.sugestao!, aceita: false },
    })
    expect(screen.getByText('Média')).toBeInTheDocument()
    expect(screen.getByText(/você ajustou/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Não' }))
    expect(acoes.avaliar).toHaveBeenCalledWith(false)
  })

  it('sem sugestão oferece pedir uma nova', async () => {
    const acoes = renderizar(tarefaExemplo({ sugestao: null, prioridade_sugerida: null }))
    await userEvent.click(screen.getByRole('button', { name: 'Pedir sugestão' }))
    expect(acoes.pedirSugestao).toHaveBeenCalled()
  })
})

it('tarefa concluída sem prioridade confirmada não pede confirmação', () => {
  renderizar(tarefaExemplo({ status: 'concluida' }))
  expect(screen.queryByRole('button', { name: 'Aceitar' })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Reabrir' })).toBeInTheDocument()
})
