from datetime import UTC, datetime, timedelta

from app.ml import DIAS_SEM_PRAZO, dias_ate_prazo
from tests.conftest import TAREFA


def criar(cliente, auth, **campos):
    resposta = cliente.post("/tarefas", json={**TAREFA, **campos}, headers=auth)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_dias_ate_prazo():
    agora = datetime(2026, 10, 10, 12, tzinfo=UTC)
    assert dias_ate_prazo(None, agora) == DIAS_SEM_PRAZO
    assert dias_ate_prazo(agora + timedelta(hours=5), agora) == 0
    assert dias_ate_prazo(agora + timedelta(days=3, hours=1), agora) == 3
    assert dias_ate_prazo(agora - timedelta(days=2), agora) == 0
    assert dias_ate_prazo(datetime(2026, 10, 12, 12), agora) == 2


def test_criar_tarefa_ja_vem_com_sugestao_e_fatores(cliente, auth, ml_falso):
    tarefa = criar(
        cliente, auth, prazo=(datetime.now(UTC) + timedelta(days=2, hours=1)).isoformat()
    )
    assert tarefa["prioridade_sugerida"] == "alta"
    assert tarefa["modelo_versao"] == "teste"
    assert tarefa["sugestao"]["fatores"][0]["atributo"] == "impacto"
    assert tarefa["sugestao"]["aceita"] is None
    assert ml_falso.chamadas == [
        {
            "dias_ate_prazo": 2,
            "impacto": 4,
            "complexidade": 3,
            "esforco_estimado": 2.5,
            "categoria": "trabalho",
        }
    ]


def test_modelo_fora_do_ar_nao_impede_salvar(cliente, auth, ml_falso):
    ml_falso.no_ar = False
    tarefa = criar(cliente, auth)
    assert tarefa["prioridade_sugerida"] is None
    assert tarefa["sugestao"] is None

    url = f"/tarefas/{tarefa['id']}/sugestao"
    assert cliente.post(url, headers=auth).status_code == 503
    ml_falso.no_ar = True
    assert cliente.post(url, headers=auth).json()["prioridade_sugerida"] == "alta"


def test_mudar_atributo_gera_nova_sugestao_e_pede_nova_confirmacao(cliente, auth, ml_falso):
    tarefa = criar(cliente, auth)
    url = f"/tarefas/{tarefa['id']}"
    cliente.post(f"{url}/prioridade", json={"prioridade": "alta"}, headers=auth)

    editada = cliente.patch(url, json={"impacto": 2}, headers=auth).json()
    assert editada["prioridade_sugerida"] == "media"
    assert editada["prioridade_confirmada"] is None
    assert len(ml_falso.chamadas) == 2


def test_mudar_titulo_ou_status_nao_chama_o_modelo(cliente, auth, ml_falso):
    tarefa = criar(cliente, auth)
    url = f"/tarefas/{tarefa['id']}"
    cliente.post(f"{url}/prioridade", json={"prioridade": "baixa"}, headers=auth)

    editada = cliente.patch(url, json={"titulo": "Novo", "status": "em_andamento"}, headers=auth)
    assert editada.json()["prioridade_confirmada"] == "baixa"
    assert len(ml_falso.chamadas) == 1


def test_aceitar_e_ajustar_a_sugestao_real(cliente, auth):
    aceita = criar(cliente, auth)
    ajustada = criar(cliente, auth)
    r1 = cliente.post(
        f"/tarefas/{aceita['id']}/prioridade", json={"prioridade": "alta"}, headers=auth
    )
    r2 = cliente.post(
        f"/tarefas/{ajustada['id']}/prioridade", json={"prioridade": "baixa"}, headers=auth
    )
    assert r1.json()["sugestao"]["aceita"] is True
    assert r2.json()["sugestao"]["aceita"] is False
    assert cliente.get("/estatisticas", headers=auth).json()["taxa_aceitacao"] == 0.5
