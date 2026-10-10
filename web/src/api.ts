export type Health = { status: string; servico: string; ml?: string }

export async function getHealth(): Promise<Health> {
  const resposta = await fetch('/api/health')
  if (!resposta.ok) throw new Error(`API respondeu ${resposta.status}`)
  return resposta.json()
}
