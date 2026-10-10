from fastapi.testclient import TestClient

from app import main

cliente = TestClient(main.app)


def test_health_com_ml_no_ar(monkeypatch):
    async def ml_ok() -> str:
        return "ok"

    monkeypatch.setattr(main, "status_ml", ml_ok)
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "servico": "api", "ml": "ok"}


def test_health_com_ml_fora_do_ar(monkeypatch):
    monkeypatch.setattr(main.settings, "ml_url", "http://127.0.0.1:9")
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    assert resposta.json()["ml"] == "indisponível"
