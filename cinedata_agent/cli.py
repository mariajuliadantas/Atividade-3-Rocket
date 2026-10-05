from __future__ import annotations

import argparse
import json
import sys

from cinedata_agent.agente import AgenteCineData, ErroAgente


def _imprimir(resultado: dict) -> None:
    print(resultado["resposta"])
    print()
    if resultado.get("modelo"):
        origem = "cache" if resultado.get("cache") else resultado["modelo"]
        print(f"Modelo: {origem}")
    for consulta in resultado.get("consultas") or []:
        print()
        print("SQL:")
        print(consulta.get("sql"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pergunte em português sobre o catálogo da CineData."
    )
    parser.add_argument("pergunta", nargs="*", help="Pergunta única. Sem argumentos, abre o chat.")
    parser.add_argument("--json", action="store_true", help="Imprime a resposta em JSON.")
    args = parser.parse_args(argv)

    agente = AgenteCineData()
    if args.pergunta:
        return _uma_pergunta(agente, " ".join(args.pergunta), args.json)

    print("CineData Analytics — escreva uma pergunta, ou 'sair' para encerrar.")
    historico: list[dict[str, str]] = []
    while True:
        try:
            pergunta = input("\nPergunta> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not pergunta:
            continue
        if pergunta.lower() in {"sair", "exit", "quit"}:
            return 0
        if pergunta.lower() == "limpar":
            historico.clear()
            print("Memória da conversa apagada.")
            continue
        try:
            resultado = agente.perguntar(pergunta, historico)
        except (ErroAgente, ValueError) as erro:
            print(f"Erro: {erro}")
            continue
        _imprimir(resultado)
        historico.append({"role": "user", "content": pergunta})
        historico.append({"role": "assistant", "content": resultado["resposta"]})


def _uma_pergunta(agente: AgenteCineData, pergunta: str, como_json: bool) -> int:
    try:
        resultado = agente.perguntar(pergunta)
    except (ErroAgente, ValueError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    if como_json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        _imprimir(resultado)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
