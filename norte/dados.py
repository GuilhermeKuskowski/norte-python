"""Leitura dos arquivos JSON da pasta dados/ (base do protótipo)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"


def _ler(nome: str) -> dict:
    with open(PASTA_DADOS / nome, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    dados.pop("_sobre", None)          # comentário do arquivo, não é dado
    return dados


@lru_cache(maxsize=None)
def areas() -> dict:
    return _ler("areas.json")


@lru_cache(maxsize=None)
def leis() -> dict:
    todas = _ler("leis.json")
    # O Norte só cita norma vigente (marcação 'revogada' do acervo ctresb/leis).
    return {k: v for k, v in todas.items() if not v.get("revogada", False)}


@lru_cache(maxsize=None)
def bairro() -> dict:
    return _ler("bairro.json")


def casos_exemplo() -> dict:
    return _ler("casos_exemplo.json")
