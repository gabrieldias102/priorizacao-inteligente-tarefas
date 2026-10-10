import numpy as np
import pandas as pd

from treino.gerador import CLASSES, gerar_tarefas, rotular, urgencia


def test_mesma_semente_gera_mesma_base():
    pd.testing.assert_frame_equal(gerar_tarefas(500, semente=7), gerar_tarefas(500, semente=7))


def test_atributos_dentro_dos_limites():
    t = gerar_tarefas(2000)
    assert t["impacto"].between(1, 5).all()
    assert t["complexidade"].between(1, 5).all()
    assert t["dias_ate_prazo"].between(0, 60).all()
    assert t["esforco_estimado"].between(0.25, 40).all()
    assert set(t["prioridade"]) == set(CLASSES)


def test_classes_equilibradas():
    proporcao = gerar_tarefas(20000, semente=1)["prioridade_regra"].value_counts(normalize=True)
    assert proporcao.between(0.28, 0.40).all()


def test_ruido_troca_cerca_de_dez_por_cento_para_classe_vizinha():
    t = gerar_tarefas(20000, semente=3)
    trocados = t[t["prioridade"] != t["prioridade_regra"]]
    assert 0.08 < len(trocados) / len(t) < 0.12
    saltos = {("baixa", "alta"), ("alta", "baixa")}
    assert not any(
        par in saltos
        for par in zip(trocados["prioridade_regra"], trocados["prioridade"], strict=True)
    )


def test_sem_ruido_quando_taxa_zero():
    t = gerar_tarefas(1000, taxa_ruido=0)
    assert (t["prioridade"] == t["prioridade_regra"]).all()


def test_urgencia_por_faixa_de_prazo():
    dias = pd.Series([0, 1, 2, 3, 5, 7, 10, 14, 15, 30])
    assert urgencia(dias).tolist() == [5, 5, 4, 4, 3, 3, 2, 2, 1, 1]


def test_prazo_curto_e_impacto_alto_e_alta():
    tarefa = pd.DataFrame(
        [{"dias_ate_prazo": 0, "impacto": 5, "complexidade": 3, "esforco_estimado": 1.0}]
    )
    assert rotular(tarefa).iloc[0] == "alta"


def test_prazo_folgado_e_impacto_baixo_e_baixa():
    tarefa = pd.DataFrame(
        [{"dias_ate_prazo": 30, "impacto": 1, "complexidade": 1, "esforco_estimado": 10.0}]
    )
    assert rotular(tarefa).iloc[0] == "baixa"


def test_mais_urgencia_nunca_baixa_a_prioridade():
    base = gerar_tarefas(500, semente=5)
    urgente = base.assign(dias_ate_prazo=0)
    ordem = {c: i for i, c in enumerate(CLASSES)}
    antes = rotular(base).map(ordem)
    depois = rotular(urgente).map(ordem)
    assert np.all(depois >= antes)
