from __future__ import annotations

import re
from typing import Any


def _moeda_brl(valor: float) -> str:
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _decimal(valor: float) -> str:
    texto = f"{valor:,.3f}".rstrip("0").rstrip(".")
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _eh_moeda(coluna: str) -> bool:
    nome = coluna.lower()
    return nome.endswith("_brl") or any(pedaço in nome for pedaço in ("receita", "lucro", "orcamento"))


def _eh_ano(coluna: str) -> bool:
    nome = coluna.lower()
    return nome == "ano" or nome.startswith("ano_")


def formatar_celula(coluna: str, valor: Any) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, bool):
        return "sim" if valor else "não"
    if _eh_ano(coluna) and isinstance(valor, (int, float)):
        return str(int(valor))
    if isinstance(valor, (int, float)) and _eh_moeda(coluna):
        return _moeda_brl(float(valor))
    if isinstance(valor, float):
        return _decimal(valor)
    if isinstance(valor, int):
        return f"{valor:,}".replace(",", ".")
    return str(valor)


def _eh_ranking(sql: str) -> bool:
    return bool(re.search(r"order\s+by[\s\S]+\bdesc\b", sql or "", re.IGNORECASE))


def _medida_ordenada(colunas: list[str], linha: dict[str, Any], sql: str) -> str | None:
    correspondencia = re.search(
        r"order\s+by\s+(?:[A-Za-z_][\w]*\.)?([A-Za-z_][\w]*)\s+desc",
        sql or "",
        re.IGNORECASE,
    )
    if correspondencia:
        alvo = correspondencia.group(1).lower()
        for coluna in colunas:
            valor = linha.get(coluna)
            if coluna.lower() == alvo and isinstance(valor, (int, float)) and not isinstance(valor, bool):
                return coluna
    for coluna in colunas:
        valor = linha.get(coluna)
        if _eh_ano(coluna):
            continue
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            return coluna
    return None


def _frase_destaque(colunas: list[str], linhas: list[dict[str, Any]], sql: str) -> str:
    if not linhas:
        return "Nenhum registro atendeu aos filtros desta consulta."
    linha = linhas[0]
    textos = [coluna for coluna in colunas if isinstance(linha.get(coluna), str)]
    medida = _medida_ordenada(colunas, linha, sql)
    if not textos or not medida:
        return f"A consulta retornou {len(linhas)} linha(s)."
    nome = linha[textos[0]]
    ano = linha.get("ano_lancamento")
    valor = formatar_celula(medida, linha[medida])
    rotulo = medida.replace("_", " ")
    if ano:
        return f"O primeiro resultado é {nome} ({ano}), com {rotulo} de {valor}."
    return f"O primeiro resultado é {nome}, com {rotulo} de {valor}."


def _tabela_markdown(colunas: list[str], linhas: list[dict[str, Any]]) -> str:
    if not linhas:
        return ""
    cabecalho = "| " + " | ".join(coluna.replace("_", " ") for coluna in colunas) + " |"
    divisor = "| " + " | ".join("---" for _ in colunas) + " |"
    corpo = []
    for linha in linhas:
        celulas = [formatar_celula(coluna, linha.get(coluna)).replace("|", "/") for coluna in colunas]
        corpo.append("| " + " | ".join(celulas) + " |")
    return "\n".join([cabecalho, divisor, *corpo])


def redigir(objetivo: str, resultado: dict[str, Any]) -> str:
    colunas = resultado.get("colunas") or []
    linhas = resultado.get("linhas") or []
    titulo = (objetivo or "Resultado da consulta").strip().rstrip(".")
    partes = [titulo + "."]
    if not linhas:
        partes.append("Nenhum registro atendeu aos filtros desta consulta.")
    elif _eh_ranking(resultado.get("sql", "")):
        partes.append(_frase_destaque(colunas, linhas, resultado.get("sql", "")))
    tabela = _tabela_markdown(colunas, linhas)
    if tabela:
        partes.append(tabela)
    if linhas:
        partes.append(f"{len(linhas)} linha(s) vindas da camada Gold, em consulta somente leitura.")
    return "\n\n".join(partes)
