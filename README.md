# Priorização Inteligente de Tarefas

Aplicação web do TCC "Priorização Inteligente de Tarefas: Aplicação de Aprendizado de Máquina em Listas de Afazeres" (Análise e Desenvolvimento de Sistemas, Unisinos). Um modelo de classificação sugere a prioridade (baixa, média ou alta) de cada tarefa, e o usuário aceita ou ajusta a sugestão.

## Estrutura

| Pasta | Conteúdo |
| --- | --- |
| `web/` | Interface em React + Vite + TypeScript |
| `api/` | API de aplicação em FastAPI (regras, login, tarefas) |
| `ml/service/` | Serviço de previsão em FastAPI + scikit-learn |
| `ml/training/` | Gerador da base mockada, treino e avaliação |
| `ml/notebooks/` | Experimentos usados no texto do TCC |
| `ml/models/` | Modelos treinados e versionados |
| `docs/` | Diagramas, questionário e resultados |

## Como rodar

Com Docker:

```bash
docker compose up --build
```

- Interface: http://localhost:5173
- API: http://localhost:8000 (documentação em `/docs`)
- Serviço de ML: http://localhost:8001

Sem Docker, cada parte separadamente:

```bash
# Serviço de ML
cd ml/service && pip install -r requirements-dev.txt && uvicorn app.main:app --port 8001

# API
cd api && pip install -r requirements-dev.txt && uvicorn app.main:app --port 8000

# Interface
cd web && npm install && npm run dev
```

## Testes e lint

```bash
cd web && npm run lint && npm test
cd api && ruff check . && pytest
cd ml/service && ruff check . && pytest
cd ml/training && ruff check . && pytest
```

## Modelo de priorização

A base mockada e o treino ficam em `ml/training`. Para gerar a base, treinar os três algoritmos e salvar o melhor modelo:

```bash
cd ml/training && pip install -r requirements-dev.txt && python -m treino.treinar
```

O resultado vai para `ml/models/` (modelo e metadados) e `docs/resultados/fase-1/` (métricas e matrizes de confusão). A análise completa está em `ml/notebooks/01_comparacao_modelos.ipynb`.
