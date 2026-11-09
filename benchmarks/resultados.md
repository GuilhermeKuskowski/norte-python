# Resultados de eficiência – Norte (Programação Dinâmica)

Python 3.13.18 · tempos em milissegundos · dependem do computador.

## 1. Memoização – distância de edição (triagem)

Pares de palavras sem letras em comum (pior caso da recursão).

| Tamanho (m = n) | Chamadas recursivas sem memo | Subproblemas com memo (m+1)·(n+1) | Tempo sem memo (ms) | Tempo com memo (ms) | Tempo tabulado (ms) |
|---|---|---|---|---|---|
| 3 | 94 | 16 | 0,014 | 0,007 | 0,002 |
| 5 | 2.524 | 36 | 0,223 | 0,016 | 0,009 |
| 7 | 72.958 | 64 | 7,121 | 0,024 | 0,008 |
| 8 | 398.593 | 81 | 59,157 | 0,031 | 0,009 |
| 9 | 2.193.844 | 100 | 197,023 | 0,045 | 0,011 |
| 10 | inviável | 121 | inviável | 0,057 | 0,014 |
| 12 | inviável | 169 | inviável | 0,064 | 0,018 |
| 20 | inviável | 441 | inviável | 0,239 | 0,049 |

**Cache por par de palavras (2ª camada de memoização)** – 500 relatos simulados, montados com o vocabulário das 10 áreas e erros de digitação aleatórios:

| Versão | Tempo total (ms) | Por relato (ms) |
|---|---|---|
| Sem cache de pares | 8.718,608 | 17,437 |
| Com cache de pares | 3.329,833 | 6,660 |

Reaproveitamento do cache: 66,3% das comparações (225.406 vindas do cache, 114.702 calculadas). Ganho: 2,6x mais rápido.

## 2. Tabulação – mochila 0/1 (plano da semana)

Capacidade: 10 horas (20 blocos de 30 min). Ações com 1 a 6 blocos e benefício de 1 a 30.

| Nº de ações (n) | Combinações testadas pela força bruta (2^n) | Células da tabela (n+1)·(C+1) | Força bruta (ms) | Tabulação (ms) | Mesmo resultado? |
|---|---|---|---|---|---|
| 5 | 32 | 126 | 0,033 | 0,025 | sim |
| 10 | 1.024 | 231 | 0,620 | 0,026 | sim |
| 14 | 16.384 | 315 | 9,279 | 0,057 | sim |
| 16 | 65.536 | 357 | 34,027 | 0,036 | sim |
| 18 | 262.144 | 399 | 133,269 | 0,053 | sim |
| 20 | 1.048.576 | 441 | inviável | 0,046 | – |
| 40 | 1.099.511.627.776 | 861 | inviável | 0,087 | – |
| 100 | 1.267.650.600.228.229.401.496.703.205.376 | 2.121 | inviável | 0,236 | – |

## 3. Grafos – menor caminho até o atendimento

**a) Por que não testar todos os caminhos:** bairro em grade, de uma esquina à oposta.

| Grade | Vértices | Força bruta (ms) | Floyd-Warshall (ms) | Mesmo resultado? |
|---|---|---|---|---|
| 3x3 | 9 | 0,040 | 0,053 | sim |
| 4x4 | 16 | 0,304 | 0,169 | sim |
| 5x5 | 25 | 20,319 | 0,504 | sim |
| 6x6 | 36 | inviável (mais de 1 milhão de caminhos) | 1,290 | – |

**b) Floyd-Warshall (calcula tudo uma vez) x Dijkstra (calcula a cada atendimento):** 1.000 atendimentos, cada um saindo de uma esquina aleatória.

| Grade | Vértices | FW: pré-cálculo O(V³) (ms) | FW: 1.000 consultas O(1) (ms) | FW total (ms) | Dijkstra: 1.000 execuções (ms) | Mais rápido |
|---|---|---|---|---|---|---|
| 5x5 | 25 | 0,477 | 0,144 | 0,621 | 18,579 | Floyd-Warshall |
| 8x8 | 64 | 6,333 | 0,158 | 6,491 | 55,292 | Floyd-Warshall |
| 10x10 | 100 | 22,630 | 0,155 | 22,785 | 93,941 | Floyd-Warshall |
| 14x14 | 196 | 159,748 | 0,296 | 160,044 | 188,776 | Floyd-Warshall |
| 20x20 | 400 | 1.635,080 | 0,440 | 1.635,520 | 449,766 | Dijkstra |

No mapa do protótipo (29 vértices, 36 trechos) o pré-cálculo leva 0,930 ms e fica guardado; cada consulta depois é imediata.

