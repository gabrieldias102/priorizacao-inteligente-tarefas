"""Gera uma coleta SIMULADA de 10 participantes, no mesmo formato da coleta real.

Serve para montar e testar a análise antes de ter os dados reais. Nada aqui foi
respondido por pessoas: os números saem de suposições escritas neste arquivo e não
podem ser apresentados como resultado da pesquisa.

Suposições principais:

- cada participante prioriza com pesos próprios, em média dando um pouco mais de peso
  ao impacto e menos ao prazo do que a regra que rotulou a base (gerador.py);
- 12% das prioridades da ficha fogem do padrão (ruído de julgamento);
- quando a sugestão difere da ficha, o participante aceita assim mesmo em 30% dos
  casos (influência da recomendação) e ajusta para a da ficha nos demais;
- a nota SUS de cada pessoa sai de uma distribuição com média perto de 78.

Uso (a partir de ml/training):

    python -m coleta.simular --saida ../../docs/resultados/coleta-simulada/dados
"""

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from treino.gerador import (
    CATEGORIAS,
    CORTE_ALTA,
    CORTE_MEDIA,
    DIAS_SEM_PRAZO,
    PROB_CATEGORIAS,
    aplicar_ruido,
    rapidez,
    urgencia,
)
from treino.modelos import ATRIBUTOS

RAIZ = Path(__file__).resolve().parents[3]
MODELO = RAIZ / "ml" / "models" / "modelo-v1.joblib"

N_PARTICIPANTES = 10
RUIDO_FICHA = 0.12
ACEITA_MESMO_DISCORDANDO = 0.30
ACEITA_QUANDO_CONCORDA = 0.96
UTIL_SE_ACEITA = 0.88
UTIL_SE_AJUSTADA = 0.45

# Pesos médios dos participantes (a regra da base usa 0,45 / 0,35 / 0,10 / 0,10).
PESOS_PESSOAS = {"urgencia": 0.38, "impacto": 0.44, "complexidade": 0.06, "rapidez": 0.12}

TITULOS = {
    "estudo": [
        "Estudar para a prova de estatística",
        "Ler capítulo do livro da disciplina",
        "Entregar trabalho em grupo",
        "Revisar anotações da aula",
        "Fazer lista de exercícios",
        "Escrever resumo do artigo",
        "Assistir aula gravada",
        "Preparar apresentação do seminário",
    ],
    "trabalho": [
        "Responder e-mails pendentes",
        "Corrigir bug relatado pelo cliente",
        "Preparar reunião de planejamento",
        "Revisar pull request do colega",
        "Atualizar documentação do sistema",
        "Enviar relatório semanal",
        "Configurar ambiente de testes",
        "Fazer entrevista técnica",
    ],
    "pessoal": [
        "Pagar fatura do cartão",
        "Renovar documento",
        "Comprar presente de aniversário",
        "Ligar para a família",
        "Organizar fotos do celular",
        "Planejar viagem do feriado",
    ],
    "saude": [
        "Marcar consulta médica",
        "Ir à academia",
        "Buscar resultado de exame",
        "Comprar remédio",
    ],
    "casa": [
        "Fazer compras do mês",
        "Lavar roupa",
        "Consertar torneira",
        "Limpar a casa",
        "Pagar conta de luz",
    ],
}

COMENTARIOS_OBSERVACAO = {
    "clareza": [
        'Abriu "Por que essa prioridade?" e disse que o motivo do prazo fazia sentido.',
        "Perguntou o que significava a porcentagem de confiança.",
        "Leu os motivos antes de aceitar e comentou que ajudam a decidir.",
    ],
    "confianca": [
        "Aceitou sem abrir os motivos, dizendo que confiava na sugestão.",
        "Comentou que confiaria mais depois de usar por alguns dias.",
        "Estranhou 100% de confiança numa tarefa simples.",
    ],
    "discordancia": [
        "Ajustou para alta dizendo que a tarefa era importante mesmo com prazo longo.",
        "Disse que o sistema não sabe que a tarefa depende de outra pessoa.",
        "Baixou a prioridade de uma tarefa rápida que podia esperar.",
    ],
    "usabilidade": [
        "Hesitou para escolher a data do prazo no celular.",
        "Procurou um botão de editar no cartão antes de achar.",
        "Cadastrou as tarefas sem dificuldade e rapidamente.",
    ],
    "melhoria": [
        "Sugeriu poder ordenar a lista manualmente.",
        "Pediu lembretes perto do prazo.",
        "Sugeriu marcar tarefas recorrentes.",
    ],
}

