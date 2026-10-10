import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

PRIORIDADES = ("baixa", "media", "alta")
STATUS = ("aberta", "em_andamento", "concluida", "cancelada")
CATEGORIAS = ("estudo", "trabalho", "pessoal", "saude", "casa")


def agora() -> datetime:
    return datetime.now(UTC)


def enum(nome: str, valores: tuple[str, ...]) -> Enum:
    # native_enum=False guarda como texto com CHECK, igual no PostgreSQL e no SQLite.
    return Enum(*valores, name=nome, native_enum=False, create_constraint=True)


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    tarefas: Mapped[list["Tarefa"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class Tarefa(Base):
    __tablename__ = "tarefa"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    titulo: Mapped[str] = mapped_column(String(200))
    descricao: Mapped[str | None] = mapped_column(Text)
    prazo: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    categoria: Mapped[str] = mapped_column(enum("categoria", CATEGORIAS))
    impacto: Mapped[int] = mapped_column(Integer)
    complexidade: Mapped[int] = mapped_column(Integer)
    esforco_estimado: Mapped[float] = mapped_column(Float)
    prioridade_sugerida: Mapped[str | None] = mapped_column(
        enum("prioridade_sugerida", PRIORIDADES)
    )
    prioridade_confirmada: Mapped[str | None] = mapped_column(
        enum("prioridade_confirmada", PRIORIDADES)
    )
    status: Mapped[str] = mapped_column(enum("status", STATUS), default="aberta")
    modelo_versao: Mapped[str | None] = mapped_column(String(40))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora, onupdate=agora
    )
    concluida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    usuario: Mapped[Usuario] = relationship(back_populates="tarefas")
    sugestoes: Mapped[list["Sugestao"]] = relationship(
        back_populates="tarefa", cascade="all, delete-orphan", order_by="Sugestao.criado_em"
    )


class Sugestao(Base):
    """Cada previsão do modelo, com os atributos do momento em que foi feita."""

    __tablename__ = "sugestao"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tarefa_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tarefa.id", ondelete="CASCADE"), index=True
    )
    atributos: Mapped[dict] = mapped_column(JSON)
    prioridade_sugerida: Mapped[str] = mapped_column(enum("sugestao_prioridade", PRIORIDADES))
    probabilidades: Mapped[dict | None] = mapped_column(JSON)
    modelo_versao: Mapped[str] = mapped_column(String(40))
    aceita: Mapped[bool | None] = mapped_column(Boolean)
    util: Mapped[bool | None] = mapped_column(Boolean)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    tarefa: Mapped[Tarefa] = relationship(back_populates="sugestoes")
