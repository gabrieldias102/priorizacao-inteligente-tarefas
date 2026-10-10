from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)

URGENTE = {
    "dias_ate_prazo": 0,
    "impacto": 5,
    "complexidade": 3,
    "esforco_estimado": 1,
    "categoria": "trabalho",
}
FOLGADA = {
    "dias_ate_prazo": 30,
    "impacto": 1,
    "complexidade": 1,
    "esforco_estimado": 10,
    "categoria": "casa",
}


def test_modelo_ativo_e_v1():
    corpo = cliente.get("/modelo").json()
    assert corpo["versao"] == "v1"
    assert corpo["algoritmo"] == "Árvore de Decisão"


def test_tarefa_urgente_e_importante_e_alta():
    corpo = cliente.post("/prever", json=URGENTE).json()
    assert corpo["prioridade"] == "alta"
    assert corpo["modelo_versao"] == "v1"
    assert abs(sum(corpo["probabilidades"].values()) - 1) < 1e-3


def test_tarefa_folgada_e_pouco_importante_e_baixa():
    assert cliente.post("/prever", json=FOLGADA).json()["prioridade"] == "baixa"


def test_fatores_explicam_a_sugestao():
    fatores = cliente.post("/prever", json=URGENTE).json()["fatores"]
    assert fatores[0]["atributo"] == "dias_ate_prazo"
    assert fatores[0]["peso"] > 0
    descricoes = {f["atributo"]: f["descricao"] for f in fatores}
    assert descricoes["dias_ate_prazo"] == "Prazo em menos de 1 dia"
    assert descricoes["impacto"] == "Impacto 5 de 5"
    assert descricoes["esforco_estimado"] == "Esforço de 1 h"
    pesos = [abs(f["peso"]) for f in fatores]
    assert pesos == sorted(pesos, reverse=True)


def test_atributos_invalidos_sao_recusados():
    assert cliente.post("/prever", json={**URGENTE, "impacto": 9}).status_code == 422
    assert cliente.post("/prever", json={**URGENTE, "categoria": "lazer"}).status_code == 422


def test_fatores_somam_a_diferenca_para_a_media():
    """Propriedade de eficiência dos valores de Shapley."""
    from app.modelo import modelo_ativo

    modelo = modelo_ativo()
    for tarefa in (URGENTE, FOLGADA):
        corpo = cliente.post("/prever", json=tarefa).json()
        classe = modelo.classes.index(corpo["prioridade"])
        media = modelo.pipeline.predict_proba(modelo.fundo)[:, classe].mean()
        soma = media + sum(f["peso"] for f in corpo["fatores"])
        assert abs(soma - corpo["probabilidades"][corpo["prioridade"]]) < 1e-3
