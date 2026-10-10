import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Prioridade = Literal["baixa", "media", "alta"]
Status = Literal["aberta", "em_andamento", "concluida", "cancelada"]
Categoria = Literal["estudo", "trabalho", "pessoal", "saude", "casa"]
Nivel = int  # 1 a 5, validado com Field nos esquemas


class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    usuario: UsuarioSaida


class TarefaCriar(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    descricao: str | None = Field(default=None, max_length=5000)
    prazo: datetime | None = None
    categoria: Categoria
    impacto: Nivel = Field(ge=1, le=5)
    complexidade: Nivel = Field(ge=1, le=5)
    esforco_estimado: float = Field(gt=0, le=200, description="Horas previstas")


class TarefaAtualizar(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    descricao: str | None = Field(default=None, max_length=5000)
    prazo: datetime | None = None
    categoria: Categoria | None = None
    impacto: Nivel | None = Field(default=None, ge=1, le=5)
    complexidade: Nivel | None = Field(default=None, ge=1, le=5)
    esforco_estimado: float | None = Field(default=None, gt=0, le=200)
    status: Status | None = None


class Fator(BaseModel):
    atributo: str
    valor: float | str
    descricao: str
    peso: float


class SugestaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prioridade_sugerida: Prioridade
    probabilidades: dict[str, float] | None
    fatores: list[Fator] | None
    modelo_versao: str
    aceita: bool | None
    util: bool | None
    criado_em: datetime


class TarefaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    titulo: str
    descricao: str | None
    prazo: datetime | None
    categoria: Categoria
    impacto: int
    complexidade: int
    esforco_estimado: float
    prioridade_sugerida: Prioridade | None
    prioridade_confirmada: Prioridade | None
    status: Status
    modelo_versao: str | None
    criado_em: datetime
    atualizado_em: datetime
    concluida_em: datetime | None
    sugestao: SugestaoSaida | None


class PrioridadeConfirmar(BaseModel):
    prioridade: Prioridade


class AvaliacaoSugestao(BaseModel):
    util: bool


class Estatisticas(BaseModel):
    total: int
    por_status: dict[str, int]
    por_prioridade: dict[str, int]
    sugestoes: int
    sugestoes_aceitas: int
    sugestoes_ajustadas: int
    taxa_aceitacao: float | None
