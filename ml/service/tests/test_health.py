from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_health():
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "servico": "ml"}


def test_modelo_sem_versao_ativa():
    assert cliente.get("/modelo").json() == {"versao": None, "algoritmo": None}
