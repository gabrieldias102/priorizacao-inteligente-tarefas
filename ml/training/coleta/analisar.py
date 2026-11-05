"""Calcula as medidas da coleta (Quadro 7, SUS e Likert) a partir dos CSVs.

Entrada (uma pasta com quatro arquivos):

- registros.csv: exportado da aplicação por `python -m app.exportar_coleta` (api/);
- ficha.csv: participante, titulo, prioridade (ficha "cega", digitada pelo pesquisador);
- questionario.csv: participante, A1..A4, B1..B10, C1..C10, D1..D4;
- observacao.csv: participante, momento, ocorrencia, tarefa, tema.

A ficha é ligada aos registros pelo título da tarefa, por isso o participante deve
cadastrar na aplicação os mesmos títulos que escreveu na ficha.

Uso (a partir de ml/training):

    python -m coleta.analisar ../../docs/resultados/coleta-simulada/dados \\
        --saida ../../docs/resultados/coleta-simulada
"""

import argparse
import json
import unicodedata
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from treino.gerador import CLASSES, rapidez, urgencia

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

F1_BASE_SIMULADA = 0.856
SUS_MEDIA_REFERENCIA = 68
ORDEM = {c: i for i, c in enumerate(CLASSES)}
ITENS_C = {
    "C1": "Qualidade",
    "C2": "Qualidade",
    "C3": "Compreensão",
    "C4": "Compreensão",
    "C5": "Confiança",
    "C6": "Controle",
    "C7": "Utilidade",
    "C8": "Organização",
    "C9": "Satisfação",
    "C10": "Satisfação",
}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(texto.lower().split())


def booleano(serie: pd.Series) -> pd.Series:
    mapa = {"true": True, "false": False, "1": True, "0": False}
    return serie.map(lambda v: mapa.get(str(v).strip().lower()) if pd.notna(v) else None)


def ler(pasta: Path) -> dict[str, pd.DataFrame]:
    dados = {nome: pd.read_csv(pasta / f"{nome}.csv") for nome in ("registros", "ficha")}
    for nome in ("questionario", "observacao"):
        caminho = pasta / f"{nome}.csv"
        dados[nome] = pd.read_csv(caminho) if caminho.exists() else pd.DataFrame()
    registros = dados["registros"]
    registros["aceita"] = booleano(registros["aceita"])
    registros["util"] = booleano(registros["util"])
    return dados


def juntar_ficha(registros: pd.DataFrame, ficha: pd.DataFrame) -> pd.DataFrame:
    ficha = ficha.assign(chave=ficha["titulo"].map(normalizar)).drop_duplicates(
        ["participante", "chave"]
    )
    registros = registros.assign(chave=registros["titulo"].map(normalizar))
    juntos = registros.merge(
        ficha[["participante", "chave", "prioridade"]].rename(
            columns={"prioridade": "prioridade_ficha"}
        ),
        on=["participante", "chave"],
        how="left",
    )
    return juntos.drop(columns="chave")


def concordancia(real: pd.Series, previsto: pd.Series) -> dict:
    validos = real.notna() & previsto.notna() & (real != "") & (previsto != "")
    real, previsto = real[validos], previsto[validos]
    if real.empty:
        return {"n": 0, "acuracia": None, "f1_macro": None, "matriz": None}
    return {
        "n": int(len(real)),
        "acuracia": round(float(accuracy_score(real, previsto)), 4),
        "f1_macro": round(
            float(f1_score(real, previsto, labels=CLASSES, average="macro", zero_division=0)), 4
        ),
        # Linhas: prioridade da pessoa; colunas: sugestão do modelo.
        "matriz": confusion_matrix(real, previsto, labels=CLASSES).tolist(),
    }


def direcao(origem: pd.Series, destino: pd.Series) -> pd.Series:
    """+1 se a pessoa subiu a prioridade em relação à sugestão, -1 se baixou, 0 se igual."""
    return np.sign(destino.map(ORDEM) - origem.map(ORDEM))


def faixa_prazo(dias: pd.Series) -> pd.Series:
    nomes = {5: "até 1 dia", 4: "2 a 3 dias", 3: "4 a 7 dias", 2: "8 a 14 dias", 1: "mais de 14"}
    return urgencia(dias).map(nomes)


