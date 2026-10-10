import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

afterEach(() => vi.restoreAllMocks())

describe('App', () => {
  it('mostra o estado da API e do serviço de ML', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok', servico: 'api', ml: 'ok' })),
    )
    render(<App />)
    expect(await screen.findByText(/API: ok · Serviço de ML: ok/)).toBeInTheDocument()
  })

  it('avisa quando a API está fora do ar', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('', { status: 503 }))
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('API respondeu 503')
  })
})
