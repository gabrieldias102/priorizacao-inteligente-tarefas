import json

import joblib
import pandas as pd

from treino.treinar import treinar


def test_treino_salva_modelo_que_preve_as_tres_classes(tmp_path):
    resultados = treinar(
        n=600,
        semente=0,
        versao="teste",
        dir_modelos=tmp_path / "modelos",
        dir_resultados=tmp_path / "resultados",
        csv=tmp_path / "dados.csv",
    )

    assert set(resultados["modelos"]) == {
        "Regressão Logística",
        "Árvore de Decisão",
        "Random Forest",
    }
    melhor = resultados["modelos"][resultados["escolhido"]]["teste"]
    assert melhor["f1_macro"] > resultados["linhas_de_base"]["Classe majoritária"]["f1_macro"]

    modelo = joblib.load(tmp_path / "modelos" / "modelo-teste.joblib")
    tarefa = pd.DataFrame(
        [
            {
                "dias_ate_prazo": 0,
                "impacto": 5,
                "complexidade": 3,
                "esforco_estimado": 1.0,
                "categoria": "trabalho",
            }
        ]
    )
    assert modelo.predict(tarefa)[0] in {"baixa", "media", "alta"}

    metadados = json.loads((tmp_path / "modelos" / "modelo-teste.json").read_text())
    assert metadados["algoritmo"] == resultados["escolhido"]
    assert len(list((tmp_path / "resultados").glob("matriz-*.png"))) == 3
    assert len(pd.read_csv(tmp_path / "dados.csv")) == 600
    assert len(pd.read_csv(tmp_path / "modelos" / "modelo-teste-fundo.csv")) == 100
