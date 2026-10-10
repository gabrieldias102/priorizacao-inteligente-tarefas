from fastapi import FastAPI

app = FastAPI(title="Priorização Inteligente de Tarefas · Serviço de ML")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "servico": "ml"}


@app.get("/modelo")
def modelo() -> dict[str, str | None]:
    # O modelo treinado chega na fase 1; até lá não há versão ativa.
    return {"versao": None, "algoritmo": None}
