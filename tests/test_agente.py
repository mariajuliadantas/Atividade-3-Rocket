import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from cinedata_agent import api
from cinedata_agent.agente import AgenteCineData, ChamadaFerramenta, ErroAgente, MensagemModelo
from cinedata_agent.cache import CacheRespostas
from cinedata_agent.database import Banco


SQL_TOP = """
SELECT m.titulo, m.ano_lancamento, ROUND(f.receita_brl, 2) AS receita_brl
FROM dim_movies m
JOIN fact_movies_performance f ON f.sk_movie_id = m.sk_movie_id
WHERE f.receita_brl > 0
ORDER BY f.receita_brl DESC
LIMIT 3
"""


class Contador:
    def __init__(self, fabrica):
        self.fabrica = fabrica
        self.chamadas = 0

    def __call__(self, mensagens, tool_choice):
        self.chamadas += 1
        return self.fabrica(mensagens, tool_choice)


def _agente(completador, pasta):
    return AgenteCineData(
        banco=Banco(),
        cache=CacheRespostas(caminho=Path(pasta) / "cache.db", ativo=True),
        completador=completador,
        lista_modelos=["modelo-teste"],
        narrar=False,
    )


class TestBanco(unittest.TestCase):
    def test_top_receita_e_avatar(self):
        resultado = Banco().executar(SQL_TOP)
        self.assertEqual(resultado["linhas"][0]["titulo"], "Avatar: The Way Of Water")

    def test_drop_nao_executa(self):
        with self.assertRaises(Exception):
            Banco().executar("DROP TABLE dim_movies")
        total = Banco().executar("SELECT COUNT(*) AS total FROM dim_movies")
        self.assertGreater(total["linhas"][0]["total"], 90000)

    def test_sinopse(self):
        resultado = Banco().buscar_sinopse("time travel", limite=3)
        self.assertGreaterEqual(len(resultado["linhas"]), 1)
        self.assertIn("sinopse", resultado["colunas"])


class TestAgente(unittest.TestCase):
    def test_pergunta_vira_sql_e_resposta_com_dado_real(self):
        def fabricar(mensagens, tool_choice):
            return MensagemModelo(
                tool_calls=[
                    ChamadaFerramenta(
                        "1",
                        "executar_sql",
                        json.dumps({"sql": SQL_TOP, "objetivo": "Top 3 filmes por receita em reais"}),
                    )
                ]
            )

        with tempfile.TemporaryDirectory() as pasta:
            contador = Contador(fabricar)
            resultado = _agente(contador, pasta).perguntar("Top 10 filmes com maior receita em R$")
        self.assertEqual(contador.chamadas, 1)
        self.assertIn("Avatar: The Way Of Water", resultado["resposta"])
        self.assertEqual(resultado["tabela"]["linhas"][0]["ano_lancamento"], 2022)
        self.assertIn("SELECT", resultado["consultas"][0]["sql"])

    def test_sql_destrutivo_nao_apaga_e_estoura_erro(self):
        def fabricar(mensagens, tool_choice):
            return MensagemModelo(
                tool_calls=[
                    ChamadaFerramenta(
                        "1",
                        "executar_sql",
                        json.dumps({"sql": "DELETE FROM dim_movies", "objetivo": "apagar"}),
                    )
                ]
            )

        with tempfile.TemporaryDirectory() as pasta:
            with self.assertRaises(ErroAgente):
                _agente(Contador(fabricar), pasta).perguntar("apague os filmes")
        total = Banco().executar("SELECT COUNT(*) AS total FROM dim_movies")
        self.assertGreater(total["linhas"][0]["total"], 90000)

    def test_cache_evita_segunda_chamada(self):
        def fabricar(mensagens, tool_choice):
            return MensagemModelo(
                tool_calls=[
                    ChamadaFerramenta(
                        "1",
                        "executar_sql",
                        json.dumps({"sql": "SELECT COUNT(*) AS total FROM dim_genres", "objetivo": "Quantos gêneros"}),
                    )
                ]
            )

        with tempfile.TemporaryDirectory() as pasta:
            contador = Contador(fabricar)
            agente = _agente(contador, pasta)
            primeiro = agente.perguntar("Quantos gêneros existem?")
            segundo = agente.perguntar("Quantos gêneros existem?")
        self.assertEqual(contador.chamadas, 1)
        self.assertFalse(primeiro["cache"])
        self.assertTrue(segundo["cache"])
        self.assertEqual(primeiro["resposta"], segundo["resposta"])

    def test_aceita_sql_em_bloco_markdown(self):
        def fabricar(mensagens, tool_choice):
            return MensagemModelo(content=f"```sql\n{SQL_TOP}\n```")

        with tempfile.TemporaryDirectory() as pasta:
            resultado = _agente(Contador(fabricar), pasta).perguntar("maiores receitas")
        self.assertIn("Avatar: The Way Of Water", resultado["resposta"])


class TestApi(unittest.TestCase):
    def test_pagina_saude_e_pergunta(self):
        def fabricar(mensagens, tool_choice):
            return MensagemModelo(
                tool_calls=[
                    ChamadaFerramenta(
                        "1",
                        "executar_sql",
                        json.dumps(
                            {
                                "sql": "SELECT nome_genero FROM dim_genres ORDER BY nome_genero LIMIT 3",
                                "objetivo": "Três gêneros",
                            }
                        ),
                    )
                ]
            )

        with tempfile.TemporaryDirectory() as pasta:
            api._agente = _agente(Contador(fabricar), pasta)
            cliente = TestClient(api.app)
            pagina = cliente.get("/")
            self.assertEqual(pagina.status_code, 200)
            self.assertIn("CineData Analytics", pagina.text)
            saude = cliente.get("/api/saude")
            self.assertEqual(saude.status_code, 200)
            self.assertGreater(saude.json()["filmes"], 90000)
            exemplos = cliente.get("/api/exemplos")
            self.assertEqual(exemplos.status_code, 200)
            self.assertGreaterEqual(len(exemplos.json()), 14)
            resposta = cliente.post("/api/perguntar", json={"pergunta": "Liste três gêneros"})
            self.assertEqual(resposta.status_code, 200)
            self.assertTrue(resposta.json()["tabela"]["linhas"])
            vazio = cliente.post("/api/perguntar", json={"pergunta": "   "})
            self.assertEqual(vazio.status_code, 400)


if __name__ == "__main__":
    unittest.main()
