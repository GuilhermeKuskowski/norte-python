"""
Norte – Programação Dinâmica (GS 2026.2 · CitizenTech · FIAP)

Como usar:
    python main.py                      # menu interativo
    python main.py --demo               # roda os 6 casos das personas
    python main.py --caso marcia        # roda um caso de exemplo
    python main.py --demo --hoje 2026-11-19   # fixa a data "de hoje" (resultado reproduzível)
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from norte import dados, triagem
from norte.orientador import formatar_plano, mapa_padrao, orientar

if hasattr(sys.stdout, "reconfigure"):          # acentos no terminal do Windows
    sys.stdout.reconfigure(encoding="utf-8")


def rodar_caso(nome: str, hoje: date) -> None:
    casos = dados.casos_exemplo()
    if nome not in casos:
        print(f"Caso '{nome}' não existe. Opções: {', '.join(casos)}")
        return
    print(formatar_plano(orientar(casos[nome], hoje)))
    print()


def perguntar(texto: str, padrao: str = "") -> str:
    resposta = input(f"{texto}{f' [{padrao}]' if padrao else ''}: ").strip()
    return resposta or padrao


def modo_interativo(hoje: date) -> None:
    print("\nNORTE – conte o seu problema com as suas palavras.")
    print("(Não use seu nome, CPF ou endereço: o Norte não precisa disso.)\n")
    relato = perguntar("O que aconteceu")
    if not relato:
        print("Nada foi digitado.")
        return

    caso: dict = {"relato": relato, "datas": {}, "valores": {}}
    achadas = triagem.areas_do_caso(relato, dados.areas())
    if not achadas:
        print("\nNão reconheci o assunto. Escolha uma área:")
        ids = list(dados.areas())
        for i, area_id in enumerate(ids, 1):
            print(f"  {i:2}. {dados.areas()[area_id]['nome']}")
        escolha = perguntar("Número da área", "10")
        caso["area"] = ids[int(escolha) - 1] if escolha.isdigit() and 1 <= int(escolha) <= len(ids) else ids[-1]
        area_ids = [caso["area"]]
    else:
        area_ids = [a["area"] for a in achadas]
        print("\nEntendi que o assunto é: " + "; ".join(a["nome"] for a in achadas))

    # Perguntas simples, só das datas e valores que as regras dessas áreas usam.
    perguntas_data = {
        "data_demissao": "Data da demissão (AAAA-MM-DD, Enter se não souber)",
        "data_negativa_inss": "Data em que soube da negativa do INSS (AAAA-MM-DD)",
        "data_compra": "Data em que recebeu a compra (AAAA-MM-DD)",
        "data_notificacao_multa": "Data de expedição da notificação da multa (AAAA-MM-DD)",
    }
    usadas = {r["prazo"]["a_partir_de"] for a in area_ids
              for r in dados.areas()[a]["acoes"] if r["prazo"]}
    for chave, texto in perguntas_data.items():
        if chave in usadas:
            valor = perguntar(texto)
            try:
                date.fromisoformat(valor)
                caso["datas"][chave] = valor
            except ValueError:
                pass
    if "trabalho" in area_ids:
        salario = perguntar("Último salário (ex.: 1850)", "")
        meses = perguntar("Quantos meses de FGTS faltaram (Enter se não souber)", "")
        if salario.replace(".", "", 1).isdigit() and meses.isdigit():
            caso["valores"].update(salario=float(salario), meses_sem_fgts=int(meses))
    if "consumo" in area_ids:
        pago = perguntar("Quanto pagou de cobrança indevida (Enter se nada)", "")
        if pago.replace(".", "", 1).isdigit():
            caso["valores"]["valor_pago_indevido"] = float(pago)

    caso["perfil_prioritario"] = []
    if perguntar("Você tem 60 anos ou mais? (s/n)", "n").lower().startswith("s"):
        caso["perfil_prioritario"].append("idoso")
    if perguntar("Você é pessoa com deficiência? (s/n)", "n").lower().startswith("s"):
        caso["perfil_prioritario"].append("pcd")
    caso["acessivel"] = perguntar("Precisa de rota acessível, sem escadas? (s/n)",
                                  "s" if caso["perfil_prioritario"] else "n").lower().startswith("s")
    horas = perguntar("Quantas horas livres você tem nesta semana", "3")
    caso["horas_disponiveis"] = float(horas.replace(",", ".")) if horas.replace(",", ".").replace(".", "", 1).isdigit() else 3

    mapa = mapa_padrao()
    print("\nDe onde você vai sair? (pontos do mapa simulado)")
    pontos = [v for v, no in mapa.nos.items() if "servico" not in no]
    for i, v in enumerate(pontos, 1):
        print(f"  {i:2}. {mapa.nos[v]['nome']}")
    escolha = perguntar("Número do ponto", "1")
    caso["origem"] = pontos[int(escolha) - 1] if escolha.isdigit() and 1 <= int(escolha) <= len(pontos) else pontos[0]

    print()
    print(formatar_plano(orientar(caso, hoje, mapa)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Norte – algoritmos de Programação Dinâmica")
    parser.add_argument("--demo", action="store_true", help="roda todos os casos de exemplo")
    parser.add_argument("--caso", help="roda um caso de exemplo (marcia, jose, juliana, rafael, ana_paula, carlos)")
    parser.add_argument("--hoje", help="data de referência AAAA-MM-DD (padrão: data do computador)")
    args = parser.parse_args()
    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()

    if args.demo:
        for nome in dados.casos_exemplo():
            rodar_caso(nome, hoje)
    elif args.caso:
        rodar_caso(args.caso, hoje)
    else:
        modo_interativo(hoje)


if __name__ == "__main__":
    main()
