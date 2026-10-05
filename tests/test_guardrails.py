import json
import unittest

from cinedata_agent.guardrails import ErroConsulta, validar_sql


class TestGuardrails(unittest.TestCase):
    def test_select_simples(self):
        sql = validar_sql("  SELECT titulo FROM dim_movies LIMIT 5;  ")
        self.assertTrue(sql.lower().startswith("select"))
        self.assertFalse(sql.endswith(";"))

    def test_cte_e_alias(self):
        sql = """
        WITH top AS (
            SELECT titulo FROM dim_movies
        )
        SELECT * FROM top
        """
        validar_sql(sql)

    def test_recusa_escrita(self):
        for sql in (
            "DROP TABLE dim_movies",
            "DELETE FROM dim_movies",
            "UPDATE dim_movies SET titulo = 'x'",
            "INSERT INTO dim_movies (titulo) VALUES ('x')",
            "PRAGMA table_info(dim_movies)",
            "SELECT titulo FROM dim_movies; DROP TABLE dim_movies",
            "SELECT * FROM sqlite_master",
            "SELECT load_extension('x')",
        ):
            with self.assertRaises(ErroConsulta, msg=sql):
                validar_sql(sql)

    def test_palavra_proibida_dentro_de_texto_e_permitida(self):
        validar_sql("SELECT titulo FROM dim_movies WHERE titulo LIKE '%delete%' LIMIT 5")

    def test_tabela_fora_da_gold(self):
        with self.assertRaises(ErroConsulta):
            validar_sql("SELECT * FROM alembic_version")


if __name__ == "__main__":
    unittest.main()
