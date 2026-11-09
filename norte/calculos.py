"""
Estimativas de valores e resposta para "Preciso de advogado?".

São contas simples (não é programação dinâmica), mas dão ao cidadão o
tamanho do direito e alimentam o plano de ação. Tudo é ESTIMATIVA:
o valor exato depende dos documentos e é conferido no atendimento.
"""
from __future__ import annotations

SALARIO_MINIMO_2026 = 1621.00  # Decreto de dezembro de 2025, vigente desde 01/01/2026


def fgts_nao_depositado(salario: float, meses: int) -> dict:
    """FGTS de meses sem depósito (8% ao mês, Lei 8.036/1990, art. 15) e o
    reflexo na multa de 40% da demissão sem justa causa (art. 18, § 1º).
    Não inclui correção monetária nem juros."""
    depositos = round(0.08 * salario * meses, 2)
    multa = round(0.40 * depositos, 2)
    return {"depositos_faltantes": depositos, "reflexo_multa_40": multa,
            "total_estimado": round(depositos + multa, 2)}


def devolucao_em_dobro(valor_pago_indevido: float) -> float:
    """Repetição do indébito: o dobro do que pagou a mais (CDC, art. 42, parágrafo único).
    Sem correção e juros; não vale quando há 'engano justificável'."""
    return round(2 * valor_pago_indevido, 2)


def preciso_de_advogado(area: str, valor_causa: float | None,
                        salario_minimo: float = SALARIO_MINIMO_2026) -> str:
    """Resposta prática, com base na lei, para a pergunta mais comum do cidadão."""
    if area == "trabalho":
        return ("Não é obrigatório: na Justiça do Trabalho o empregado pode reclamar "
                "pessoalmente (CLT, art. 791). O sindicato e a Defensoria ajudam de graça.")
    if area == "violencia":
        return ("Não para começar: a medida protetiva pode ser pedida na delegacia, que envia "
                "o pedido ao juiz em até 48 horas (Lei 11.340/2006, art. 12, III). "
                "A Defensoria acompanha de graça.")
    if area == "transito":
        return ("Não: a defesa prévia e o recurso à JARI são pedidos administrativos que a "
                "própria pessoa pode fazer (CTB, arts. 281-A e 285).")
    if area == "familia":
        return ("Não para começar: a ação de alimentos pode ser pedida pessoalmente ao juiz "
                "(Lei 5.478/1968, art. 2º), e a Defensoria Pública atende de graça.")
    if area == "saude" and valor_causa is None:
        return ("Não para reclamar: a reclamação na ANS ou na ouvidoria do SUS é feita pela "
                "própria pessoa. Para ir à Justiça, até 20 salários mínimos dá para ir sozinho "
                "ao Juizado Especial Cível (Lei 9.099/1995, art. 9º); a Defensoria atende de graça.")
    if area == "inss":
        teto = 60 * salario_minimo
        if valor_causa is None or valor_causa <= teto:
            return (f"Não é obrigatório: causas contra o INSS de até 60 salários mínimos "
                    f"({moeda(teto)}) vão ao Juizado Especial Federal (Lei 10.259/2001, art. 3º), "
                    "onde a parte pode ter representante advogado ou não (art. 10). "
                    "A Defensoria Pública da União atende de graça.")
        return "Sim: acima de 60 salários mínimos procure a Defensoria Pública da União."
    if valor_causa is None:
        return ("Depende do valor: até 20 salários mínimos dá para ir sozinho ao Juizado "
                "Especial Cível (Lei 9.099/1995, art. 9º). A Defensoria atende quem não pode pagar.")
    vinte, quarenta = 20 * salario_minimo, 40 * salario_minimo
    if valor_causa <= vinte:
        return (f"Não: a causa (cerca de {moeda(valor_causa)}) está abaixo de 20 salários mínimos "
                f"({moeda(vinte)}), então você pode ir sozinho ao Juizado Especial Cível "
                "(Lei 9.099/1995, art. 9º).")
    if valor_causa <= quarenta:
        return (f"Sim: entre 20 e 40 salários mínimos o Juizado Especial Cível exige advogado "
                "(Lei 9.099/1995, art. 9º). A Defensoria Pública atende de graça.")
    return ("Sim: acima de 40 salários mínimos a causa vai à Justiça comum. Peça a Defensoria "
            "Pública e a gratuidade da justiça (CPC, art. 98).")


def moeda(valor: float) -> str:
    """Formata no padrão brasileiro: R$ 1.234,56."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")
