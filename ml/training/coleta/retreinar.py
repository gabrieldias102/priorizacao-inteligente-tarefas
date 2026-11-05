"""Retreina o modelo com as prioridades confirmadas na coleta (RF12) e compara com a v1.

A versão 2 é treinada com a base mockada mais as tarefas dos participantes, rotuladas
com a prioridade que eles confirmaram (aceita ou ajustada), com peso maior que as
tarefas mockadas. Para comparar de forma justa, a avaliação deixa um participante de
fora por vez: o modelo é treinado sem as tarefas dele e testado na ficha "cega" dele.

Uso (a partir de ml/training):

    python -m coleta.retreinar ../../docs/resultados/coleta-simulada/dados \\
        --saida ../../docs/resultados/coleta-simulada

Com --salvar, a versão 2 treinada com todos os participantes vai para ml/models
(use só com os dados reais).
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import clone

from coleta.analisar import concordancia, juntar_ficha, ler
from treino.gerador import CLASSES, gerar_tarefas
from treino.modelos import ATRIBUTOS
from treino.treinar import metricas, salvar_fundo

RAIZ = Path(__file__).resolve().parents[3]
MODELOS = RAIZ / "ml" / "models"
PESO_COLETA = 10


def base_da_coleta(pasta: Path, rotulo: str) -> pd.DataFrame:
    dados = ler(pasta)
    tabela = juntar_ficha(dados["registros"], dados["ficha"])
    coluna = {"confirmada": "prioridade_confirmada", "ficha": "prioridade_ficha"}[rotulo]
    tabela = tabela[tabela[coluna].isin(CLASSES) & tabela["dias_ate_prazo"].notna()].copy()
    tabela["rotulo"] = tabela[coluna]
    tabela["dias_ate_prazo"] = tabela["dias_ate_prazo"].astype(int)
    return tabela


def treinar_v2(modelo_v1, mock: pd.DataFrame, coleta: pd.DataFrame, peso: int):
    x = pd.concat([mock[ATRIBUTOS], coleta[ATRIBUTOS]], ignore_index=True)
    y = pd.concat([mock["prioridade"], coleta["rotulo"]], ignore_index=True)
    pesos = [1] * len(mock) + [peso] * len(coleta)
    modelo = clone(modelo_v1)
    modelo.fit(x, y, clf__sample_weight=pesos)
    return modelo


def retreinar(
    pasta: Path,
    saida: Path,
    rotulo: str = "confirmada",
    peso: int = PESO_COLETA,
    salvar: bool = False,
    simulado: bool = False,
    modelo_v1_caminho: Path = MODELOS / "modelo-v1.joblib",
    n_mock: int = 3000,
) -> dict:
    modelo_v1 = joblib.load(modelo_v1_caminho)
    mock = gerar_tarefas(n=n_mock, semente=42)
    coleta = base_da_coleta(pasta, rotulo)
    com_ficha = coleta[coleta["prioridade_ficha"].isin(CLASSES)]

    previsto_v1, previsto_v2, real = [], [], []
    for codigo in sorted(com_ficha["participante"].unique()):
        teste = com_ficha[com_ficha["participante"] == codigo]
        treino = coleta[coleta["participante"] != codigo]
        v2 = treinar_v2(modelo_v1, mock, treino, peso)
        real.extend(teste["prioridade_ficha"])
        previsto_v1.extend(modelo_v1.predict(teste[ATRIBUTOS]))
        previsto_v2.extend(v2.predict(teste[ATRIBUTOS]))

    real, previsto_v1, previsto_v2 = pd.Series(real), pd.Series(previsto_v1), pd.Series(previsto_v2)
    final = treinar_v2(modelo_v1, mock, coleta, peso)
    # Quanto a v2 se afasta da regra original: desempenho na base mockada.
    mock_teste = gerar_tarefas(n=600, semente=7)
    resultado = {
        "dados": "simulados" if simulado else "coleta",
        "rotulo": rotulo,
        "peso_tarefas_coleta": peso,
        "tarefas_coleta": int(len(coleta)),
        "avaliacao": "deixa um participante de fora; teste na ficha cega",
        "v1_na_ficha": concordancia(real, previsto_v1),
        "v2_na_ficha": concordancia(real, previsto_v2),
        "v1_base_mockada": metricas(
            mock_teste["prioridade"], modelo_v1.predict(mock_teste[ATRIBUTOS])
        ),
        "v2_base_mockada": metricas(mock_teste["prioridade"], final.predict(mock_teste[ATRIBUTOS])),
    }
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "retreino.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")

    if salvar:
        if simulado:
            raise ValueError("Não salve em ml/models um modelo treinado com dados simulados.")
        joblib.dump(final, MODELOS / "modelo-v2.joblib", compress=3)
        salvar_fundo(pd.concat([mock, coleta])[ATRIBUTOS], MODELOS / "modelo-v2-fundo.csv", 42)
        metadados = json.loads((MODELOS / "modelo-v1.json").read_text())
        metadados.update(
            versao="v2",
            treinado_em=datetime.now(UTC).isoformat(timespec="seconds"),
            metricas_teste=resultado["v2_base_mockada"],
            coleta={"tarefas": resultado["tarefas_coleta"], "peso": peso, "rotulo": rotulo},
            metricas_ficha=resultado["v2_na_ficha"],
        )
        (MODELOS / "modelo-v2.json").write_text(
            json.dumps(metadados, ensure_ascii=False, indent=2) + "\n"
        )
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("pasta", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--rotulo", choices=["confirmada", "ficha"], default="confirmada")
    parser.add_argument("--peso", type=int, default=PESO_COLETA)
    parser.add_argument("--salvar", action="store_true", help="salva modelo-v2 em ml/models")
    parser.add_argument("--simulado", action="store_true")
    args = parser.parse_args()
    r = retreinar(args.pasta, args.saida, args.rotulo, args.peso, args.salvar, args.simulado)
    for nome in ("v1_na_ficha", "v2_na_ficha", "v1_base_mockada", "v2_base_mockada"):
        print(f"{nome:<16} acurácia {r[nome]['acuracia']:.3f}  F1 macro {r[nome]['f1_macro']:.3f}")


if __name__ == "__main__":
    main()