RESPOSTAS_D = {
    "D1": [
        "Ajustei tarefas importantes com prazo longo, o sistema deixou como baixa.",
        "Na tarefa de saúde, que para mim é prioridade mesmo sem prazo.",
        "Em tarefas rápidas que o sistema subiu, mas podiam esperar.",
        "Quase não ajustei, concordei com a maioria.",
        "Quando a tarefa dependia de outra pessoa, o sistema não tinha como saber.",
    ],
    "D2": [
        "Sim, o prazo e o impacto explicaram bem.",
        "Fizeram sentido, mas o esforço pesando a favor foi estranho.",
        "Sim, gostei de ver os motivos em linguagem simples.",
        "A maioria sim; a categoria aparecendo como motivo pareceu estranho.",
    ],
    "D3": [
        "A sugestão automática já ordenando a lista.",
        "Ser simples e rápido de cadastrar.",
        "Ver o motivo de cada prioridade.",
        "Poder aceitar ou mudar a prioridade com um clique.",
    ],
    "D4": [
        "Lembretes perto do prazo.",
        "Tarefas recorrentes.",
        "Poder dizer que uma tarefa depende de outra.",
        "Um aplicativo para celular.",
        "Nada, achei completo para o objetivo.",
    ],
}


def tarefas_da_semana(rng: np.random.Generator, n: int) -> pd.DataFrame:
    """Tarefas reais de uma semana: prazos mais curtos que os da base de treino."""
    sem_prazo = rng.random(n) < 0.12
    dias = np.clip(np.round(rng.gamma(shape=1.3, scale=4, size=n)), 0, 45).astype(int)
    esforco = np.round(np.clip(rng.lognormal(0.6, 0.8, n), 0.25, 20) * 4) / 4
    categorias = rng.choice(CATEGORIAS, size=n, p=PROB_CATEGORIAS)
    usados: set[str] = set()
    titulos = []
    for categoria in categorias:
        opcoes = [t for t in TITULOS[categoria] if t not in usados] or TITULOS[categoria]
        titulo = str(rng.choice(opcoes))
        usados.add(titulo)
        titulos.append(titulo)
    return pd.DataFrame(
        {
            "titulo": titulos,
            "categoria": categorias,
            "dias_ate_prazo": np.where(sem_prazo, DIAS_SEM_PRAZO, dias),
            "impacto": rng.choice([1, 2, 3, 4, 5], size=n, p=[0.05, 0.15, 0.35, 0.28, 0.17]),
            "complexidade": rng.choice([1, 2, 3, 4, 5], size=n, p=[0.15, 0.30, 0.30, 0.17, 0.08]),
            "esforco_estimado": esforco,
        }
    )


def prioridade_da_pessoa(tarefas: pd.DataFrame, rng: np.random.Generator) -> pd.Series:
    """Prioridade que o participante anota na ficha, com pesos próprios e ruído."""
    pesos = {k: max(0.0, v + rng.normal(0, 0.05)) for k, v in PESOS_PESSOAS.items()}
    total = sum(pesos.values())
    s = (
        pesos["urgencia"] * urgencia(tarefas["dias_ate_prazo"])
        + pesos["impacto"] * tarefas["impacto"]
        + pesos["complexidade"] * tarefas["complexidade"]
        + pesos["rapidez"] * rapidez(tarefas["esforco_estimado"])
    ) / total
    rotulos = pd.Series(
        np.select([s >= CORTE_ALTA, s >= CORTE_MEDIA], ["alta", "media"], default="baixa"),
        index=tarefas.index,
    )
    return aplicar_ruido(rotulos, RUIDO_FICHA, rng)


def vizinha(classe: str, rng: np.random.Generator) -> str:
    if classe == "media":
        return str(rng.choice(["baixa", "alta"]))
    return "media"


def likert(valor: float, rng: np.random.Generator, desvio: float = 0.6) -> int:
    return int(np.clip(np.round(valor + rng.normal(0, desvio)), 1, 5))


def questionario(codigo: str, aceitacao: float, rng: np.random.Generator) -> dict:
    nota = np.clip(rng.normal(78, 9), 45, 100) / 100  # SUS desejado, de 0 a 1
    respostas = {
        "participante": codigo,
        "A1_faixa_etaria": rng.choice(["18 a 24", "25 a 34", "35 a 44"], p=[0.5, 0.4, 0.1]),
        "A2_ocupacao": rng.choice(
            [
                "estudante",
                "profissional de tecnologia",
                "estudante e profissional de tecnologia",
            ],
            p=[0.3, 0.3, 0.4],
        ),
        "A3_frequencia_lista": rng.choice(
            ["raramente", "algumas vezes por semana", "todos os dias"], p=[0.2, 0.5, 0.3]
        ),
        "A4_metodo_atual": rng.choice(
            [
                "pelo prazo",
                "pela importância",
                "por um método como Matriz de Eisenhower ou GUT",
                "pelo que for mais rápido",
                "sem critério definido",
            ],
            p=[0.4, 0.2, 0.1, 0.1, 0.2],
        ),
    }
    for i in range(1, 11):
        positivo = i % 2 == 1  # itens ímpares da SUS são positivos
        respostas[f"B{i}"] = likert(1 + 4 * nota if positivo else 5 - 4 * nota, rng)
    base = 2.6 + 2 * aceitacao  # quem aceitou mais tende a avaliar melhor
    medias = {
        "C1": base,
        "C2": base,
        "C3": base + 0.2,
        "C4": base,
        "C5": base - 0.4,
        "C6": 4.6,
        "C7": base,
        "C8": base - 0.6,
        "C9": base + 0.1,
        "C10": base,
    }
    respostas.update({item: likert(media, rng) for item, media in medias.items()})
    respostas.update({item: str(rng.choice(opcoes)) for item, opcoes in RESPOSTAS_D.items()})
    return respostas


