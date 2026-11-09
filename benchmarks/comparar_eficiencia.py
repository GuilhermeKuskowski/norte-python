"""
Noção de eficiência: versão ingênua x versão com programação dinâmica.

Rodar a partir da pasta do projeto:
    python benchmarks/comparar_eficiencia.py

Os tempos dependem do computador; o que importa é como cada versão CRESCE
quando o cenário cresce. O resultado também é salvo em benchmarks/resultados.md.
"""
from __future__ import annotations

import random
import sys
import time
from itertools import combinations
from math import inf
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from norte import dados, plano, triagem          # noqa: E402
from norte.atendimento import MapaBairro          # noqa: E402

linhas_md: list[str] = []


def saida(texto: str = "") -> None:
    print(texto)
    linhas_md.append(texto)


def cronometrar(funcao, *args, repeticoes: int = 1):
    inicio = time.perf_counter()
    for _ in range(repeticoes):
        resultado = funcao(*args)
    return resultado, (time.perf_counter() - inicio) / repeticoes


def ms(segundos: float) -> str:
    return f"{segundos * 1000:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")


def milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


# ----------------------------------------------------------------------------
# 1) Memoização: distância de edição
# ----------------------------------------------------------------------------
def contar_chamadas_ingenua(a: str, b: str) -> int:
    contador = 0

    def d(x: str, y: str) -> int:
        nonlocal contador
        contador += 1
        if not x:
            return len(y)
        if not y:
            return len(x)
        if x[-1] == y[-1]:
            return d(x[:-1], y[:-1])
        return 1 + min(d(x[:-1], y), d(x, y[:-1]), d(x[:-1], y[:-1]))

    d(a, b)
    return contador


def bloco_memoizacao() -> None:
    saida("## 1. Memoização – distância de edição (triagem)\n")
    saida("Pares de palavras sem letras em comum (pior caso da recursão).\n")
    saida("| Tamanho (m = n) | Chamadas recursivas sem memo | Subproblemas com memo (m+1)·(n+1) "
          "| Tempo sem memo (ms) | Tempo com memo (ms) | Tempo tabulado (ms) |")
    saida("|---|---|---|---|---|---|")
    for n in (3, 5, 7, 8, 9, 10, 12, 20):
        a, b = "a" * n, "b" * n
        memo_t = cronometrar(triagem.distancia_memo, a, b, repeticoes=20)[1]
        tab_t = cronometrar(triagem.distancia_tabulada, a, b, repeticoes=20)[1]
        if n <= 9:
            chamadas = milhar(contar_chamadas_ingenua(a, b))
            ing_t = ms(cronometrar(triagem.distancia_ingenua, a, b)[1])
        else:
            chamadas, ing_t = "inviável", "inviável"
        saida(f"| {n} | {chamadas} | {(n + 1) ** 2} | {ing_t} | {ms(memo_t)} | {ms(tab_t)} |")

    # Cache por par de palavras em um volume realista de atendimentos.
    saida("\n**Cache por par de palavras (2ª camada de memoização)** – 500 relatos simulados, "
          "montados com o vocabulário das 10 áreas e erros de digitação aleatórios:\n")
    rnd = random.Random(2026)
    areas = dados.areas()
    vocab = [p for a in areas.values() for p in a["palavras"]] + ["casa", "ontem", "mae", "hoje", "ajuda", "dinheiro"]

    def com_erro(p: str) -> str:
        if len(p) > 4 and rnd.random() < 0.35:
            i = rnd.randrange(len(p))
            return p[:i] + rnd.choice("aeioscrzu") + p[i + 1:]
        return p

    relatos = [" ".join(com_erro(rnd.choice(vocab)) for _ in range(rnd.randint(6, 14))) for _ in range(500)]

    original = triagem.distancia
    triagem.distancia = triagem.distancia_memo            # desliga o cache de pares
    _, sem_cache = cronometrar(lambda: [triagem.classificar(r, areas) for r in relatos])
    triagem.distancia = original
    triagem.distancia.cache_clear()
    _, com_cache = cronometrar(lambda: [triagem.classificar(r, areas) for r in relatos])
    info = triagem.estatisticas_cache()
    saida("| Versão | Tempo total (ms) | Por relato (ms) |")
    saida("|---|---|---|")
    saida(f"| Sem cache de pares | {ms(sem_cache)} | {ms(sem_cache / len(relatos))} |")
    saida(f"| Com cache de pares | {ms(com_cache)} | {ms(com_cache / len(relatos))} |")
    taxa = f"{info['taxa_acerto']:.1%}".replace(".", ",")
    ganho = f"{sem_cache / com_cache:.1f}".replace(".", ",")
    saida(f"\nReaproveitamento do cache: {taxa} das comparações "
          f"({milhar(info['acertos'])} vindas do cache, {milhar(info['calculos'])} calculadas). "
          f"Ganho: {ganho}x mais rápido.\n")


