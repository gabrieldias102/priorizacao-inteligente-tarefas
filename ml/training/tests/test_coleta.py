import pandas as pd
import pytest

from coleta.analisar import analisar, juntar_ficha, sus
from coleta.retreinar import retreinar
from coleta.simular import N_PARTICIPANTES, simular


def test_sus_segue_o_metodo_de_brooke():
    melhor = {f"B{i}": 5 if i % 2 else 1 for i in range(1, 11)}
    pior = {f"B{i}": 1 if i % 2 else 5 for i in range(1, 11)}
    neutro = {f"B{i}": 3 for i in range(1, 11)}
    assert list(sus(pd.DataFrame([melhor, pior, neutro]))) == [100, 0, 50]


def test_ficha_e_ligada_pelo_titulo_sem_diferenciar_acentos_e_maiusculas():
    registros = pd.DataFrame(
        {"participante": ["P01", "P01"], "titulo": ["Estudar  Estatística", "Lavar roupa"]}
    )
    ficha = pd.DataFrame(
        {"participante": ["P01"], "titulo": ["estudar estatistica"], "prioridade": ["alta"]}
    )
    juntos = juntar_ficha(registros, ficha)
    assert juntos["prioridade_ficha"].tolist()[0] == "alta"
    assert pd.isna(juntos["prioridade_ficha"].tolist()[1])


def escrever(pasta, registros, ficha):
    pasta.mkdir()
    pd.DataFrame(registros).to_csv(pasta / "registros.csv", index=False)
    pd.DataFrame(ficha).to_csv(pasta / "ficha.csv", index=False)


def tarefa(titulo, sugerida, confirmada, aceita, util, sugestoes=1):
    return {
        "participante": "P01",
        "titulo": titulo,
        "categoria": "trabalho",
        "dias_ate_prazo": 2,
        "impacto": 3,
        "complexidade": 2,
        "esforco_estimado": 1.0,
        "prioridade_sugerida": sugerida,
        "confianca": 0.8,
        "prioridade_confirmada": confirmada,
        "aceita": aceita,
        "util": util,
        "sugestoes": sugestoes,
    }


def test_medidas_do_quadro_7(tmp_path):
    registros = [
        tarefa("a", "alta", "alta", True, True),  # ficha alta: concorda
        tarefa("b", "media", "media", True, True),  # ficha baixa: aceitou por influência
        tarefa("c", "media", "alta", False, False),  # ficha alta: ajustou para cima
        tarefa("d", "baixa", "baixa", True, None),  # ficha baixa: concorda, sem avaliação
        tarefa("e", None, "media", None, None, sugestoes=0),  # modelo fora do ar
    ]
    ficha = [
        {"participante": "P01", "titulo": t, "prioridade": p}
        for t, p in zip("abcde", ["alta", "baixa", "alta", "baixa", "media"], strict=True)
    ]
    escrever(tmp_path / "dados", registros, ficha)

    m = analisar(tmp_path / "dados", tmp_path / "saida")["registros"]

    assert m["taxa_aceitacao"] == {"aceitas": 3, "confirmadas": 4, "valor": 0.75}
    assert m["concordancia_cega"]["n"] == 4
    assert m["concordancia_cega"]["acuracia"] == 0.5
    assert m["concordancia_apos_sugestao"]["acuracia"] == 0.75
    assert m["influencia"] == {
        "sugestoes_que_contrariavam_a_ficha": 2,
        "aceitas_assim_mesmo": 1,
        "valor": 0.5,
    }
    assert m["direcao_ajustes"]["total"] == {"tarefas": 4, "subiu": 1, "baixou": 0}
    assert m["utilidade"]["valor"] == pytest.approx(2 / 3, abs=1e-4)
    assert m["disponibilidade"] == {"sem_sugestao": 1, "tarefas": 5, "valor": 0.2}
    assert (tmp_path / "saida" / "matriz-cega.png").exists()
    assert "titulo" not in pd.read_csv(tmp_path / "saida" / "tarefas-anonimizadas.csv")


def test_coleta_simulada_completa(tmp_path):
    arquivos = simular(tmp_path / "dados", semente=1)

    registros = pd.read_csv(arquivos["registros"])
    questionario = pd.read_csv(arquivos["questionario"])
    assert registros["participante"].nunique() == N_PARTICIPANTES
    assert len(registros) == len(pd.read_csv(arquivos["ficha"]))
    assert registros.groupby("participante").size().between(8, 12).all()
    assert questionario[[f"B{i}" for i in range(1, 11)]].isin(range(1, 6)).all().all()

    medidas = analisar(tmp_path / "dados", tmp_path / "saida", simulado=True)
    assert medidas["dados"] == "simulados"
    assert medidas["registros"]["concordancia_cega"]["n"] == len(registros) - 1
    assert 0 <= medidas["questionario"]["sus"]["media"] <= 100

    resultado = retreinar(tmp_path / "dados", tmp_path / "saida", simulado=True, n_mock=600)
    assert resultado["v2_na_ficha"]["n"] == resultado["v1_na_ficha"]["n"]
    with pytest.raises(ValueError):
        retreinar(tmp_path / "dados", tmp_path / "saida", salvar=True, simulado=True, n_mock=600)
