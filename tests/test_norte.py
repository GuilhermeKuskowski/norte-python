"""
Testes de funcionamento correto (biblioteca padrão unittest).

Rodar a partir da pasta do projeto:
    python -m unittest discover -s tests -v
"""
import random
import string
import sys
import unittest
from datetime import date
from math import inf
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from norte import calculos, dados, plano, prazos, triagem          # noqa: E402
from norte.atendimento import MapaBairro                            # noqa: E402
from norte.orientador import orientar                               # noqa: E402

HOJE = date(2026, 11, 19)


class TestTriagemMemoizacao(unittest.TestCase):
    def test_valores_conhecidos(self):
        self.assertEqual(triagem.distancia_memo("kitten", "sitting"), 3)
        self.assertEqual(triagem.distancia_memo("recisao", "rescisao"), 1)
        self.assertEqual(triagem.distancia_memo("", "inss"), 4)
        self.assertEqual(triagem.distancia_memo("fgts", "fgts"), 0)

    def test_tres_versoes_concordam(self):
        rnd = random.Random(42)
        for _ in range(300):
            a = "".join(rnd.choices("abcde", k=rnd.randint(0, 7)))
            b = "".join(rnd.choices("abcde", k=rnd.randint(0, 7)))
            esperado = triagem.distancia_ingenua(a, b)
            self.assertEqual(triagem.distancia_memo(a, b), esperado, (a, b))
            self.assertEqual(triagem.distancia_tabulada(a, b), esperado, (a, b))

    def test_normalizacao_tira_acentos(self):
        self.assertEqual(triagem.tokenizar("Rescisão, Benefício!"), ["rescisao", "beneficio"])

    def test_personas_caem_na_area_certa(self):
        esperado = {"marcia": ["trabalho"], "jose": ["inss"], "juliana": ["consumo"],
                    "rafael": ["moradia", "transito"], "ana_paula": ["familia"], "carlos": ["saude"]}
        for nome, caso in dados.casos_exemplo().items():
            achadas = [a["area"] for a in triagem.areas_do_caso(caso["relato"], dados.areas())]
            self.assertEqual(achadas, esperado[nome], nome)

    def test_erros_de_digitacao(self):
        areas = dados.areas()
        self.assertEqual(triagem.areas_do_caso("fui demitida e nao recebi a recisão", areas)[0]["area"], "trabalho")
        self.assertEqual(triagem.areas_do_caso("multaram meu carro no radar", areas)[0]["area"], "transito")
        self.assertEqual(triagem.areas_do_caso("meu companheiro me agrediu, tenho medo", areas)[0]["area"], "violencia")

    def test_relato_sem_assunto(self):
        self.assertEqual(triagem.areas_do_caso("bom dia tudo bem", dados.areas()), [])


class TestPlanoTabulacao(unittest.TestCase):
    def test_exemplo_classico(self):
        melhor, idx = plano.mochila_tabulada([1, 3, 4, 5], [1, 4, 5, 7], 7)
        self.assertEqual(melhor, 9)
        self.assertEqual(sorted(idx), [1, 2])

    def test_igual_a_forca_bruta(self):
        rnd = random.Random(7)
        for _ in range(200):
            n = rnd.randint(0, 10)
            custos = [rnd.randint(1, 6) for _ in range(n)]
            benef = [rnd.randint(1, 30) for _ in range(n)]
            cap = rnd.randint(0, 20)
            melhor, idx = plano.mochila_tabulada(custos, benef, cap)
            self.assertEqual(melhor, plano.mochila_forca_bruta(custos, benef, cap)[0])
            self.assertLessEqual(sum(custos[i] for i in idx), cap)          # cabe no tempo
            self.assertEqual(sum(benef[i] for i in idx), melhor)             # reconstrução certa

    def test_semana_respeita_horas(self):
        for caso in dados.casos_exemplo().values():
            p = orientar(caso, HOJE)
            self.assertLessEqual(p["semana"]["minutos_usados"], caso["horas_disponiveis"] * 60)

    def test_prazo_vermelho_entra_na_semana(self):
        p = orientar(dados.casos_exemplo()["jose"], HOJE)
        ids = [a["id"] for a in p["semana"]["esta_semana"]]
        self.assertEqual(ids[0], "I3")         # recurso ao INSS vence em 6 dias: primeiro da lista


