"""
Achar atendimento gratuito: do mais perto ao mais longe, com rota acessível.

TÉCNICA: GRAFOS + programação dinâmica em grafos (Floyd-Warshall).

O bairro vira um grafo: vértices são esquinas, pontos de referência e locais
de atendimento (Defensoria, Procon, CRAS...). Arestas são trechos de rua com
o tempo de caminhada. Cada trecho também diz se é ACESSÍVEL (sem escada,
sem ladeira forte, calçada boa): para o Carlos (cego) e o Seu José (idoso),
o Norte só usa trechos acessíveis, mesmo que o caminho fique mais longo.

Floyd-Warshall é programação dinâmica:

    dist_k[i][j] = menor tempo de i até j usando só os vértices 0..k-1
                   como pontos intermediários

    dist_k[i][j] = min( dist_{k-1}[i][j],
                        dist_{k-1}[i][k] + dist_{k-1}[k][j] )

A tabela é reaproveitada de uma iteração para a outra (tabulação em 3 laços).
Custo: O(V³) uma única vez; depois, cada consulta "qual o tempo de X até Y"
é O(1) e o caminho é remontado pela matriz 'proximo'. Como o Norte atende
muita gente no mesmo bairro e o bairro tem poucas dezenas de vértices,
calcular tudo uma vez e consultar muitas vezes compensa.

Dijkstra (guloso, O((V+E) log V) por origem) fica como comparação e como
conferência nos testes: os dois têm que dar exatamente os mesmos tempos.
"""
from __future__ import annotations

import heapq
from math import inf


class MapaBairro:
    def __init__(self, dados: dict):
        self.nome = dados.get("bairro", "")
        self.nos = {n["id"]: n for n in dados["nos"]}
        self.ids = list(self.nos)                      # ordem fixa dos vértices
        self.indice = {v: i for i, v in enumerate(self.ids)}
        self.arestas = [(a, b, float(m), bool(ac)) for a, b, m, ac in dados["arestas"]]
        for a, b, _, _ in self.arestas:
            if a not in self.nos or b not in self.nos:
                raise ValueError(f"aresta com vértice desconhecido: {a}-{b}")
        self._cache_fw: dict[bool, tuple[list, list]] = {}   # memoiza a matriz pronta

    # ------------------------------------------------------------------
    # Representações do grafo
    # ------------------------------------------------------------------
    def adjacencia(self, somente_acessiveis: bool = False) -> dict[str, list[tuple[str, float]]]:
        """Lista de adjacência (ruas de mão dupla para quem anda a pé)."""
        adj: dict[str, list[tuple[str, float]]] = {v: [] for v in self.ids}
        for a, b, minutos, acessivel in self.arestas:
            if somente_acessiveis and not acessivel:
                continue
            adj[a].append((b, minutos))
            adj[b].append((a, minutos))
        return adj

    # ------------------------------------------------------------------
    # Floyd-Warshall (programação dinâmica)
    # ------------------------------------------------------------------
    def floyd_warshall(self, somente_acessiveis: bool = False) -> tuple[list, list]:
        """Devolve (dist, proximo). Resultado memoizado por modo (comum/acessível)."""
        if somente_acessiveis in self._cache_fw:
            return self._cache_fw[somente_acessiveis]

        n = len(self.ids)
        dist = [[inf] * n for _ in range(n)]
        proximo: list[list[int | None]] = [[None] * n for _ in range(n)]
        for i in range(n):
            dist[i][i] = 0.0
            proximo[i][i] = i
        for a, b, minutos, acessivel in self.arestas:
            if somente_acessiveis and not acessivel:
                continue
            i, j = self.indice[a], self.indice[b]
            if minutos < dist[i][j]:                     # mantém o trecho mais rápido
                dist[i][j] = dist[j][i] = minutos
                proximo[i][j], proximo[j][i] = j, i

        for k in range(n):
            dk = dist[k]
            for i in range(n):
                dik = dist[i][k]
                if dik == inf:
                    continue
                di, pi = dist[i], proximo[i]
                for j in range(n):
                    novo = dik + dk[j]
                    if novo < di[j]:
                        di[j] = novo
                        pi[j] = pi[k]

        self._cache_fw[somente_acessiveis] = (dist, proximo)
        return dist, proximo

    def caminho(self, origem: str, destino: str, somente_acessiveis: bool = False) -> list[str]:
        _, proximo = self.floyd_warshall(somente_acessiveis)
        i, j = self.indice[origem], self.indice[destino]
        if proximo[i][j] is None:
            return []
        rota = [origem]
        while i != j:
            i = proximo[i][j]
            rota.append(self.ids[i])
        return rota

    def tempo(self, origem: str, destino: str, somente_acessiveis: bool = False) -> float:
        dist, _ = self.floyd_warshall(somente_acessiveis)
        return dist[self.indice[origem]][self.indice[destino]]

    # ------------------------------------------------------------------
    # Dijkstra (comparação e conferência)
    # ------------------------------------------------------------------
    def dijkstra(self, origem: str, somente_acessiveis: bool = False) -> dict[str, float]:
        adj = self.adjacencia(somente_acessiveis)
        dist = {v: inf for v in self.ids}
        dist[origem] = 0.0
        fila = [(0.0, origem)]
        while fila:
            d, u = heapq.heappop(fila)
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                if d + w < dist[v]:
                    dist[v] = d + w
                    heapq.heappush(fila, (dist[v], v))
        return dist

    # ------------------------------------------------------------------
    # Consulta usada pelo plano de ação
    # ------------------------------------------------------------------
    def atendimentos_proximos(self, origem: str, tipos: list[str], acessivel: bool = False,
                              limite: int = 3) -> list[dict]:
        """Locais de atendimento dos tipos pedidos, do mais perto ao mais longe."""
        if origem not in self.nos:
            raise ValueError(f"origem desconhecida: {origem}")
        achados = []
        for v, no in self.nos.items():
            if no.get("servico") not in tipos:
                continue
            minutos = self.tempo(origem, v, acessivel)
            if minutos == inf:
                continue                                  # sem rota (acessível) até lá
            achados.append({
                "id": v, "nome": no["nome"], "tipo": no["servico"],
                "horario": no.get("horario", ""), "minutos": int(minutos),
                "rota": [self.nos[p]["nome"] for p in self.caminho(origem, v, acessivel)],
            })
        achados.sort(key=lambda a: (a["minutos"], tipos.index(a["tipo"])))
        return achados[:limite]
