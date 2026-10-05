from __future__ import annotations

import re

from cinedata_agent.config import TABELAS_PERMITIDAS

_PALAVRAS_PROIBIDAS = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|create|attach|detach|pragma|replace|"
    r"vacuum|reindex|grant|revoke|truncate|load_extension|writefile|readfile|"
    r"begin|commit|rollback|savepoint"
    r")\b",
    re.IGNORECASE,
)
_FUNCOES_PROIBIDAS = re.compile(
    r"\b(load_extension|writefile|readfile|edit|fts3_tokenizer)\s*\(",
    re.IGNORECASE,
)
_METADADOS = re.compile(r"\bsqlite_(?:master|temp_master|schema)\b", re.IGNORECASE)
_CTE = re.compile(
    r"(?:with\s+(?:recursive\s+)?|,)\s*([A-Za-z_][\w]*)\s+as\s*\(",
    re.IGNORECASE,
)
_TABELA = re.compile(
    r"\b(?:from|join)\s+((?:[A-Za-z_][\w]*\.)?[A-Za-z_][\w]*)",
    re.IGNORECASE,
)


class ErroConsulta(ValueError):
    pass


def _sem_literais(sql: str) -> str:
    return re.sub(r"'(?:''|[^'])*'", "''", sql)


def validar_sql(sql: str) -> str:
    if not sql or not sql.strip():
        raise ErroConsulta("A consulta veio vazia.")

    texto = sql.strip()
    if texto.endswith(";"):
        texto = texto[:-1].strip()

    analisavel = _sem_literais(texto)
    if ";" in analisavel:
        raise ErroConsulta("Envie apenas uma consulta, sem ponto e vírgula no meio.")

    if _PALAVRAS_PROIBIDAS.search(analisavel) or _FUNCOES_PROIBIDAS.search(analisavel):
        raise ErroConsulta("Só são permitidas consultas de leitura (SELECT).")

    if _METADADOS.search(analisavel):
        raise ErroConsulta("Consulta a tabelas internas do SQLite não é permitida.")

    primeira = re.search(r"[A-Za-z_]+", analisavel)
    if not primeira or primeira.group(0).lower() not in {"select", "with"}:
        raise ErroConsulta("A consulta precisa começar com SELECT ou WITH.")

    ctes = {nome.lower() for nome in _CTE.findall(analisavel)}
    for bruto in _TABELA.findall(analisavel):
        nome = bruto.split(".")[-1].lower()
        if nome in ctes:
            continue
        if nome not in TABELAS_PERMITIDAS:
            raise ErroConsulta(f"A tabela '{nome}' não faz parte da camada Gold liberada.")

    return texto


def aplicar_limite(sql: str, limite: int) -> str:
    return f"SELECT * FROM (\n{sql}\n) AS resultado_agente LIMIT {int(limite)}"
