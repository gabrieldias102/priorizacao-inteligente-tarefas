import csv

from app.exportar_coleta import apagar_contas, exportar
from app.modelos import Usuario
from tests.conftest import TAREFA, registrar


def preparar(cliente):
    ana = registrar(cliente, email="ana@exemplo.com")
    beto = registrar(cliente, email="beto@exemplo.com")
    outro = registrar(cliente, email="fora@exemplo.com")

    aceita = cliente.post("/tarefas", json=TAREFA, headers=ana).json()
    cliente.post(f"/tarefas/{aceita['id']}/prioridade", json={"prioridade": "alta"}, headers=ana)
    cliente.post(f"/tarefas/{aceita['id']}/avaliacao", json={"util": True}, headers=ana)

    ajustada = cliente.post("/tarefas", json={**TAREFA, "impacto": 2}, headers=ana).json()
    url = f"/tarefas/{ajustada['id']}"
    cliente.post(f"{url}/prioridade", json={"prioridade": "baixa"}, headers=ana)
    cliente.post(f"{url}/avaliacao", json={"util": False}, headers=ana)

    cliente.post("/tarefas", json=TAREFA, headers=beto)
    cliente.post("/tarefas", json=TAREFA, headers=outro)


def test_exporta_uma_linha_por_tarefa_sem_dados_pessoais(cliente, sessao_fabrica, tmp_path):
    preparar(cliente)
    participantes = {"ana@exemplo.com": "P01", "beto@exemplo.com": "P02"}

    with sessao_fabrica() as sessao:
        exportar(sessao, participantes, tmp_path)

    with (tmp_path / "registros.csv").open(encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert [(linha["participante"], linha["tarefa"]) for linha in linhas] == [
        ("P01", "1"),
        ("P01", "2"),
        ("P02", "1"),
    ]
    primeira, segunda, terceira = linhas
    assert primeira["prioridade_sugerida"] == "alta"
    assert primeira["prioridade_confirmada"] == "alta"
    assert (primeira["aceita"], primeira["util"]) == ("True", "True")
    assert primeira["confianca"] == "0.7"
    assert segunda["prioridade_sugerida"] == "media"
    assert segunda["prioridade_confirmada"] == "baixa"
    assert (segunda["aceita"], segunda["util"]) == ("False", "False")
    assert terceira["aceita"] == "" and terceira["prioridade_confirmada"] == ""
    texto = (tmp_path / "registros.csv").read_text(encoding="utf-8")
    assert "@" not in texto and "Ana" not in texto


def test_tarefa_ajustada_e_depois_editada_mantem_a_sugestao_da_criacao(
    cliente, sessao_fabrica, tmp_path
):
    ana = registrar(cliente)
    tarefa = cliente.post("/tarefas", json=TAREFA, headers=ana).json()
    url = f"/tarefas/{tarefa['id']}"
    cliente.post(f"{url}/prioridade", json={"prioridade": "media"}, headers=ana)
    cliente.patch(url, json={"impacto": 1}, headers=ana)

    with sessao_fabrica() as sessao:
        [linha] = exportar(sessao, {"ana@exemplo.com": "P01"}, tmp_path)
    assert linha["prioridade_sugerida"] == "alta"
    assert linha["aceita"] is False
    assert linha["sugestoes"] == 2
    # A classe escolhida foi descartada pela edição; fica em branco em vez de errada.
    assert linha["prioridade_confirmada"] == ""


def test_tarefa_sem_sugestao_conta_para_disponibilidade(
    cliente, sessao_fabrica, ml_falso, tmp_path
):
    ana = registrar(cliente)
    ml_falso.no_ar = False
    cliente.post("/tarefas", json=TAREFA, headers=ana)

    with sessao_fabrica() as sessao:
        [linha] = exportar(sessao, {"ana@exemplo.com": "P01"}, tmp_path)
    assert linha["sugestoes"] == 0
    assert linha["prioridade_sugerida"] == ""


def test_apagar_contas_remove_so_os_participantes(cliente, sessao_fabrica):
    preparar(cliente)
    with sessao_fabrica() as sessao:
        apagadas = apagar_contas(sessao, {"ana@exemplo.com": "P01", "beto@exemplo.com": "P02"})
        restantes = [u.email for u in sessao.query(Usuario)]
    assert apagadas == 2
    assert restantes == ["fora@exemplo.com"]