def faixa_esforco(horas: pd.Series) -> pd.Series:
    nomes = {5: "até 1 h", 4: "até 2 h", 3: "até 4 h", 2: "até 8 h", 1: "mais de 8 h"}
    return rapidez(horas).map(nomes)


def ajustes_por_atributo(tabela: pd.DataFrame, coluna_pessoa: str) -> dict:
    """Para cada faixa de atributo: quantas sugestões a pessoa subiu ou baixou."""
    base = tabela[tabela["prioridade_sugerida"].notna() & tabela[coluna_pessoa].notna()].copy()
    base = base[base[coluna_pessoa] != ""]
    base["direcao"] = direcao(base["prioridade_sugerida"], base[coluna_pessoa])
    base["prazo"] = faixa_prazo(base["dias_ate_prazo"])
    base["esforco"] = faixa_esforco(base["esforco_estimado"])
    resultado = {}
    for atributo in ("prazo", "impacto", "esforco", "categoria"):
        grupos = {}
        for valor, grupo in base.groupby(atributo, sort=True):
            grupos[str(valor)] = {
                "tarefas": int(len(grupo)),
                "subiu": int((grupo["direcao"] > 0).sum()),
                "baixou": int((grupo["direcao"] < 0).sum()),
            }
        resultado[atributo] = grupos
    resultado["total"] = {
        "tarefas": int(len(base)),
        "subiu": int((base["direcao"] > 0).sum()),
        "baixou": int((base["direcao"] < 0).sum()),
    }
    return resultado


def taxa(numerador, denominador) -> float | None:
    return round(numerador / denominador, 4) if denominador else None


def medidas_registros(tabela: pd.DataFrame) -> dict:
    com_sugestao = tabela[
        tabela["prioridade_sugerida"].notna() & (tabela["prioridade_sugerida"] != "")
    ]
    confirmadas = com_sugestao[com_sugestao["aceita"].notna()]
    avaliadas = com_sugestao[com_sugestao["util"].notna()]
    aceitas = confirmadas[confirmadas["aceita"].eq(True)]
    ajustadas = confirmadas[confirmadas["aceita"].eq(False)]

    cega = concordancia(com_sugestao["prioridade_ficha"], com_sugestao["prioridade_sugerida"])
    apos = concordancia(com_sugestao["prioridade_confirmada"], com_sugestao["prioridade_sugerida"])
    ficha_confirmada = concordancia(
        com_sugestao["prioridade_ficha"], com_sugestao["prioridade_confirmada"]
    )
    # Influência: sugestões aceitas que contrariavam a ficha.
    discordantes = confirmadas[
        confirmadas["prioridade_ficha"].notna()
        & (confirmadas["prioridade_ficha"] != confirmadas["prioridade_sugerida"])
    ]
    return {
        "tarefas": int(len(tabela)),
        "tarefas_sem_ficha": int(tabela["prioridade_ficha"].isna().sum()),
        "taxa_aceitacao": {
            "aceitas": int(len(aceitas)),
            "confirmadas": int(len(confirmadas)),
            "valor": taxa(len(aceitas), len(confirmadas)),
        },
        "concordancia_cega": cega,
        "concordancia_apos_sugestao": apos,
        "ficha_x_confirmada": ficha_confirmada,
        "influencia": {
            "sugestoes_que_contrariavam_a_ficha": int(len(discordantes)),
            "aceitas_assim_mesmo": int(discordantes["aceita"].eq(True).sum()),
            "valor": taxa(int(discordantes["aceita"].eq(True).sum()), len(discordantes)),
        },
        "comparacao_base_simulada": {
            "f1_macro_base": F1_BASE_SIMULADA,
            "f1_macro_cega": cega["f1_macro"],
            "diferenca": (
                round(cega["f1_macro"] - F1_BASE_SIMULADA, 4)
                if cega["f1_macro"] is not None
                else None
            ),
        },
        "direcao_ajustes": ajustes_por_atributo(tabela, "prioridade_confirmada"),
        "direcao_ficha": ajustes_por_atributo(tabela, "prioridade_ficha"),
        "utilidade": {
            "sim": int(avaliadas["util"].eq(True).sum()),
            "avaliadas": int(len(avaliadas)),
            "valor": taxa(int(avaliadas["util"].eq(True).sum()), len(avaliadas)),
            "quando_aceita": taxa(
                int(aceitas["util"].eq(True).sum()),
                int(aceitas["util"].notna().sum()),
            ),
            "quando_ajustada": taxa(
                int(ajustadas["util"].eq(True).sum()),
                int(ajustadas["util"].notna().sum()),
            ),
        },
        "disponibilidade": {
            "sem_sugestao": int((tabela["sugestoes"] == 0).sum()),
            "tarefas": int(len(tabela)),
            "valor": taxa(int((tabela["sugestoes"] == 0).sum()), len(tabela)),
        },
        "confianca_media": {
            "aceitas": round(float(aceitas["confianca"].mean()), 4) if len(aceitas) else None,
            "ajustadas": round(float(ajustadas["confianca"].mean()), 4) if len(ajustadas) else None,
        },
    }


