import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.ml import get_ml


class MLFalso:
    """Substitui o serviço de ML: alta se impacto >= 4, senão média; ou fora do ar."""

    def __init__(self):
        self.no_ar = True
        self.chamadas: list[dict] = []

    def prever(self, dados: dict) -> dict | None:
        self.chamadas.append(dados)
        if not self.no_ar:
            return None
        prioridade = "alta" if dados["impacto"] >= 4 else "media"
        return {
            "prioridade": prioridade,
            "probabilidades": {"baixa": 0.1, "media": 0.2, "alta": 0.7},
            "fatores": [
                {
                    "atributo": "impacto",
                    "valor": dados["impacto"],
                    "descricao": "Impacto",
                    "peso": 0.3,
                }
            ],
            "modelo_versao": "teste",
        }


@pytest.fixture
def sessao_fabrica():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def ml_falso():
    return MLFalso()


@pytest.fixture
def cliente(sessao_fabrica, ml_falso):
    def db_de_teste():
        with sessao_fabrica() as sessao:
            yield sessao

    app.dependency_overrides[get_db] = db_de_teste
    app.dependency_overrides[get_ml] = lambda: ml_falso
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def registrar(cliente, email="ana@exemplo.com", senha="senha-segura"):
    resposta = cliente.post("/auth/registrar", json={"nome": "Ana", "email": email, "senha": senha})
    assert resposta.status_code == 201, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


@pytest.fixture
def auth(cliente):
    return registrar(cliente)


TAREFA = {
    "titulo": "Entregar relatório",
    "categoria": "trabalho",
    "impacto": 4,
    "complexidade": 3,
    "esforco_estimado": 2.5,
}
