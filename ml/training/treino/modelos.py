"""Pipelines candidatos e grades de hiperparâmetros."""

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

ATRIBUTOS_NUMERICOS = ["dias_ate_prazo", "impacto", "complexidade"]
ATRIBUTOS = [*ATRIBUTOS_NUMERICOS, "esforco_estimado", "categoria"]


def preprocessamento() -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("num", StandardScaler(), ATRIBUTOS_NUMERICOS),
            (
                "esforco",
                Pipeline(
                    [
                        ("log", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
                        ("escala", StandardScaler()),
                    ]
                ),
                ["esforco_estimado"],
            ),
            ("categoria", OneHotEncoder(handle_unknown="ignore"), ["categoria"]),
        ]
    )


def candidatos(semente: int) -> dict[str, tuple[Pipeline, dict]]:
    """Nome do algoritmo -> (pipeline, grade de hiperparâmetros)."""

    def pipe(classificador) -> Pipeline:
        return Pipeline([("prep", preprocessamento()), ("clf", classificador)])

    return {
        "Regressão Logística": (
            pipe(LogisticRegression(max_iter=2000)),
            {"clf__C": [0.1, 1, 10]},
        ),
        "Árvore de Decisão": (
            pipe(DecisionTreeClassifier(random_state=semente)),
            {"clf__max_depth": [4, 6, 8, None], "clf__min_samples_leaf": [1, 5, 20]},
        ),
        "Random Forest": (
            pipe(RandomForestClassifier(random_state=semente)),
            {
                "clf__n_estimators": [100, 200],
                "clf__max_depth": [8, 12, None],
                "clf__min_samples_leaf": [1, 5],
            },
        ),
    }
