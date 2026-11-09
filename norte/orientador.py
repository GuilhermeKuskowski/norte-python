"""
Orientador: junta as três partes em um Plano de Ação.

    relato ──► [triagem: memoização] ──► áreas do caso
                                            │
          regras da curadoria + prazos ◄────┘
                    │
                    ▼
    [plano da semana: tabulação / mochila] ──► o que fazer agora e depois
                    │
                    ▼
    [atendimento gratuito: grafo / Floyd-Warshall] ──► onde ir e por qual rota
"""
from __future__ import annotations

import textwrap
from datetime import date

from . import calculos, dados, plano, triagem
from .atendimento import MapaBairro
from .prazos import PESO_SEMAFORO, calcular_prazo

AVISO = ("O Norte dá orientação, não consultoria jurídica. Confirme sempre no atendimento "
         "gratuito indicado. Valores e prazos são estimativas.")

_mapa_padrao: MapaBairro | None = None


def mapa_padrao() -> MapaBairro:
    """O mapa é criado uma vez só e reaproveitado (a matriz do Floyd-Warshall fica guardada)."""
    global _mapa_padrao
    if _mapa_padrao is None:
        _mapa_padrao = MapaBairro(dados.bairro())
    return _mapa_padrao


def _estimativas(area_ids: list[str], valores: dict) -> list[dict]:
    est = []
    if "trabalho" in area_ids and valores.get("salario") and valores.get("meses_sem_fgts"):
        r = calculos.fgts_nao_depositado(valores["salario"], valores["meses_sem_fgts"])
        est.append({"area": "trabalho", "valor": r["total_estimado"],
                    "texto": (f"FGTS de {valores['meses_sem_fgts']} meses sem depósito: "
                              f"{calculos.moeda(r['depositos_faltantes'])} + reflexo na multa de 40%: "
                              f"{calculos.moeda(r['reflexo_multa_40'])} = "
                              f"{calculos.moeda(r['total_estimado'])} (Lei 8.036/1990, arts. 15 e 18, § 1º)")})
    if "consumo" in area_ids and valores.get("valor_pago_indevido"):
        dobro = calculos.devolucao_em_dobro(valores["valor_pago_indevido"])
        est.append({"area": "consumo", "valor": dobro,
                    "texto": (f"Devolução em dobro do que pagou indevidamente: "
                              f"{calculos.moeda(valores['valor_pago_indevido'])} x 2 = "
                              f"{calculos.moeda(dobro)} (CDC, art. 42, parágrafo único)")})
    return est


def orientar(caso: dict, hoje: date | None = None, mapa: MapaBairro | None = None) -> dict:
    hoje = hoje or date.today()
    mapa = mapa or mapa_padrao()
    todas_areas, todas_leis = dados.areas(), dados.leis()

    # 1) Triagem (memoização)
    encontradas = triagem.areas_do_caso(caso["relato"], todas_areas)
    if caso.get("area"):                                   # pessoa escolheu na lista
        encontradas = [{"area": caso["area"], "nome": todas_areas[caso["area"]]["nome"],
                        "pontos": 0, "palavras": ["escolhida pela pessoa"]}]
    area_ids = [a["area"] for a in encontradas]
    perfil = set(caso.get("perfil_prioritario", []))          # {"idoso"}, {"pcd"} ou vazio
    if perfil and area_ids and "idosos_pcd" not in area_ids:
        area_ids.append("idosos_pcd")
        encontradas.append({"area": "idosos_pcd", "nome": todas_areas["idosos_pcd"]["nome"],
                            "pontos": 0, "palavras": ["resposta da pessoa: " + " e ".join(
                                {"idoso": "pessoa idosa", "pcd": "pessoa com deficiência"}[x]
                                for x in sorted(perfil))]})

    if not area_ids:
        return {"caso": caso, "hoje": hoje, "areas": [], "sem_area": True,
                "opcoes": {k: v["nome"] for k, v in todas_areas.items()}}

    # 2) Ações da curadoria + prazos + benefício
    acoes = []
    for area_id in area_ids:
        for regra in todas_areas[area_id]["acoes"]:
            lei = todas_leis.get(regra["lei"])
            if lei is None:                                # norma revogada: não cita
                continue
            if regra.get("so_para") and regra["so_para"] not in perfil:
                continue                                   # ex.: gratuidade só para 65+
            prazo = calcular_prazo(regra["prazo"], caso.get("datas", {}), hoje)
            acoes.append({**regra, "area": area_id, "prazo": prazo,
                          "beneficio": regra["impacto"] * PESO_SEMAFORO[prazo.semaforo],
                          "lei_nome": lei["nome"], "fonte": lei["fonte"]})

    # 3) Plano da semana (tabulação / mochila)
    semana = plano.montar_semana(acoes, caso.get("horas_disponiveis", 2))

    # 4) Valores e "preciso de advogado?"
    valores = caso.get("valores", {})
    estimativas = _estimativas(area_ids, valores)
    advogado = {}
    for posicao, area_id in enumerate(area_ids):
        if area_id == "idosos_pcd":
            continue
        # O valor da causa informado vale para o assunto principal do relato.
        valor_causa = valores.get("valor_causa") if posicao == 0 else None
        if valor_causa is None:
            valor_causa = next((e["valor"] for e in estimativas if e["area"] == area_id), None)
        advogado[area_id] = calculos.preciso_de_advogado(area_id, valor_causa)

    # 5) Atendimento gratuito (grafo / Floyd-Warshall)
    atendimento = {a: mapa.atendimentos_proximos(caso["origem"], todas_areas[a]["orgaos"],
                                                 caso.get("acessivel", False))
                   for a in area_ids}

    # 6) Checklist: documentos das ações desta semana, sem repetir
    checklist: dict[str, None] = {}
    for acao in semana["esta_semana"]:
        for doc in acao["documentos"]:
            checklist.setdefault(doc, None)

    return {
        "caso": caso, "hoje": hoje, "areas": encontradas, "sem_area": False,
        "modo_discreto": any(todas_areas[a].get("modo_discreto") for a in area_ids),
        "semana": semana, "estimativas": estimativas, "advogado": advogado,
        "atendimento": atendimento, "checklist": list(checklist),
        "nomes_areas": {a: todas_areas[a]["nome"] for a in area_ids},
    }