def observacoes(codigo: str, titulos: list[str], rng: np.random.Generator) -> list[dict]:
    linhas = []
    temas = rng.choice(list(COMENTARIOS_OBSERVACAO), size=rng.integers(2, 5), replace=False)
    for tema in temas:
        linhas.append(
            {
                "participante": codigo,
                "momento": rng.choice(["uso guiado", "uso livre"], p=[0.7, 0.3]),
                "ocorrencia": str(rng.choice(COMENTARIOS_OBSERVACAO[tema])),
                "tarefa": str(rng.choice(titulos)),
                "tema": tema,
            }
        )
    return linhas


def simular(saida: Path, semente: int = 2026, modelo_caminho: Path = MODELO) -> dict[str, Path]:
    rng = np.random.default_rng(semente)
    modelo = joblib.load(modelo_caminho)
    inicio = datetime(2026, 11, 9, 14, tzinfo=UTC)

    registros, fichas, respostas, notas = [], [], [], []
    for p in range(1, N_PARTICIPANTES + 1):
        codigo = f"P{p:02d}"
        tarefas = tarefas_da_semana(rng, int(rng.integers(8, 13)))
        tarefas["ficha"] = prioridade_da_pessoa(tarefas, rng)
        tarefas["sugerida"] = modelo.predict(tarefas[ATRIBUTOS])
        confianca = modelo.predict_proba(tarefas[ATRIBUTOS]).max(axis=1)

        aceitas = 0
        for i, tarefa in tarefas.iterrows():
            fichas.append(
                {"participante": codigo, "titulo": tarefa["titulo"], "prioridade": tarefa["ficha"]}
            )
            if tarefa["sugerida"] == tarefa["ficha"]:
                aceita = rng.random() < ACEITA_QUANDO_CONCORDA
                confirmada = tarefa["sugerida"] if aceita else vizinha(tarefa["ficha"], rng)
            else:
                aceita = rng.random() < ACEITA_MESMO_DISCORDANDO
                confirmada = tarefa["sugerida"] if aceita else tarefa["ficha"]
            aceitas += aceita
            util = rng.random() < (UTIL_SE_ACEITA if aceita else UTIL_SE_AJUSTADA)
            registros.append(
                {
                    "participante": codigo,
                    "tarefa": i + 1,
                    "titulo": tarefa["titulo"],
                    "categoria": tarefa["categoria"],
                    "dias_ate_prazo": tarefa["dias_ate_prazo"],
                    "impacto": tarefa["impacto"],
                    "complexidade": tarefa["complexidade"],
                    "esforco_estimado": tarefa["esforco_estimado"],
                    "prioridade_sugerida": tarefa["sugerida"],
                    "confianca": round(float(confianca[i]), 4),
                    "prioridade_confirmada": confirmada,
                    "aceita": aceita,
                    "util": util,
                    "sugestoes": 1,
                    "status": "aberta",
                    "modelo_versao": "v1",
                    "criado_em": (inicio + timedelta(days=p, minutes=3 * i)).isoformat(),
                }
            )
        respostas.append(questionario(codigo, aceitas / len(tarefas), rng))
        notas.extend(observacoes(codigo, list(tarefas["titulo"]), rng))

    registros = pd.DataFrame(registros).astype({"aceita": object, "util": object})
    # Uma tarefa salva sem sugestão (serviço de ML demorou a responder).
    falha = int(rng.integers(len(registros)))
    registros.loc[
        falha, ["prioridade_sugerida", "confianca", "aceita", "util", "modelo_versao"]
    ] = None
    registros.loc[falha, "sugestoes"] = 0
    registros.loc[falha, "prioridade_confirmada"] = fichas[falha]["prioridade"]

    saida.mkdir(parents=True, exist_ok=True)
    arquivos = {
        "registros": saida / "registros.csv",
        "ficha": saida / "ficha.csv",
        "questionario": saida / "questionario.csv",
        "observacao": saida / "observacao.csv",
    }
    registros.to_csv(arquivos["registros"], index=False)
    pd.DataFrame(fichas).to_csv(arquivos["ficha"], index=False)
    pd.DataFrame(respostas).to_csv(arquivos["questionario"], index=False)
    pd.DataFrame(notas).to_csv(arquivos["observacao"], index=False)
    return arquivos


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--saida", type=Path, default=RAIZ / "docs" / "resultados" / "coleta-simulada" / "dados"
    )
    parser.add_argument("--semente", type=int, default=2026)
    args = parser.parse_args()
    for nome, caminho in simular(args.saida, args.semente).items():
        print(f"{nome}: {caminho}")


if __name__ == "__main__":
    main()
