"""Cliente do serviço de ML."""

import logging
import math
from datetime import UTC, datetime

import httpx

from app.config import settings
from app.modelos import Tarefa

log = logging.getLogger(__name__)

# Mesmo valor usado no treino para tarefa sem prazo (ml/training/treino/gerador.py).
DIAS_SEM_PRAZO = 30
ATRIBUTOS_DO_MODELO = ("prazo", "categoria", "impacto", "complexidade", "esforco_estimado")


def dias_ate_prazo(prazo: datetime | None, agora: datetime) -> int:
    if prazo is None:
        return DIAS_SEM_PRAZO
    if prazo.tzinfo is None:
        prazo = prazo.replace(tzinfo=UTC)
    return max(0, math.floor((prazo - agora).total_seconds() / 86400))


def atributos(tarefa: Tarefa, agora: datetime | None = None) -> dict:
    return {
        "dias_ate_prazo": dias_ate_prazo(tarefa.prazo, agora or datetime.now(UTC)),
        "impacto": tarefa.impacto,
        "complexidade": tarefa.complexidade,
        "esforco_estimado": tarefa.esforco_estimado,
        "categoria": tarefa.categoria,
    }


class ClienteML:
    def __init__(self, url: str, timeout: float = 2.0):
        self.url = url
        self.timeout = timeout

    def prever(self, dados: dict) -> dict | None:
        """Devolve a previsão, ou None se o serviço estiver fora do ar."""
        try:
            resposta = httpx.post(f"{self.url}/prever", json=dados, timeout=self.timeout)
            resposta.raise_for_status()
            return resposta.json()
        except httpx.HTTPError as erro:
            log.warning("Serviço de ML indisponível: %s", erro)
            return None


def get_ml() -> ClienteML:
    return ClienteML(settings.ml_url)