# --------------------------------------------------------------------------
# Texto do plano (linguagem simples)
# --------------------------------------------------------------------------
def _quebrar(texto: str, recuo: str = "   ") -> str:
    return textwrap.fill(texto, width=88, initial_indent=recuo, subsequent_indent=recuo + "  ")


def _linha_acao(n: int, acao: dict) -> str:
    p = acao["prazo"]
    if p.data_limite:
        quando = f"até {p.data_limite.strftime('%d/%m/%Y')} ({p.dias_restantes} dias)"
        if p.dias_restantes < 0:
            quando = f"venceu em {p.data_limite.strftime('%d/%m/%Y')}"
    else:
        quando = p.observacao or "sem prazo curto"
    linhas = [_quebrar(f"{n}. {acao['texto']}", "  "),
              _quebrar(f"[{p.rotulo}] {quando} · cerca de {acao['duracao_min']} min"),
              _quebrar(f"Lei: {acao['lei_nome']}, {acao['artigo']} – {acao['fonte']}")]
    return "\n".join(linhas)


def formatar_plano(p: dict) -> str:
    caso = p["caso"]
    saida = []
    titulo = "NORTE · PLANO DE AÇÃO"
    saida.append("=" * 88)
    saida.append(f"{titulo}{('· ' + caso['persona']).rjust(88 - len(titulo))}" if caso.get("persona") else titulo)
    saida.append("=" * 88)
    saida.append(_quebrar(f"Relato: \"{caso['relato']}\"", ""))

    if p["sem_area"]:
        saida.append("\nNão consegui identificar o assunto. Escolha uma das 10 áreas:")
        for i, nome in enumerate(p["opcoes"].values(), 1):
            saida.append(f"  {i:2}. {nome}")
        return "\n".join(saida)

    if p["modo_discreto"]:
        saida.append("\n[MODO DISCRETO ATIVO – botão de saída rápida disponível no app]")

    saida.append("\n1) SEU ASSUNTO (triagem)")
    for a in p["areas"]:
        saida.append(_quebrar(f"• {a['nome']} – reconheci: {', '.join(a['palavras'])}"))

    if p["estimativas"]:
        saida.append("\n2) QUANTO PODE ESTAR EM JOGO (estimativa)")
        for e in p["estimativas"]:
            saida.append(_quebrar("• " + e["texto"]))
    elif caso.get("valores", {}).get("valor_causa"):
        saida.append("\n2) QUANTO PODE ESTAR EM JOGO")
        saida.append(f"   • Valor informado pela pessoa: {calculos.moeda(caso['valores']['valor_causa'])}")
    else:
        saida.append("\n2) QUANTO PODE ESTAR EM JOGO\n   • Sem valor informado para estimar.")

    s = p["semana"]
    horas = caso.get("horas_disponiveis", 2)
    saida.append(f"\n3) O QUE FAZER ESTA SEMANA (você tem {horas:g} h; plano usa "
                 f"{s['minutos_usados'] // 60} h {s['minutos_usados'] % 60:02d} min)")
    for n, acao in enumerate(s["esta_semana"], 1):
        saida.append(_linha_acao(n, acao))
    if s["depois"]:
        saida.append("\n   Para as próximas semanas:")
        for n, acao in enumerate(s["depois"], len(s["esta_semana"]) + 1):
            saida.append(_linha_acao(n, acao))

    saida.append("\n4) PRECISO DE ADVOGADO?")
    for area_id, resposta in p["advogado"].items():
        saida.append(_quebrar(f"• {p['nomes_areas'][area_id]}: {resposta}"))

    modo = "rota ACESSÍVEL, sem escadas nem trechos ruins" if caso.get("acessivel") else "rota mais rápida a pé"
    saida.append(f"\n5) ONDE BUSCAR ATENDIMENTO GRATUITO – {modo}")
    for area_id, locais in p["atendimento"].items():
        saida.append(f"   {p['nomes_areas'][area_id]}:")
        if not locais:
            saida.append("     – nenhum local alcançável pelo mapa; use os canais por telefone ou internet.")
        for loc in locais:
            saida.append(_quebrar(f"• {loc['nome']} – {loc['minutos']} min a pé · {loc['horario']}", "     "))
            saida.append(_quebrar("rota: " + " → ".join(loc["rota"]), "       "))

    saida.append("\n6) CHECKLIST DE DOCUMENTOS (para as ações desta semana)")
    for doc in p["checklist"] or ["Documento com foto"]:
        saida.append(f"   [ ] {doc}")

    saida.append("\n" + _quebrar(AVISO, ""))
    return "\n".join(saida)