def sus(questionario: pd.DataFrame) -> pd.Series:
    """Pontuação SUS de 0 a 100 (BROOKE, 1996)."""
    impares = sum(questionario[f"B{i}"] - 1 for i in (1, 3, 5, 7, 9))
    pares = sum(5 - questionario[f"B{i}"] for i in (2, 4, 6, 8, 10))
    return (impares + pares) * 2.5


def medidas_questionario(questionario: pd.DataFrame) -> dict:
    if questionario.empty:
        return {}
    notas = sus(questionario)
    itens = {}
    for item, aspecto in ITENS_C.items():
        valores = questionario[item]
        itens[item] = {
            "aspecto": aspecto,
            "mediana": float(valores.median()),
            "media": round(float(valores.mean()), 2),
            "concordam": round(float((valores >= 4).mean()), 4),
            "distribuicao": {str(n): int((valores == n).sum()) for n in range(1, 6)},
        }
    perfil = {
        coluna: questionario[coluna].value_counts().to_dict()
        for coluna in questionario.columns
        if coluna.startswith("A")
    }
    abertas = {
        coluna: questionario[["participante", coluna]].dropna().values.tolist()
        for coluna in questionario.columns
        if coluna.startswith("D")
    }
    return {
        "sus": {
            "por_participante": dict(
                zip(questionario["participante"], notas.round(1), strict=True)
            ),
            "media": round(float(notas.mean()), 1),
            "mediana": round(float(notas.median()), 1),
            "desvio": round(float(notas.std(ddof=1)), 1) if len(notas) > 1 else None,
            "minimo": float(notas.min()),
            "maximo": float(notas.max()),
            "acima_de_68": int((notas > SUS_MEDIA_REFERENCIA).sum()),
            "participantes": int(len(notas)),
        },
        "likert_c": itens,
        "perfil": perfil,
        "abertas": abertas,
    }


def medidas_observacao(observacao: pd.DataFrame) -> dict:
    if observacao.empty:
        return {}
    return {
        "ocorrencias": int(len(observacao)),
        "por_tema": observacao["tema"].value_counts().to_dict(),
        "participantes_por_tema": observacao.groupby("tema")["participante"].nunique().to_dict(),
    }


def por_participante(tabela: pd.DataFrame, questionario: pd.DataFrame) -> list[dict]:
    notas = (
        dict(zip(questionario["participante"], sus(questionario), strict=True))
        if not questionario.empty
        else {}
    )
    linhas = []
    for codigo, grupo in tabela.groupby("participante"):
        com = grupo[grupo["prioridade_sugerida"].notna()]
        confirmadas = com[com["aceita"].notna()]
        cega = concordancia(com["prioridade_ficha"], com["prioridade_sugerida"])
        linhas.append(
            {
                "participante": codigo,
                "tarefas": int(len(grupo)),
                "aceitacao": taxa(int(confirmadas["aceita"].eq(True).sum()), len(confirmadas)),
                "concordancia_cega": cega["acuracia"],
                "sus": float(notas[codigo]) if codigo in notas else None,
            }
        )
    return linhas


def marcar(fig, simulado: bool) -> None:
    if simulado:
        fig.text(
            0.99, 0.01, "DADOS SIMULADOS", ha="right", va="bottom", color="#C44E52", fontsize=8
        )


