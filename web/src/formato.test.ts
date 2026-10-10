import { describe, expect, it } from 'vitest'
import { isoParaLocal, localParaIso, prazoRelativo } from './formato'

describe('prazoRelativo', () => {
  const agora = new Date(2026, 9, 10, 15, 0)
  it.each([
    [new Date(2026, 9, 10, 23, 0), 'Vence hoje'],
    [new Date(2026, 9, 11, 8, 0), 'Vence amanhã'],
    [new Date(2026, 9, 15, 8, 0), 'Vence em 5 dias'],
    [new Date(2026, 9, 9, 8, 0), 'Venceu ontem'],
    [new Date(2026, 9, 7, 8, 0), 'Venceu há 3 dias'],
  ])('%s → %s', (prazo, esperado) => {
    expect(prazoRelativo(prazo.toISOString(), agora)).toBe(esperado)
  })
})

it('converte datetime-local em ISO e volta', () => {
  expect(localParaIso('')).toBeNull()
  expect(isoParaLocal(localParaIso('2026-10-12T09:30'))).toBe('2026-10-12T09:30')
})
