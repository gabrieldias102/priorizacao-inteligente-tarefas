"""Carrega o modelo treinado e explica cada previsão com valores de Shapley."""

import json
from functools import lru_cache
from itertools import combinations
from math import factorial
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pydantic_settings import BaseSettings

RAIZ_ML = Path(__file__).resolve().parents[2]
ATRIBUTOS = ["dias_ate_prazo", "impacto", "complexidade", "esforco_estimado", "categoria"]


class Settings(BaseSettings):
    modelo_caminho: Path = RAIZ_ML / "models" / "modelo-v1.joblib"


def descrever(atributo: str, valor) -> str:
    if atributo == "dias_ate_prazo":
        if valor == 0:
            return "Prazo vence hoje"
        return f"Prazo em {valor} dia" + ("s" if valor != 1 else "")
    if atributo == "impacto":
        return f"Impacto {valor} de 5"
    if atributo == "complexidade":
        return f"Complexidade {valor} de 5"
    if atributo == "esforco_estimado":
        return "Esforço de " + f"{valor:g}".replace(".", ",") + " h"
    return f"Categoria {valor}"


def coalizoes(n: int) -> list[tuple[int, ...]]:
    return [c for k in range(n + 1) for c in combinations(range(n), k)]


class Modelo:
    def __init__(self, caminho: Path):
        self.pipeline = joblib.load(caminho)
        self.metadados = json.loads(caminho.with_suffix(".json").read_text())
        self.versao: str = self.metadados["versao"]
        self.classes: list[str] = list(self.pipeline.classes_)
        self.fundo = pd.read_csv(caminho.with_name(f"{caminho.stem}-fundo.csv"))[ATRIBUTOS]
        self.coalizoes = coalizoes(len(ATRIBUTOS))

    def shapley(self, atributos: dict, indice_classe: int) -> list[float]:
        """Valores de Shapley exatos (intervencionais) da classe prevista.

        Para cada coalizão S de atributos, v(S) é a probabilidade média da classe
        quando os atributos de S têm os valores da tarefa e os demais vêm da amostra
        de fundo. Com 5 atributos são 32 coalizões, calculadas num único lote.
        """
        n, m = len(ATRIBUTOS), len(self.fundo)
        lotes = []
        for coalizao in self.coalizoes:
            linhas = self.fundo.copy()
            for i in coalizao:
                linhas[ATRIBUTOS[i]] = atributos[ATRIBUTOS[i]]
            lotes.append(linhas)
        probs = self.pipeline.predict_proba(pd.concat(lotes, ignore_index=True))[:, indice_classe]
        medias = probs.reshape(len(self.coalizoes), m).mean(axis=1)
        valor = dict(zip(self.coalizoes, medias, strict=True))

        resultado = np.zeros(n)
        for coalizao, v in valor.items():
            for i in range(n):
                if i in coalizao:
                    continue
                com_i = tuple(sorted((*coalizao, i)))
                peso = factorial(len(coalizao)) * factorial(n - len(coalizao) - 1) / factorial(n)
                resultado[i] += peso * (valor[com_i] - v)
        return resultado.tolist()

    def prever(self, atributos: dict) -> dict:
        probs = self.pipeline.predict_proba(pd.DataFrame([atributos])[ATRIBUTOS])[0]
        indice = int(probs.argmax())
        contribuicoes = self.shapley(atributos, indice)
        fatores = [
            {
                "atributo": atributo,
                "valor": atributos[atributo],
                "descricao": descrever(atributo, atributos[atributo]),
                "peso": round(peso, 4),
            }
            for atributo, peso in zip(ATRIBUTOS, contribuicoes, strict=True)
        ]
        fatores.sort(key=lambda f: -abs(f["peso"]))
        return {
            "prioridade": self.classes[indice],
            "probabilidades": {
                c: round(float(p), 4) for c, p in zip(self.classes, probs, strict=True)
            },
            "fatores": fatores,
            "modelo_versao": self.versao,
        }


@lru_cache
def modelo_ativo() -> Modelo:
    return Modelo(Settings().modelo_caminho)
