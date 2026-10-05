from __future__ import annotations

import argparse
import json
from pathlib import Path

from cinedata_agent.config import ARQUIVO_PERGUNTAS, PASTA_AVALIACAO
from cinedata_agent.database import Banco
from cinedata_agent.resposta import redigir


def carregar_perguntas() -> list[dict]:
    return json.loads(ARQUIVO_PERGUNTAS.read_text(encoding="utf-8"))


def avaliar(banco: Banco | None = None) -> list[dict]:
    base = banco or Banco()
    saida = []
    for item in carregar_perguntas():
        resultado = base.executar(item["sql"], limite=30, tempo_limite=40)
        saida.append(
            {
                "id": item["id"],
                "categoria": item["categoria"],
                "pergunta": item["pergunta"],
                "sql": item["sql"],
                "resposta": redigir(item["pergunta"], resultado),
                "tabela": {"colunas": resultado["colunas"], "linhas": resultado["linhas"]},
            }
        )
    return saida


def para_markdown(resultados: list[dict]) -> str:
    partes = [
        "# Avaliação — respostas de referência",
        "",
        "SQL das perguntas da atividade, executado direto no banco, sem chamar o modelo.",
        "",
    ]
    categoria = ""
    for item in resultados:
        if item["categoria"] != categoria:
            categoria = item["categoria"]
            partes.extend([f"## {categoria}", ""])
        partes.extend(
            [
                f"### {item['pergunta']}",
                "",
                item["resposta"],
                "",
                "<details><summary>SQL</summary>",
                "",
                "```sql",
                item["sql"].strip(),
                "```",
                "",
                "</details>",
                "",
            ]
        )
    return "\n".join(partes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Executa o conjunto de avaliação no SQLite.")
    parser.add_argument(
        "--salvar",
        action="store_true",
        help="Grava avaliacao/resultados.md",
    )
    args = parser.parse_args(argv)
    resultados = avaliar()
    texto = para_markdown(resultados)
    if args.salvar:
        destino = Path(PASTA_AVALIACAO) / "resultados.md"
        destino.write_text(texto, encoding="utf-8")
        print(f"Salvo em {destino}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
