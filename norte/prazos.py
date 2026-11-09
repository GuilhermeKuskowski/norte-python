"""
Alertas de prazo com semáforo (apoio ao plano de ação).

Não é programação dinâmica: é a regra de negócio que dá a URGÊNCIA de cada
ação. O semáforo vira peso no algoritmo da mochila (plano.py), para que o
que vence primeiro tenha mais chance de entrar na semana do cidadão.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

# Peso de urgência usado pela mochila.
PESO_SEMAFORO = {"vermelho": 3, "amarelo": 2, "verde": 1, "sem_prazo": 1, "vencido": 1, "a_confirmar": 1}

ROTULO = {
    "vermelho": "VERMELHO – agir já",
    "amarelo": "AMARELO – em breve",
    "verde": "VERDE – em dia",
    "sem_prazo": "VERDE – sem prazo curto",
    "vencido": "PRAZO PODE TER PASSADO – procure atendimento gratuito para avaliar",
    "a_confirmar": "A CONFIRMAR – se isso vale para o seu caso, informe a data",
}


@dataclass
class Prazo:
    semaforo: str
    data_limite: date | None = None
    dias_restantes: int | None = None
    observacao: str = ""

    @property
    def rotulo(self) -> str:
        return ROTULO[self.semaforo]


def somar_periodo(inicio: date, quantidade: int, unidade: str) -> date:
    if unidade == "dias":
        return inicio + timedelta(days=quantidade)
    if unidade == "anos":
        try:
            return inicio.replace(year=inicio.year + quantidade)
        except ValueError:            # 29 de fevereiro em ano não bissexto
            return inicio.replace(year=inicio.year + quantidade, day=28)
    raise ValueError(f"unidade desconhecida: {unidade}")


def classificar_dias(dias: int) -> str:
    if dias < 0:
        return "vencido"
    if dias <= 15:
        return "vermelho"
    if dias <= 60:
        return "amarelo"
    return "verde"


def calcular_prazo(regra: dict | None, datas_do_caso: dict, hoje: date) -> Prazo:
    """Calcula a data limite de uma ação a partir das datas que o cidadão informou."""
    if regra is None:
        return Prazo("sem_prazo")
    texto_inicio = datas_do_caso.get(regra["a_partir_de"])
    if not texto_inicio:
        return Prazo("a_confirmar", observacao="sem a data o Norte não calcula o prazo")
    inicio = date.fromisoformat(texto_inicio)
    limite = somar_periodo(inicio, regra["quantidade"], regra["unidade"])
    dias = (limite - hoje).days
    return Prazo(classificar_dias(dias), limite, dias)
