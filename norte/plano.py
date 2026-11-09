"""
Plano da semana: quais ações fazer primeiro com o tempo que a pessoa tem.

TÉCNICA: TABULAÇÃO (programação dinâmica de baixo para cima) –
problema da MOCHILA 0/1.

O problema: o plano de ação de um caso pode ter várias ações (pedir extrato,
ir ao sindicato, dar entrada no seguro-desemprego, ir à Defensoria...). Mas
quem mais precisa do Norte tem pouco tempo livre: a Márcia faz bicos, o
Rafael perde renda a cada hora parado. Se ela tem 4 horas nesta semana,
quais ações cabem e trazem o maior benefício?

  - capacidade  = tempo disponível na semana (em blocos de 30 minutos)
  - custo       = duração estimada de cada ação (em blocos de 30 minutos)
  - benefício   = impacto da ação (1 a 10, definido pela curadoria)
                  x peso de urgência do prazo (vermelho 3, amarelo 2, verde 1)

    T[i][c] = maior benefício usando só as i primeiras ações com capacidade c

    T[0][c] = 0
    T[i][c] = T[i-1][c]                                  (não faz a ação i)
            ou T[i-1][c - custo_i] + beneficio_i          (faz a ação i, se couber)
            – o que for maior

A tabela é preenchida com dois laços, sem recursão. A resposta fica em
T[n][capacidade] e as ações escolhidas são recuperadas andando de trás para
frente na tabela.

Custo: O(n · C) de tempo e memória (n ações, C blocos de tempo).
Testar todas as combinações (força bruta) custa O(2^n · n).
"""
from __future__ import annotations

from itertools import combinations
from math import ceil

MINUTOS_POR_BLOCO = 30


def em_blocos(minutos: int) -> int:
    return ceil(minutos / MINUTOS_POR_BLOCO)


def mochila_tabulada(custos: list[int], beneficios: list[int], capacidade: int) -> tuple[int, list[int]]:
    """Devolve (melhor benefício, índices das ações escolhidas)."""
    n = len(custos)
    tabela = [[0] * (capacidade + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        custo, beneficio = custos[i - 1], beneficios[i - 1]
        for c in range(capacidade + 1):
            tabela[i][c] = tabela[i - 1][c]                       # não faz
            if custo <= c:
                com_acao = tabela[i - 1][c - custo] + beneficio   # faz
                if com_acao > tabela[i][c]:
                    tabela[i][c] = com_acao

    # Reconstrução: se o valor mudou da linha i-1 para a i, a ação i entrou.
    escolhidas = []
    c = capacidade
    for i in range(n, 0, -1):
        if tabela[i][c] != tabela[i - 1][c]:
            escolhidas.append(i - 1)
            c -= custos[i - 1]
    escolhidas.reverse()
    return tabela[n][capacidade], escolhidas


def mochila_forca_bruta(custos: list[int], beneficios: list[int], capacidade: int) -> tuple[int, list[int]]:
    """Testa todas as 2^n combinações. Só para comparar (correção e tempo)."""
    n = len(custos)
    melhor, melhor_conj = 0, []
    for k in range(n + 1):
        for conj in combinations(range(n), k):
            if sum(custos[i] for i in conj) <= capacidade:
                valor = sum(beneficios[i] for i in conj)
                if valor > melhor:
                    melhor, melhor_conj = valor, list(conj)
    return melhor, melhor_conj


def montar_semana(acoes: list[dict], horas_disponiveis: float) -> dict:
    """Escolhe as ações da semana e ordena pela urgência.

    Cada ação já chega com 'beneficio' calculado (impacto x peso do semáforo).
    """
    capacidade = int(horas_disponiveis * 60) // MINUTOS_POR_BLOCO
    custos = [em_blocos(a["duracao_min"]) for a in acoes]
    beneficios = [a["beneficio"] for a in acoes]
    total, idx = mochila_tabulada(custos, beneficios, capacidade)

    escolhidas = [acoes[i] for i in idx]
    depois = [a for i, a in enumerate(acoes) if i not in set(idx)]

    # Dentro da semana, faz primeiro o que vence primeiro (sem data = por último).
    def chave_urgencia(a: dict):
        dias = a["prazo"].dias_restantes
        return (dias if dias is not None and dias >= 0 else 10**6, -a["beneficio"])

    escolhidas.sort(key=chave_urgencia)
    depois.sort(key=chave_urgencia)
    minutos_usados = sum(em_blocos(a["duracao_min"]) for a in escolhidas) * MINUTOS_POR_BLOCO
    return {"capacidade_blocos": capacidade, "beneficio_total": total,
            "minutos_usados": minutos_usados, "esta_semana": escolhidas, "depois": depois}
