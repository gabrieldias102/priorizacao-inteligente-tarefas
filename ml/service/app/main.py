from typing import Annotated, Literal

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from app.modelo import Modelo, modelo_ativo

app = FastAPI(title="Priorização Inteligente de Tarefas · Serviço de ML")

ModeloAtivo = Annotated[Modelo, Depends(modelo_ativo)]


class Atributos(BaseModel):
    dias_ate_prazo: int = Field(ge=0, le=3650)
    impacto: int = Field(ge=1, le=5)
    complexidade: int = Field(ge=1, le=5)
    esforco_estimado: float = Field(gt=0, le=200)
    categoria: Literal["estudo", "trabalho", "pessoal", "saude", "casa"]


class Fator(BaseModel):
    atributo: str
    valor: float | str
    descricao: str
    peso: float = Field(description="Quanto o atributo aumenta (+) ou reduz (-) a classe prevista")


class Previsao(BaseModel):
    prioridade: Literal["baixa", "media", "alta"]
    probabilidades: dict[str, float]
    fatores: list[Fator]
    modelo_versao: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "servico": "ml"}


@app.get("/modelo")
def modelo(ativo: ModeloAtivo) -> dict:
    m = ativo.metadados
    return {
        "versao": m["versao"],
        "algoritmo": m["algoritmo"],
        "treinado_em": m["treinado_em"],
        "metricas_teste": m["metricas_teste"],
    }


@app.post("/prever")
def prever(atributos: Atributos, ativo: ModeloAtivo) -> Previsao:
    return Previsao(**ativo.prever(atributos.model_dump()))
