import unittest

from cinedata_agent.avaliar import avaliar, carregar_perguntas


class TestReferencias(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resultados = {item["id"]: item for item in avaliar()}

    def test_cobre_as_categorias_da_atividade(self):
        categorias = {item["categoria"] for item in carregar_perguntas()}
        self.assertEqual(
            categorias,
            {
                "Bilheteria e finanças",
                "Popularidade e engajamento",
                "Elenco e equipe",
                "Gêneros e produtoras",
                "Avaliações dos usuários",
            },
        )

    def test_cada_consulta_devolve_linha(self):
        for item in self.resultados.values():
            self.assertGreater(len(item["tabela"]["linhas"]), 0, item["id"])

    def test_marcos_conhecidos_do_catalogo(self):
        top = self.resultados["bilheteria_top10"]["tabela"]["linhas"]
        self.assertEqual(top[0]["titulo"], "Avatar: The Way Of Water")
        self.assertEqual(len(top), 10)
        generos = self.resultados["filmes_por_genero"]["tabela"]["linhas"]
        self.assertEqual(generos[0]["nome_genero"], "Drama")
        produtora = self.resultados["produtora_lucro"]["tabela"]["linhas"][0]
        self.assertEqual(produtora["nome_produtora"], "Marvel Studios")


if __name__ == "__main__":
    unittest.main()