def salvar_matriz(
    matriz: list, titulo: str, rotulo_linhas: str, caminho: Path, simulado: bool
) -> None:
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.imshow(matriz, cmap="Blues")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, matriz[i][j], ha="center", va="center")
    ax.set_xticks(range(3), CLASSES)
    ax.set_yticks(range(3), CLASSES)
    ax.set_xlabel("Sugestão do modelo")
    ax.set_ylabel(rotulo_linhas)
    ax.set_title(titulo)
    fig.tight_layout()
    marcar(fig, simulado)
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def salvar_graficos(medidas: dict, saida: Path) -> None:
    simulado = medidas["dados"] == "simulados"
    reg = medidas["registros"]
    if reg["concordancia_cega"]["matriz"]:
        salvar_matriz(
            reg["concordancia_cega"]["matriz"],
            "Concordância cega",
            "Prioridade na ficha",
            saida / "matriz-cega.png",
            simulado,
        )
    if reg["concordancia_apos_sugestao"]["matriz"]:
        salvar_matriz(
            reg["concordancia_apos_sugestao"]["matriz"],
            "Após a sugestão",
            "Prioridade confirmada",
            saida / "matriz-confirmada.png",
            simulado,
        )
    quest = medidas.get("questionario")
    if not quest:
        return
    notas = quest["sus"]["por_participante"]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.bar(list(notas), list(notas.values()), color="#4C78A8")
    ax.axhline(SUS_MEDIA_REFERENCIA, color="#888", linestyle="--", label="Média de referência (68)")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Pontuação SUS")
    ax.legend(loc="lower right", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    marcar(fig, simulado)
    fig.savefig(saida / "sus.png", dpi=150)
    plt.close(fig)

    itens = quest["likert_c"]
    cores = ["#C44E52", "#E8A0A0", "#CCCCCC", "#9DB9D9", "#4C78A8"]
    fig, ax = plt.subplots(figsize=(7, 4))
    nomes = list(itens)[::-1]
    esquerda = np.zeros(len(nomes))
    for n, cor in zip(range(1, 6), cores, strict=True):
        valores = np.array([itens[i]["distribuicao"][str(n)] for i in nomes])
        ax.barh(nomes, valores, left=esquerda, color=cor, label=str(n))
        esquerda += valores
    ax.set_xlabel("Participantes")
    ax.legend(
        title="Resposta", ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.15), frameon=False
    )
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    marcar(fig, simulado)
    fig.savefig(saida / "likert-parte-c.png", dpi=150)
    plt.close(fig)


def analisar(pasta: Path, saida: Path, simulado: bool = False) -> dict:
    dados = ler(pasta)
    tabela = juntar_ficha(dados["registros"], dados["ficha"])
    medidas = {
        "dados": "simulados" if simulado else "coleta",
        "registros": medidas_registros(tabela),
        "questionario": medidas_questionario(dados["questionario"]),
        "observacao": medidas_observacao(dados["observacao"]),
        "por_participante": por_participante(tabela, dados["questionario"]),
    }
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "metricas.json").write_text(
        json.dumps(medidas, ensure_ascii=False, indent=2, default=str) + "\n"
    )
    # Base cruzada sem títulos, para publicar junto com o trabalho.
    tabela.drop(columns=["titulo"]).to_csv(saida / "tarefas-anonimizadas.csv", index=False)
    salvar_graficos(medidas, saida)
    return medidas


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("pasta", type=Path, help="pasta com registros.csv, ficha.csv etc.")
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument(
        "--simulado", action="store_true", help="marca os resultados como simulados"
    )
    args = parser.parse_args()
    m = analisar(args.pasta, args.saida, args.simulado)
    r = m["registros"]
    print(f"Taxa de aceitação: {r['taxa_aceitacao']['valor']}")
    cega = r["concordancia_cega"]
    print(f"Concordância cega: acurácia {cega['acuracia']}, F1 macro {cega['f1_macro']}")
    print(f"Após a sugestão:   acurácia {r['concordancia_apos_sugestao']['acuracia']}")
    print(f"Utilidade: {r['utilidade']['valor']}")
    print(f"Tarefas sem sugestão: {r['disponibilidade']['valor']}")
    if m["questionario"]:
        print(f"SUS média: {m['questionario']['sus']['media']}")


if __name__ == "__main__":
    main()
