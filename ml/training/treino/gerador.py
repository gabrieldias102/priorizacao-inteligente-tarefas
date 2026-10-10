"""Gera a base sintética (mockada) de tarefas rotuladas por prioridade.

O rótulo vem de uma pontuação inspirada no método GUT e na matriz de Eisenhower:

    S = 0,45·U + 0,35·I + 0,10·C + 0,10·R

U é a urgência (1 a 5) derivada dos dias até o prazo, I o impacto, C a complexidade
e R um bônus (1 a 5) para tarefas rápidas. Cortes em S definem baixa, média e alta.
Depois, uma fração dos rótulos é trocada para uma classe vizinha, simulando a
subjetividade de quem prioriza.
"""

import numpy as np
import pandas as pd

CATEGORIAS = ["estudo", "trabalho", "pessoal", "saude", "casa"]
PROB_CATEGORIAS = [0.25, 0.30, 0.20, 0.10, 0.15]
CLASSES = ["baixa", "media", "alta"]

PESOS = {"urgencia": 0.45, "impacto": 0.35, "complexidade": 0.10, "rapidez": 0.10}

# Cortes calibrados para classes de tamanho parecido (ver test_classes_equilibradas).
CORTE_MEDIA = 2.55
CORTE_ALTA = 3.2

# Tarefa sem prazo entra no modelo como se vencesse em 30 dias.
DIAS_SEM_PRAZO = 30
TAXA_RUIDO = 0.10


def urgencia(dias_ate_prazo: pd.Series) -> pd.Series:
    """Converte dias até o prazo em urgência de 1 (folgado) a 5 (vence até amanhã)."""
    return pd.Series(
        np.select(
            [dias_ate_prazo <= 1, dias_ate_prazo <= 3, dias_ate_prazo <= 7, dias_ate_prazo <= 14],
            [5, 4, 3, 2],
            default=1,
        ),
        index=dias_ate_prazo.index,
    )


def rapidez(esforco_horas: pd.Series) -> pd.Series:
    """Bônus de 1 a 5 para tarefas rápidas: quanto menor o esforço, maior o bônus."""
    return pd.Series(
        np.select(
            [esforco_horas <= 1, esforco_horas <= 2, esforco_horas <= 4, esforco_horas <= 8],
            [5, 4, 3, 2],
            default=1,
        ),
        index=esforco_horas.index,
    )


def pontuacao(tarefas: pd.DataFrame) -> pd.Series:
    s = (
        PESOS["urgencia"] * urgencia(tarefas["dias_ate_prazo"])
        + PESOS["impacto"] * tarefas["impacto"]
        + PESOS["complexidade"] * tarefas["complexidade"]
        + PESOS["rapidez"] * rapidez(tarefas["esforco_estimado"])
    )
    # Arredonda para os cortes não dependerem de erro de ponto flutuante.
    return s.round(2)


def rotular(tarefas: pd.DataFrame) -> pd.Series:
    """Aplica a regra sem ruído e devolve baixa, media ou alta."""
    s = pontuacao(tarefas)
    return pd.Series(
        np.select([s >= CORTE_ALTA, s >= CORTE_MEDIA], ["alta", "media"], default="baixa"),
        index=tarefas.index,
    )


def aplicar_ruido(rotulos: pd.Series, taxa: float, rng: np.random.Generator) -> pd.Series:
    """Troca uma fração dos rótulos para uma classe vizinha."""
    ruidosos = rotulos.copy()
    trocar = rng.random(len(rotulos)) < taxa
    for i in np.flatnonzero(trocar):
        atual = rotulos.iloc[i]
        if atual == "media":
            ruidosos.iloc[i] = rng.choice(["baixa", "alta"])
        else:
            ruidosos.iloc[i] = "media"
    return ruidosos


def gerar_tarefas(n: int = 3000, semente: int = 42, taxa_ruido: float = TAXA_RUIDO) -> pd.DataFrame:
    """Gera n tarefas com atributos plausíveis e a prioridade rotulada."""
    rng = np.random.default_rng(semente)

    sem_prazo = rng.random(n) < 0.15
    dias = np.clip(np.round(rng.gamma(shape=1.5, scale=5, size=n)), 0, 60).astype(int)
    dias = np.where(sem_prazo, DIAS_SEM_PRAZO, dias)

    esforco = np.clip(rng.lognormal(mean=0.8, sigma=0.8, size=n), 0.25, 40)
    esforco = np.round(esforco * 4) / 4

    tarefas = pd.DataFrame(
        {
            "dias_ate_prazo": dias,
            "impacto": rng.choice([1, 2, 3, 4, 5], size=n, p=[0.10, 0.20, 0.35, 0.20, 0.15]),
            "complexidade": rng.choice([1, 2, 3, 4, 5], size=n, p=[0.15, 0.25, 0.30, 0.20, 0.10]),
            "esforco_estimado": esforco,
            "categoria": rng.choice(CATEGORIAS, size=n, p=PROB_CATEGORIAS),
        }
    )
    tarefas["prioridade_regra"] = rotular(tarefas)
    tarefas["prioridade"] = aplicar_ruido(tarefas["prioridade_regra"], taxa_ruido, rng)
    return tarefas
