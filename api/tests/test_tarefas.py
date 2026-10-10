import uuid
from datetime import UTC, datetime, timedelta

from app.modelos import Sugestao
from tests.conftest import TAREFA, registrar


def criar(cliente, auth, **campos):
    resposta = cliente.post("/tarefas", json={**TAREFA, **campos}, headers=auth)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_criar_tarefa(cliente, auth):
    tarefa = criar(cliente, auth, descricao="Versão final")
    assert tarefa["titulo"] == "Entregar relatório"
    assert tarefa["status"] == "aberta"
    assert tarefa["prioridade_sugerida"] == "alta"
    assert tarefa["prioridade_confirmada"] is None


def test_atributos_fora_da_faixa_sao_recusados(cliente, auth):
    for campos in (
        {"impacto": 6},
        {"complexidade": 0},
        {"esforco_estimado": 0},
        {"categoria": "lazer"},
    ):
        assert cliente.post("/tarefas", json={**TAREFA, **campos}, headers=auth).status_code == 422


def test_lista_ordena_por_prioridade_e_depois_prazo(cliente, auth, ml_falso):
    ml_falso.no_ar = False
    amanha = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    semana = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    baixa = criar(cliente, auth, titulo="baixa", prazo=amanha)
    alta_longe = criar(cliente, auth, titulo="alta longe", prazo=semana)
    alta_perto = criar(cliente, auth, titulo="alta perto", prazo=amanha)
    sem_prioridade = criar(cliente, auth, titulo="sem prioridade")
    for tarefa, prioridade in ((baixa, "baixa"), (alta_longe, "alta"), (alta_perto, "alta")):
        cliente.post(
            f"/tarefas/{tarefa['id']}/prioridade", json={"prioridade": prioridade}, headers=auth
        )

    titulos = [t["titulo"] for t in cliente.get("/tarefas", headers=auth).json()]
    assert titulos == ["alta perto", "alta longe", "baixa", sem_prioridade["titulo"]]


def test_filtros(cliente, auth, ml_falso):
    ml_falso.no_ar = False
    estudo = criar(cliente, auth, categoria="estudo")
    criar(cliente, auth, categoria="casa")
    cliente.patch(f"/tarefas/{estudo['id']}", json={"status": "em_andamento"}, headers=auth)
    cliente.post(f"/tarefas/{estudo['id']}/prioridade", json={"prioridade": "media"}, headers=auth)

    def ids(**params):
        return [t["id"] for t in cliente.get("/tarefas", params=params, headers=auth).json()]

    assert ids(categoria="estudo") == [estudo["id"]]
    assert ids(status="em_andamento") == [estudo["id"]]
    assert ids(prioridade="media") == [estudo["id"]]
    assert ids(prioridade="alta") == []


def test_concluir_registra_data_e_reabrir_limpa(cliente, auth):
    tarefa = criar(cliente, auth)
    concluida = cliente.patch(
        f"/tarefas/{tarefa['id']}", json={"status": "concluida"}, headers=auth
    ).json()
    assert concluida["concluida_em"] is not None
    reaberta = cliente.patch(
        f"/tarefas/{tarefa['id']}", json={"status": "aberta"}, headers=auth
    ).json()
    assert reaberta["concluida_em"] is None


def test_editar_campos_e_recusar_nulo_obrigatorio(cliente, auth):
    tarefa = criar(cliente, auth)
    editada = cliente.patch(
        f"/tarefas/{tarefa['id']}", json={"impacto": 2, "descricao": None}, headers=auth
    )
    assert editada.json()["impacto"] == 2
    assert (
        cliente.patch(f"/tarefas/{tarefa['id']}", json={"titulo": None}, headers=auth).status_code
        == 422
    )


def test_excluir(cliente, auth):
    tarefa = criar(cliente, auth)
    assert cliente.delete(f"/tarefas/{tarefa['id']}", headers=auth).status_code == 204
    assert cliente.get(f"/tarefas/{tarefa['id']}", headers=auth).status_code == 404


def test_usuario_nao_ve_tarefa_de_outro(cliente, auth):
    tarefa = criar(cliente, auth)
    outro = registrar(cliente, email="bia@exemplo.com")
    url = f"/tarefas/{tarefa['id']}"
    assert cliente.get("/tarefas", headers=outro).json() == []
    assert cliente.get(url, headers=outro).status_code == 404
    assert cliente.patch(url, json={"impacto": 1}, headers=outro).status_code == 404
    assert cliente.delete(url, headers=outro).status_code == 404
    assert (
        cliente.post(f"{url}/prioridade", json={"prioridade": "alta"}, headers=outro).status_code
        == 404
    )
    assert cliente.get(url, headers=auth).json()["impacto"] == TAREFA["impacto"]


def test_tarefa_inexistente(cliente, auth):
    assert cliente.get(f"/tarefas/{uuid.uuid4()}", headers=auth).status_code == 404


def adicionar_sugestao(sessao_fabrica, tarefa_id, prioridade):
    with sessao_fabrica() as sessao:
        sessao.add(
            Sugestao(
                tarefa_id=uuid.UUID(tarefa_id),
                atributos={},
                prioridade_sugerida=prioridade,
                modelo_versao="v1",
            )
        )
        sessao.commit()


def test_aceitar_e_ajustar_sugestao_entram_nas_estatisticas(
    cliente, auth, sessao_fabrica, ml_falso
):
    ml_falso.no_ar = False
    aceita = criar(cliente, auth)
    ajustada = criar(cliente, auth)
    adicionar_sugestao(sessao_fabrica, aceita["id"], "alta")
    adicionar_sugestao(sessao_fabrica, ajustada["id"], "media")

    cliente.post(f"/tarefas/{aceita['id']}/prioridade", json={"prioridade": "alta"}, headers=auth)
    cliente.post(
        f"/tarefas/{ajustada['id']}/prioridade", json={"prioridade": "baixa"}, headers=auth
    )

    stats = cliente.get("/estatisticas", headers=auth).json()
    assert stats["total"] == 2
    assert stats["sugestoes"] == 2
    assert stats["sugestoes_aceitas"] == 1
    assert stats["sugestoes_ajustadas"] == 1
    assert stats["taxa_aceitacao"] == 0.5
    assert stats["por_prioridade"] == {"baixa": 1, "media": 0, "alta": 1}


def test_estatisticas_sem_sugestoes(cliente, auth, ml_falso):
    ml_falso.no_ar = False
    criar(cliente, auth)
    stats = cliente.get("/estatisticas", headers=auth).json()
    assert stats["taxa_aceitacao"] is None
    assert stats["por_status"]["aberta"] == 1


def test_avaliar_sugestao(cliente, auth, sessao_fabrica, ml_falso):
    ml_falso.no_ar = False
    tarefa = criar(cliente, auth)
    url = f"/tarefas/{tarefa['id']}/avaliacao"
    assert cliente.post(url, json={"util": True}, headers=auth).status_code == 409
    adicionar_sugestao(sessao_fabrica, tarefa["id"], "media")
    assert cliente.post(url, json={"util": False}, headers=auth).status_code == 204
    with sessao_fabrica() as sessao:
        assert sessao.query(Sugestao).one().util is False
