import unittest

from cinedata_agent.resposta import formatar_celula, redigir


class TestResposta(unittest.TestCase):
    def test_ano_nao_ganha_separador_de_milhar(self):
        self.assertEqual(formatar_celula("ano_lancamento", 2022), "2022")

    def test_receita_em_reais(self):
        texto = formatar_celula("receita_brl", 12390136500.54)
        self.assertTrue(texto.startswith("R$ "))
        self.assertIn("12.390.136.500,54", texto)

    def test_ranking_cita_o_primeiro_e_nao_inventa_linha(self):
        texto = redigir(
            "Top receita",
            {
                "sql": "SELECT titulo FROM dim_movies ORDER BY receita_brl DESC",
                "colunas": ["titulo", "ano_lancamento", "receita_brl"],
                "linhas": [
                    {"titulo": "Avatar: The Way Of Water", "ano_lancamento": 2022, "receita_brl": 10.5}
                ],
            },
        )
        self.assertIn("Avatar: The Way Of Water (2022)", texto)
        self.assertIn("R$ 10,50", texto)

    def test_lista_por_ano_nao_trata_o_primeiro_como_campeao(self):
        texto = redigir(
            "Nota média por ano",
            {
                "sql": "SELECT ano_lancamento, nota FROM fatos ORDER BY ano_lancamento",
                "colunas": ["ano_lancamento", "nota_media_imdb"],
                "linhas": [
                    {"ano_lancamento": 2016, "nota_media_imdb": 6.1},
                    {"ano_lancamento": 2017, "nota_media_imdb": 6.2},
                ],
            },
        )
        self.assertNotIn("primeiro resultado", texto.lower())


if __name__ == "__main__":
    unittest.main()
