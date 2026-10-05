from __future__ import annotations

import sqlite3
import time
from typing import Any

from cinedata_agent.config import (
    LIMITE_LINHAS,
    TABELAS_PERMITIDAS,
    TEMPO_LIMITE_SEGUNDOS,
    caminho_banco,
)
from cinedata_agent.guardrails import ErroConsulta, aplicar_limite, validar_sql


class Banco:
    def __init__(self, caminho=None):
        self.caminho = caminho or caminho_banco()

    def conectar(self) -> sqlite3.Connection:
        if not self.caminho.exists():
            raise ErroConsulta(
                f"Não encontrei o banco em {self.caminho}. "
                "Coloque cinerocket.db na pasta do projeto ou defina DB_PATH."
            )
        uri = f"{self.caminho.as_uri()}?mode=ro"
        conexao = sqlite3.connect(uri, uri=True, timeout=30)
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA query_only = ON")
        return conexao

    def resumo(self) -> dict[str, Any]:
        conexao = self.conectar()
        try:
            tabelas = [
                linha[0]
                for linha in conexao.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
                )
                if linha[0] in TABELAS_PERMITIDAS
            ]
            filmes = conexao.execute("SELECT COUNT(*) FROM dim_movies").fetchone()[0]
            return {"arquivo": self.caminho.name, "tabelas": tabelas, "filmes": filmes}
        finally:
            conexao.close()

    def executar(
        self,
        sql: str,
        limite: int = LIMITE_LINHAS,
        tempo_limite: int = TEMPO_LIMITE_SEGUNDOS,
    ) -> dict[str, Any]:
        sql_limpo = validar_sql(sql)
        sql_final = aplicar_limite(sql_limpo, limite)
        conexao = self.conectar()
        inicio = time.perf_counter()

        def interromper() -> int:
            if time.perf_counter() - inicio > tempo_limite:
                return 1
            return 0

        conexao.set_progress_handler(interromper, 10000)
        try:
            cursor = conexao.execute(sql_final)
            brutas = cursor.fetchall()
            colunas = [item[0] for item in cursor.description] if cursor.description else []
        except sqlite3.OperationalError as erro:
            mensagem = str(erro)
            if "interrupted" in mensagem.lower():
                raise ErroConsulta(
                    "A consulta passou do tempo limite. Agregue menos linhas ou filtre mais."
                ) from erro
            raise ErroConsulta(mensagem) from erro
        finally:
            conexao.close()

        linhas = [_normalizar(dict(linha)) for linha in brutas]
        return {"sql": sql_limpo, "colunas": colunas, "linhas": linhas}

    def buscar_sinopse(self, termo: str, limite: int = 5) -> dict[str, Any]:
        limpo = "".join(caractere for caractere in termo if caractere not in "%_").strip()
        if len(limpo) < 3:
            raise ErroConsulta("Informe um termo de busca com pelo menos 3 caracteres.")
        limite = max(1, min(int(limite or 5), 8))
        conexao = self.conectar()
        try:
            cursor = conexao.execute(
                """
                SELECT titulo, ano_lancamento, substr(sinopse, 1, 280) AS sinopse
                FROM dim_movies
                WHERE sinopse LIKE ?
                LIMIT ?
                """,
                (f"%{limpo}%", limite),
            )
            brutas = cursor.fetchall()
            colunas = [item[0] for item in cursor.description]
        finally:
            conexao.close()
        return {
            "sql": "busca lexical em dim_movies.sinopse",
            "colunas": colunas,
            "linhas": [_normalizar(dict(linha)) for linha in brutas],
            "termo": limpo,
        }


def _normalizar(linha: dict[str, Any]) -> dict[str, Any]:
    ajustada: dict[str, Any] = {}
    for coluna, valor in linha.items():
        if isinstance(valor, float):
            ajustada[coluna] = round(valor, 4 if abs(valor) < 1000 else 2)
        elif isinstance(valor, str) and len(valor) > 300:
            ajustada[coluna] = valor[:300] + "…"
        else:
            ajustada[coluna] = valor
    return ajustada