# ----------------------------------------------------------------------------
# 2) Tabulação: mochila do plano da semana
# ----------------------------------------------------------------------------
def bloco_tabulacao() -> None:
    saida("## 2. Tabulação – mochila 0/1 (plano da semana)\n")
    saida("Capacidade: 10 horas (20 blocos de 30 min). Ações com 1 a 6 blocos e benefício de 1 a 30.\n")
    saida("| Nº de ações (n) | Combinações testadas pela força bruta (2^n) | Células da tabela (n+1)·(C+1) "
          "| Força bruta (ms) | Tabulação (ms) | Mesmo resultado? |")
    saida("|---|---|---|---|---|---|")
    rnd = random.Random(11)
    cap = 20
    for n in (5, 10, 14, 16, 18, 20, 40, 100):
        custos = [rnd.randint(1, 6) for _ in range(n)]
        benef = [rnd.randint(1, 30) for _ in range(n)]
        (val_t, _), tab_t = cronometrar(plano.mochila_tabulada, custos, benef, cap)
        if n <= 18:
            (val_b, _), bru_t = cronometrar(plano.mochila_forca_bruta, custos, benef, cap)
            bru, igual = ms(bru_t), "sim" if val_b == val_t else "NÃO"
        else:
            bru, igual = "inviável", "–"
        saida(f"| {n} | {milhar(2 ** n)} | {milhar((n + 1) * (cap + 1))} | {bru} | {ms(tab_t)} | {igual} |")
    saida("")


# ----------------------------------------------------------------------------
# 3) Grafos: Floyd-Warshall x Dijkstra x força bruta
# ----------------------------------------------------------------------------
def bairro_em_grade(lado: int, semente: int) -> MapaBairro:
    rnd = random.Random(semente)
    nos = [{"id": f"{i}_{j}", "nome": f"Esquina {i}-{j}"} for i in range(lado) for j in range(lado)]
    arestas = []
    for i in range(lado):
        for j in range(lado):
            if i + 1 < lado:
                arestas.append([f"{i}_{j}", f"{i + 1}_{j}", rnd.randint(1, 9), rnd.random() > 0.15])
            if j + 1 < lado:
                arestas.append([f"{i}_{j}", f"{i}_{j + 1}", rnd.randint(1, 9), rnd.random() > 0.15])
    return MapaBairro({"nos": nos, "arestas": arestas})


def menor_por_forca_bruta(mapa: MapaBairro, origem: str, destino: str) -> float:
    """Enumera TODOS os caminhos simples (sem repetir esquina). Exponencial."""
    adj = mapa.adjacencia()
    melhor = inf
    visitado = {origem}

    def dfs(u: str, custo: float) -> None:
        nonlocal melhor
        if u == destino:
            melhor = min(melhor, custo)
            return
        for v, w in adj[u]:
            if v not in visitado:
                visitado.add(v)
                dfs(v, custo + w)
                visitado.remove(v)

    dfs(origem, 0.0)
    return melhor


def bloco_grafos() -> None:
    saida("## 3. Grafos – menor caminho até o atendimento\n")
    saida("**a) Por que não testar todos os caminhos:** bairro em grade, de uma esquina à oposta.\n")
    saida("| Grade | Vértices | Força bruta (ms) | Floyd-Warshall (ms) | Mesmo resultado? |")
    saida("|---|---|---|---|---|")
    for lado in (3, 4, 5, 6):
        mapa = bairro_em_grade(lado, lado)
        o, d = "0_0", f"{lado - 1}_{lado - 1}"
        fw_val, fw_t = cronometrar(lambda: (mapa._cache_fw.clear(), mapa.tempo(o, d))[1])
        if lado <= 5:
            bf_val, bf_t = cronometrar(menor_por_forca_bruta, mapa, o, d)
            saida(f"| {lado}x{lado} | {lado * lado} | {ms(bf_t)} | {ms(fw_t)} | {'sim' if bf_val == fw_val else 'NÃO'} |")
        else:
            saida(f"| {lado}x{lado} | {lado * lado} | inviável (mais de 1 milhão de caminhos) | {ms(fw_t)} | – |")

    saida("\n**b) Floyd-Warshall (calcula tudo uma vez) x Dijkstra (calcula a cada atendimento):** "
          "1.000 atendimentos, cada um saindo de uma esquina aleatória.\n")
    saida("| Grade | Vértices | FW: pré-cálculo O(V³) (ms) | FW: 1.000 consultas O(1) (ms) "
          "| FW total (ms) | Dijkstra: 1.000 execuções (ms) | Mais rápido |")
    saida("|---|---|---|---|---|---|---|")
    for lado in (5, 8, 10, 14, 20):
        mapa = bairro_em_grade(lado, 100 + lado)
        rnd = random.Random(lado)
        consultas = [(rnd.choice(mapa.ids), rnd.choice(mapa.ids)) for _ in range(1000)]
        mapa._cache_fw.clear()
        _, pre = cronometrar(mapa.floyd_warshall)
        _, cons = cronometrar(lambda: [mapa.tempo(o, d) for o, d in consultas])
        _, dij = cronometrar(lambda: [mapa.dijkstra(o)[d] for o, d in consultas])
        vencedor = "Floyd-Warshall" if pre + cons < dij else "Dijkstra"
        saida(f"| {lado}x{lado} | {lado * lado} | {ms(pre)} | {ms(cons)} | {ms(pre + cons)} | {ms(dij)} | {vencedor} |")

    real = MapaBairro(dados.bairro())
    _, pre_real = cronometrar(real.floyd_warshall)
    saida(f"\nNo mapa do protótipo ({len(real.ids)} vértices, {len(real.arestas)} trechos) o "
          f"pré-cálculo leva {ms(pre_real)} ms e fica guardado; cada consulta depois é imediata.\n")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    saida("# Resultados de eficiência – Norte (Programação Dinâmica)\n")
    saida(f"Python {sys.version.split()[0]} · tempos em milissegundos · dependem do computador.\n")
    bloco_memoizacao()
    bloco_tabulacao()
    bloco_grafos()
    (RAIZ / "benchmarks" / "resultados.md").write_text("\n".join(linhas_md) + "\n", encoding="utf-8")
    print("\n(resultado salvo em benchmarks/resultados.md)")
