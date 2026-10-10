import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from app.esquemas import (
    AvaliacaoSugestao,
    Categoria,
    Estatisticas,
    Prioridade,
    PrioridadeConfirmar,
    Status,
    TarefaAtualizar,
    TarefaCriar,
    TarefaSaida,
)
from app.modelos import PRIORIDADES, STATUS, Sugestao, Tarefa
from app.seguranca import Db, UsuarioAtual

rotas = APIRouter(tags=["tarefas"])

PESO_PRIORIDADE = {"alta": 0, "media": 1, "baixa": 2, None: 3}


def prioridade_efetiva(tarefa: Tarefa) -> str | None:
    return tarefa.prioridade_confirmada or tarefa.prioridade_sugerida


def chave_ordem(tarefa: Tarefa) -> tuple:
    """Prioridade (alta primeiro), depois prazo mais próximo; sem prazo vai para o fim."""
    prazo = tarefa.prazo or datetime.max.replace(tzinfo=UTC)
    if prazo.tzinfo is None:
        prazo = prazo.replace(tzinfo=UTC)
    return (PESO_PRIORIDADE[prioridade_efetiva(tarefa)], prazo, tarefa.criado_em)


def buscar(db: Db, usuario: UsuarioAtual, tarefa_id: uuid.UUID) -> Tarefa:
    tarefa = db.get(Tarefa, tarefa_id)
    # 404 também para tarefa de outro usuário, para não revelar que ela existe.
    if tarefa is None or tarefa.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarefa não encontrada")
    return tarefa


@rotas.get("/tarefas")
def listar(
    usuario: UsuarioAtual,
    db: Db,
    status_: Annotated[Status | None, Query(alias="status")] = None,
    categoria: Categoria | None = None,
    prioridade: Prioridade | None = None,
) -> list[TarefaSaida]:
    consulta = select(Tarefa).where(Tarefa.usuario_id == usuario.id)
    if status_ is not None:
        consulta = consulta.where(Tarefa.status == status_)
    if categoria is not None:
        consulta = consulta.where(Tarefa.categoria == categoria)
    tarefas = list(db.scalars(consulta))
    if prioridade is not None:
        tarefas = [t for t in tarefas if prioridade_efetiva(t) == prioridade]
    return [TarefaSaida.model_validate(t) for t in sorted(tarefas, key=chave_ordem)]


@rotas.post("/tarefas", status_code=status.HTTP_201_CREATED)
def criar(dados: TarefaCriar, usuario: UsuarioAtual, db: Db) -> TarefaSaida:
    # A sugestão do modelo entra na fase 3; por enquanto a tarefa nasce sem prioridade.
    tarefa = Tarefa(usuario_id=usuario.id, **dados.model_dump())
    db.add(tarefa)
    db.commit()
    return TarefaSaida.model_validate(tarefa)


@rotas.get("/tarefas/{tarefa_id}")
def detalhar(tarefa_id: uuid.UUID, usuario: UsuarioAtual, db: Db) -> TarefaSaida:
    return TarefaSaida.model_validate(buscar(db, usuario, tarefa_id))


@rotas.patch("/tarefas/{tarefa_id}")
def atualizar(
    tarefa_id: uuid.UUID, dados: TarefaAtualizar, usuario: UsuarioAtual, db: Db
) -> TarefaSaida:
    tarefa = buscar(db, usuario, tarefa_id)
    mudancas = dados.model_dump(exclude_unset=True)
    for campo in ("titulo", "categoria", "impacto", "complexidade", "esforco_estimado", "status"):
        if campo in mudancas and mudancas[campo] is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{campo} não pode ser nulo")
    for campo, valor in mudancas.items():
        setattr(tarefa, campo, valor)
    if "status" in mudancas:
        tarefa.concluida_em = datetime.now(UTC) if tarefa.status == "concluida" else None
    db.commit()
    return TarefaSaida.model_validate(tarefa)


@rotas.delete("/tarefas/{tarefa_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(tarefa_id: uuid.UUID, usuario: UsuarioAtual, db: Db) -> Response:
    db.delete(buscar(db, usuario, tarefa_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@rotas.post("/tarefas/{tarefa_id}/prioridade")
def confirmar_prioridade(
    tarefa_id: uuid.UUID, dados: PrioridadeConfirmar, usuario: UsuarioAtual, db: Db
) -> TarefaSaida:
    """Aceita a sugestão (mesma prioridade) ou ajusta para outra."""
    tarefa = buscar(db, usuario, tarefa_id)
    tarefa.prioridade_confirmada = dados.prioridade
    if tarefa.sugestoes:
        ultima = tarefa.sugestoes[-1]
        ultima.aceita = ultima.prioridade_sugerida == dados.prioridade
    db.commit()
    return TarefaSaida.model_validate(tarefa)


@rotas.post("/tarefas/{tarefa_id}/avaliacao", status_code=status.HTTP_204_NO_CONTENT)
def avaliar_sugestao(
    tarefa_id: uuid.UUID, dados: AvaliacaoSugestao, usuario: UsuarioAtual, db: Db
) -> Response:
    tarefa = buscar(db, usuario, tarefa_id)
    if not tarefa.sugestoes:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta tarefa ainda não tem sugestão")
    tarefa.sugestoes[-1].util = dados.util
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@rotas.get("/estatisticas")
def estatisticas(usuario: UsuarioAtual, db: Db) -> Estatisticas:
    tarefas = list(db.scalars(select(Tarefa).where(Tarefa.usuario_id == usuario.id)))
    sugestoes = list(
        db.scalars(select(Sugestao).join(Tarefa).where(Tarefa.usuario_id == usuario.id))
    )
    respondidas = [s for s in sugestoes if s.aceita is not None]
    aceitas = sum(1 for s in respondidas if s.aceita)
    return Estatisticas(
        total=len(tarefas),
        por_status={s: sum(1 for t in tarefas if t.status == s) for s in STATUS},
        por_prioridade={
            p: sum(1 for t in tarefas if prioridade_efetiva(t) == p) for p in PRIORIDADES
        },
        sugestoes=len(sugestoes),
        sugestoes_aceitas=aceitas,
        sugestoes_ajustadas=len(respondidas) - aceitas,
        taxa_aceitacao=round(aceitas / len(respondidas), 4) if respondidas else None,
    )
