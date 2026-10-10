import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="Priorização Inteligente de Tarefas · API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def status_ml() -> str:
    try:
        async with httpx.AsyncClient(base_url=settings.ml_url, timeout=2) as cliente:
            resposta = await cliente.get("/health")
        return "ok" if resposta.status_code == 200 else "erro"
    except httpx.HTTPError:
        return "indisponível"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "servico": "api", "ml": await status_ml()}
