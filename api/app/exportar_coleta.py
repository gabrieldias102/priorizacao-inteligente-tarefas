"""Exporta os registros da coleta de dados (seção 4.9.4) e apaga as contas de teste.

O pesquisador monta um CSV ligando o e-mail de cada conta ao código do participante:

    email,participante
    pessoa1@exemplo.com,P01

e roda, a partir de api/ (com DATABASE_URL apontando para o banco publicado):

    python -m app.exportar_coleta participantes.csv --saida ../coleta

O resultado é coleta/registros.csv, uma linha por tarefa, sem nome nem e-mail.
Depois de conferir a exportação, as contas podem ser apagadas, como promete o termo
de consentimento:

    python -m app.exportar_coleta participantes.csv --apagar-contas
"""

import argparse
import csv
from pathlib import Path

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.modelos import Sugestao, Tarefa, Usuario

COLUNAS = [
    "participante",
    "tarefa",
    "titulo",
    "categoria",
    "dias_ate_prazo",
    "impacto",
    "complexidade",
    "esforco_estimado",
    "prioridade_sugerida",
    "confianca",
    "prioridade_confirmada",
    "aceita",
    "util",
    "sugestoes",
    "status",
    "modelo_versao",
    "criado_em",
]


def ler_participantes(caminho: Path) -> dict[str, str]:
    with caminho.open(newline="", encoding="utf-8") as arquivo:
        return {
            linha["email"].strip().lower(): linha["participante"].strip()
            for linha in csv.DictReader(arquivo)
        }


def sugestao_da_sessao(tarefa: Tarefa) -> Sugestao | None:
    """A primeira sugestão que o participante confirmou; se nenhuma, a primeira feita.

    Na sessão, a tarefa é confirmada logo depois de criada. Editar um atributo depois
    gera nova sugestão, mas a que interessa para medir a concordância é a da criação.
    """
    if not tarefa.sugestoes:
        return None
    confirmadas = [s for s in tarefa.sugestoes if s.aceita is not None]
    return confirmadas[0] if confirmadas else tarefa.sugestoes[0]


def prioridade_confirmada(tarefa: Tarefa, sugestao: Sugestao | None) -> str | None:
    if sugestao is None:
        return tarefa.prioridade_confirmada
    if sugestao.aceita:
        return sugestao.prioridade_sugerida
    if sugestao is tarefa.sugestoes[-1]:
        return tarefa.prioridade_confirmada
    # Ajustada e depois editada: a classe escolhida na hora não ficou guardada.
    return None


def linhas_da_coleta(sessao: Session, participantes: dict[str, str]) -> list[dict]:
    usuarios = sessao.scalars(
        select(Usuario)
        .where(Usuario.email.in_(participantes))
        .options(selectinload(Usuario.tarefas).selectinload(Tarefa.sugestoes))
    )
    linhas = []
    for usuario in usuarios:
        codigo = participantes[usuario.email.lower()]
        tarefas = sorted(usuario.tarefas, key=lambda t: t.criado_em)
        for numero, tarefa in enumerate(tarefas, start=1):
            sugestao = sugestao_da_sessao(tarefa)
            atributos = sugestao.atributos if sugestao else {}
            probabilidades = (sugestao.probabilidades or {}) if sugestao else {}
            linhas.append(
                {
                    "participante": codigo,
                    "tarefa": numero,
                    "titulo": tarefa.titulo,
                    "categoria": tarefa.categoria,
                    "dias_ate_prazo": atributos.get("dias_ate_prazo", ""),
                    "impacto": atributos.get("impacto", tarefa.impacto),
                    "complexidade": atributos.get("complexidade", tarefa.complexidade),
                    "esforco_estimado": atributos.get("esforco_estimado", tarefa.esforco_estimado),
                    "prioridade_sugerida": sugestao.prioridade_sugerida if sugestao else "",
                    "confianca": (
                        round(probabilidades.get(sugestao.prioridade_sugerida, 0), 4)
                        if sugestao
                        else ""
                    ),
                    "prioridade_confirmada": prioridade_confirmada(tarefa, sugestao) or "",
                    "aceita": ""
                    if sugestao is None or sugestao.aceita is None
                    else sugestao.aceita,
                    "util": "" if sugestao is None or sugestao.util is None else sugestao.util,
                    "sugestoes": len(tarefa.sugestoes),
                    "status": tarefa.status,
                    "modelo_versao": sugestao.modelo_versao if sugestao else "",
                    "criado_em": tarefa.criado_em.isoformat(),
                }
            )
    return sorted(linhas, key=lambda linha: (linha["participante"], linha["tarefa"]))


def exportar(sessao: Session, participantes: dict[str, str], saida: Path) -> list[dict]:
    linhas = linhas_da_coleta(sessao, participantes)
    saida.mkdir(parents=True, exist_ok=True)
    with (saida / "registros.csv").open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(linhas)
    return linhas


def apagar_contas(sessao: Session, participantes: dict[str, str]) -> int:
    """Apaga as contas (e, em cascata, tarefas e sugestões) dos participantes."""
    ids = list(sessao.scalars(select(Usuario.id).where(Usuario.email.in_(participantes))))
    if ids:
        tarefas = select(Tarefa.id).where(Tarefa.usuario_id.in_(ids))
        sessao.execute(delete(Sugestao).where(Sugestao.tarefa_id.in_(tarefas)))
        sessao.execute(delete(Tarefa).where(Tarefa.usuario_id.in_(ids)))
        sessao.execute(delete(Usuario).where(Usuario.id.in_(ids)))
        sessao.commit()
    return len(ids)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("participantes", type=Path, help="CSV com as colunas email,participante")
    parser.add_argument("--saida", type=Path, default=Path("coleta"))
    parser.add_argument("--banco", default=settings.database_url, help="URL do banco")
    parser.add_argument(
        "--apagar-contas", action="store_true", help="apaga as contas em vez de exportar"
    )
    args = parser.parse_args()

    participantes = ler_participantes(args.participantes)
    with Session(create_engine(args.banco)) as sessao:
        if args.apagar_contas:
            print(f"{apagar_contas(sessao, participantes)} conta(s) apagada(s).")
            return
        linhas = exportar(sessao, participantes, args.saida)
    faltando = sorted(set(participantes.values()) - {linha["participante"] for linha in linhas})
    print(f"{len(linhas)} tarefa(s) exportada(s) em {args.saida / 'registros.csv'}.")
    if faltando:
        print(f"Sem conta ou sem tarefas no banco: {', '.join(faltando)}")


if __name__ == "__main__":
    main()