class TestAtendimentoGrafos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapa = MapaBairro(dados.bairro())

    def test_floyd_warshall_igual_dijkstra(self):
        for acessivel in (False, True):
            dist, _ = self.mapa.floyd_warshall(acessivel)
            for origem in self.mapa.ids:
                dj = self.mapa.dijkstra(origem, acessivel)
                for destino in self.mapa.ids:
                    i, j = self.mapa.indice[origem], self.mapa.indice[destino]
                    self.assertEqual(dist[i][j], dj[destino], (origem, destino, acessivel))

    def test_caminho_soma_o_tempo(self):
        pesos = {}
        for a, b, m, _ in self.mapa.arestas:
            pesos[(a, b)] = pesos[(b, a)] = m
        rota = self.mapa.caminho("P1", "S_DEF")
        self.assertEqual(rota[0], "P1")
        self.assertEqual(rota[-1], "S_DEF")
        self.assertEqual(sum(pesos[(rota[k], rota[k + 1])] for k in range(len(rota) - 1)),
                         self.mapa.tempo("P1", "S_DEF"))

    def test_rota_acessivel_evita_escada(self):
        inacessiveis = {frozenset((a, b)) for a, b, _, ac in self.mapa.arestas if not ac}
        rota_comum = self.mapa.caminho("P1", "S_DEF")
        rota_acess = self.mapa.caminho("P1", "S_DEF", somente_acessiveis=True)
        self.assertIn("P4", rota_comum)                    # a mais rápida passa pela escadaria
        for k in range(len(rota_acess) - 1):
            self.assertNotIn(frozenset((rota_acess[k], rota_acess[k + 1])), inacessiveis)
        self.assertGreater(self.mapa.tempo("P1", "S_DEF", True), self.mapa.tempo("P1", "S_DEF"))

    def test_ranking_do_mais_perto(self):
        locais = self.mapa.atendimentos_proximos("P12", ["cras"], acessivel=True)
        self.assertEqual([l["id"] for l in locais], ["S_CRAS1", "S_CRAS2"])
        self.assertTrue(all(l["minutos"] < inf for l in locais))


class TestApoio(unittest.TestCase):
    def test_semaforo(self):
        regra = {"quantidade": 30, "unidade": "dias", "a_partir_de": "d"}
        self.assertEqual(prazos.calcular_prazo(regra, {"d": "2026-11-01"}, HOJE).semaforo, "vermelho")
        self.assertEqual(prazos.calcular_prazo(regra, {"d": "2026-10-01"}, HOJE).semaforo, "vencido")
        self.assertEqual(prazos.calcular_prazo(regra, {}, HOJE).semaforo, "a_confirmar")
        self.assertEqual(prazos.calcular_prazo(None, {}, HOJE).semaforo, "sem_prazo")

    def test_ano_bissexto(self):
        self.assertEqual(prazos.somar_periodo(date(2028, 2, 29), 2, "anos"), date(2030, 2, 28))

    def test_calculos(self):
        r = calculos.fgts_nao_depositado(1850, 7)
        self.assertAlmostEqual(r["depositos_faltantes"], 1036.00)
        self.assertAlmostEqual(r["reflexo_multa_40"], 414.40)
        self.assertEqual(calculos.devolucao_em_dobro(380), 760)
        self.assertEqual(calculos.moeda(32420), "R$ 32.420,00")

    def test_preciso_de_advogado(self):
        self.assertTrue(calculos.preciso_de_advogado("consumo", 5000).startswith("Não"))
        self.assertTrue(calculos.preciso_de_advogado("consumo", 40000).startswith("Sim"))
        self.assertTrue(calculos.preciso_de_advogado("moradia", 100000).startswith("Sim"))

    def test_so_cita_lei_vigente(self):
        leis = dados.leis()
        for area in dados.areas().values():
            for acao in area["acoes"]:
                self.assertIn(acao["lei"], leis, acao["id"])
                self.assertTrue(leis[acao["lei"]]["fonte"].startswith("https://"))

    def test_gratuidade_65_mais_nao_aparece_para_pcd_jovem(self):
        p = orientar(dados.casos_exemplo()["carlos"], HOJE)
        ids = [a["id"] for a in p["semana"]["esta_semana"] + p["semana"]["depois"]]
        self.assertNotIn("P3", ids)
        self.assertIn("P1", ids)


if __name__ == "__main__":
    unittest.main()
