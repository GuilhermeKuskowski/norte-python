"""
Triagem do Norte: descobre qual das 10 áreas da vida é a do relato.

TÉCNICA: MEMOIZAÇÃO (programação dinâmica de cima para baixo).

O problema: o cidadão escreve do jeito dele ("recisão", "depozitado",
"benefisio", "sego") ou o texto vem de uma transcrição de áudio com erros.
Uma busca exata por palavras-chave falharia justamente com quem mais
precisa do Norte (baixa escolaridade, pressa, leitor de tela).

A solução: comparar cada palavra do relato com o vocabulário de cada área
usando a DISTÂNCIA DE EDIÇÃO (Levenshtein): o menor número de letras
inseridas, removidas ou trocadas para transformar uma palavra na outra.

    d(i, j) = distância entre os i primeiros caracteres de A
              e os j primeiros caracteres de B

    d(i, 0) = i            d(0, j) = j
    se A[i-1] == B[j-1]:   d(i, j) = d(i-1, j-1)
    senão:                 d(i, j) = 1 + min(d(i-1, j),     # remover
                                             d(i, j-1),     # inserir
                                             d(i-1, j-1))   # trocar

A recursão pura recalcula os mesmos subproblemas (i, j) muitas vezes:
custo exponencial, O(3^(m+n)). Com memoização, cada par (i, j) é
calculado uma vez só: O(m·n) de tempo e de memória.

Há ainda uma SEGUNDA camada de memoização: o resultado de cada par de
palavras (palavra do relato, palavra-chave) fica guardado. Como os relatos
repetem muito as mesmas palavras ("inss", "nome", "demitida"), a partir do
segundo atendimento quase tudo vem direto do cache.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

# Palavras muito comuns que não ajudam a descobrir a área.
STOPWORDS = {
    "que", "nao", "uma", "um", "uns", "umas", "com", "sem", "por", "para", "pra",
    "pro", "dos", "das", "nos", "nas", "meu", "minha", "meus", "minhas", "seu",
    "sua", "ele", "ela", "eles", "elas", "eu", "voce", "foi", "sou", "era", "esta",
    "estava", "estou", "tem", "tinha", "ter", "mas", "como", "mais", "muito", "isso",
    "esse", "essa", "este", "ainda", "acho", "depois", "antes", "quando", "onde",
    "porque", "tambem", "entao", "ja", "mesmo", "perto", "dizendo", "disse", "fala",
    "nunca", "sempre", "varios", "varias", "anos", "mes", "dia", "dias", "recebi",
}

TAMANHO_MAXIMO_PALAVRA = 30  # protege a recursão contra "palavras" absurdas


# --------------------------------------------------------------------------
# Normalização do texto
# --------------------------------------------------------------------------
def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e só com letras, números e espaços."""
    sem_acento = unicodedata.normalize("NFKD", texto.lower())
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", sem_acento)


def tokenizar(texto: str) -> list[str]:
    """Quebra o relato em palavras úteis (sem repetição, na ordem em que aparecem)."""
    vistas: dict[str, None] = {}
    for palavra in normalizar(texto).split():
        if len(palavra) >= 3 and palavra not in STOPWORDS:
            vistas.setdefault(palavra[:TAMANHO_MAXIMO_PALAVRA], None)
    return list(vistas)


# --------------------------------------------------------------------------
# Distância de edição: três versões (para comparar eficiência)
# --------------------------------------------------------------------------
def distancia_ingenua(a: str, b: str) -> int:
    """Recursão pura, SEM memoização. Custo O(3^(m+n)): só para comparação."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    if a[-1] == b[-1]:
        return distancia_ingenua(a[:-1], b[:-1])
    return 1 + min(
        distancia_ingenua(a[:-1], b),        # remover
        distancia_ingenua(a, b[:-1]),        # inserir
        distancia_ingenua(a[:-1], b[:-1]),   # trocar
    )


def distancia_memo(a: str, b: str) -> int:
    """Mesma recursão, COM memoização (top-down). Custo O(m·n)."""

    @lru_cache(maxsize=None)
    def d(i: int, j: int) -> int:
        if i == 0:
            return j
        if j == 0:
            return i
        if a[i - 1] == b[j - 1]:
            return d(i - 1, j - 1)
        return 1 + min(d(i - 1, j), d(i, j - 1), d(i - 1, j - 1))

    return d(len(a), len(b))


def distancia_tabulada(a: str, b: str) -> int:
    """Versão de baixo para cima (tabulação), guardando só 2 linhas da tabela.

    Mesmo tempo O(m·n), mas memória O(n) e sem recursão. Serve para conferir
    a versão memoizada nos testes e para comparar as duas abordagens.
    """
    anterior = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        atual = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                atual[j] = anterior[j - 1]
            else:
                atual[j] = 1 + min(anterior[j], atual[j - 1], anterior[j - 1])
        anterior = atual
    return anterior[len(b)]


@lru_cache(maxsize=200_000)
def distancia(a: str, b: str) -> int:
    """Segunda camada de memoização: cache por PAR de palavras."""
    return distancia_memo(a, b)


def tolerancia(palavra: str) -> int:
    """Quantos erros aceitamos: siglas e palavras de 3 letras precisam bater exatamente."""
    if len(palavra) <= 3:
        return 0
    if len(palavra) <= 8:
        return 1
    return 2


def combina(palavra: str, chave: str) -> bool:
    tol = tolerancia(chave)
    if abs(len(palavra) - len(chave)) > tol:   # poda barata antes da PD
        return False
    return distancia(palavra, chave) <= tol


# --------------------------------------------------------------------------
# Classificação do relato
# --------------------------------------------------------------------------
def classificar(relato: str, areas: dict) -> list[dict]:
    """Devolve as áreas em ordem de pontuação, com as palavras reconhecidas.

    Cada palavra do relato pontua no máximo uma vez por área (na palavra-chave
    de maior peso que ela reconhece), e cada palavra-chave também só conta uma
    vez. Assim "filho" não soma de novo por parecer com "filha" e "filhos".
    """
    palavras = tokenizar(relato)
    resultado = []
    for area_id, area in areas.items():
        pontos = 0
        achadas = []
        usadas: set[str] = set()
        for palavra in palavras:
            candidatas = [(peso, chave) for chave, peso in area["palavras"].items()
                          if chave not in usadas and combina(palavra, chave)]
            if not candidatas:
                continue
            peso, chave = max(candidatas, key=lambda pc: (pc[0], pc[1] == palavra))
            usadas.add(chave)
            pontos += peso
            achadas.append(palavra if palavra == chave else f"{palavra}→{chave}")
        if pontos > 0:
            resultado.append({"area": area_id, "nome": area["nome"],
                              "pontos": pontos, "palavras": achadas})
    resultado.sort(key=lambda r: (-r["pontos"], r["area"]))
    return resultado


def areas_do_caso(relato: str, areas: dict, fracao_minima: float = 0.6) -> list[dict]:
    """Áreas que entram no plano: a melhor e as que chegam perto dela.

    Um relato pode tocar mais de uma área (ex.: caução do aluguel + multa).
    Exigimos pelo menos 3 pontos para evitar falso positivo por uma palavra solta.
    """
    ranking = classificar(relato, areas)
    if not ranking:
        return []
    melhor = ranking[0]["pontos"]
    return [r for r in ranking if r["pontos"] >= max(3, fracao_minima * melhor)]


def estatisticas_cache() -> dict:
    info = distancia.cache_info()
    total = info.hits + info.misses
    return {"acertos": info.hits, "calculos": info.misses,
            "taxa_acerto": (info.hits / total) if total else 0.0}
