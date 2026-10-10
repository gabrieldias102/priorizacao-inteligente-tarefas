"""Treina e compara os algoritmos na base mockada e salva o melhor modelo.

Uso (a partir de ml/training):

    python -m treino.treinar
"""

import argparse
import json
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import joblib
import matplotlib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    f1_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split

from treino.gerador import CLASSES, gerar_tarefas
from treino.modelos import ATRIBUTOS, candidatos

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = Path(__file__).resolve().parents[3]


def metricas(y_real: pd.Series, y_prev) -> dict:
    relatorio = classification_report(
        y_real, y_prev, labels=CLASSES, output_dict=True, zero_division=0
    )
    return {
        "acuracia": round(accuracy_score(y_real, y_prev), 4),
        "f1_macro": round(
            f1_score(y_real, y_prev, labels=CLASSES, average="macro", zero_division=0), 4
        ),
        "por_classe": {
            c: {k: round(relatorio[c][k], 4) for k in ("precision", "recall", "f1-score")}
            for c in CLASSES
        },
    }


def salvar_matriz(y_real, y_prev, titulo: str, caminho: Path) -> None:
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_predictions(
        y_real, y_prev, labels=CLASSES, ax=ax, cmap="Blues", colorbar=False
    )
    ax.set_title(titulo)
    ax.set_xlabel("Prevista")
    ax.set_ylabel("Real")
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def importancia_atributos(modelo) -> dict[str, float]:
    nomes = modelo.named_steps["prep"].get_feature_names_out()
    clf = modelo.named_steps["clf"]
    if hasattr(clf, "feature_importances_"):
        valores = clf.feature_importances_
    else:
        valores = abs(clf.coef_).mean(axis=0)
        valores = valores / valores.sum()
    pares = sorted(zip(nomes, valores, strict=True), key=lambda p: -p[1])
    return {nome.split("__", 1)[1]: round(float(v), 4) for nome, v in pares}


def treinar(
    n: int, semente: int, versao: str, dir_modelos: Path, dir_resultados: Path, csv: Path | None
) -> dict:
    dir_modelos.mkdir(parents=True, exist_ok=True)
    dir_resultados.mkdir(parents=True, exist_ok=True)

    tarefas = gerar_tarefas(n=n, semente=semente)
    if csv is not None:
        csv.parent.mkdir(parents=True, exist_ok=True)
        tarefas.to_csv(csv, index=False)
    treino, teste = train_test_split(
        tarefas, test_size=0.2, stratify=tarefas["prioridade"], random_state=semente
    )
    x_treino, y_treino = treino[ATRIBUTOS], treino["prioridade"]
    x_teste, y_teste = teste[ATRIBUTOS], teste["prioridade"]

    resultados: dict = {"linhas_de_base": {}, "modelos": {}}

    maioria = DummyClassifier(strategy="most_frequent").fit(x_treino, y_treino)
    resultados["linhas_de_base"]["Classe majoritária"] = metricas(y_teste, maioria.predict(x_teste))
    resultados["linhas_de_base"]["Regra sem ruído"] = metricas(y_teste, teste["prioridade_regra"])

    validacao = StratifiedKFold(n_splits=5, shuffle=True, random_state=semente)
    melhores = {}
    for nome, (pipeline, grade) in candidatos(semente).items():
        busca = GridSearchCV(pipeline, grade, cv=validacao, scoring="f1_macro")
        busca.fit(x_treino, y_treino)
        previsto = busca.best_estimator_.predict(x_teste)
        melhores[nome] = busca.best_estimator_
        resultados["modelos"][nome] = {
            "melhores_parametros": {
                k.removeprefix("clf__"): v for k, v in busca.best_params_.items()
            },
            "f1_macro_validacao": round(busca.best_score_, 4),
            "teste": metricas(y_teste, previsto),
            "importancia_atributos": importancia_atributos(busca.best_estimator_),
        }
        arquivo = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
        arquivo = arquivo.lower().replace(" ", "-")
        salvar_matriz(y_teste, previsto, nome, dir_resultados / f"matriz-{arquivo}.png")

    # Escolhe pela validação cruzada, não pelo teste, para o teste seguir imparcial.
    escolhido = max(
        resultados["modelos"], key=lambda m: resultados["modelos"][m]["f1_macro_validacao"]
    )
    resultados["escolhido"] = escolhido
    resultados["base"] = {
        "tarefas": n,
        "treino": len(treino),
        "teste": len(teste),
        "semente": semente,
        "distribuicao": tarefas["prioridade"].value_counts().to_dict(),
    }

    metadados = {
        "versao": versao,
        "algoritmo": escolhido,
        "atributos": ATRIBUTOS,
        "classes": CLASSES,
        "treinado_em": datetime.now(UTC).isoformat(timespec="seconds"),
        "metricas_teste": resultados["modelos"][escolhido]["teste"],
        "parametros": resultados["modelos"][escolhido]["melhores_parametros"],
    }
    joblib.dump(melhores[escolhido], dir_modelos / f"modelo-{versao}.joblib", compress=3)
    (dir_modelos / f"modelo-{versao}.json").write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2) + "\n"
    )
    (dir_resultados / "metricas.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2) + "\n"
    )
    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tarefas", type=int, default=3000)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--versao", default="v1")
    parser.add_argument("--modelos", type=Path, default=RAIZ / "ml" / "models")
    parser.add_argument("--resultados", type=Path, default=RAIZ / "docs" / "resultados" / "fase-1")
    parser.add_argument(
        "--csv", type=Path, default=RAIZ / "ml" / "training" / "dados" / "tarefas_mock.csv"
    )
    args = parser.parse_args()

    resultados = treinar(
        args.tarefas, args.semente, args.versao, args.modelos, args.resultados, args.csv
    )
    linhas = {
        **resultados["linhas_de_base"],
        **{m: r["teste"] for m, r in resultados["modelos"].items()},
    }
    print(f"{'Modelo':<22} {'Acurácia':>9} {'F1 macro':>9}")
    for nome, m in linhas.items():
        print(f"{nome:<22} {m['acuracia']:>9.3f} {m['f1_macro']:>9.3f}")
    print(f"Escolhido: {resultados['escolhido']}")


if __name__ == "__main__":
    main()
