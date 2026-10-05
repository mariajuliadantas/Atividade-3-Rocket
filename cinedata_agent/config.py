from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PASTA_AVALIACAO = ROOT / "avaliacao"
ARQUIVO_PERGUNTAS = PASTA_AVALIACAO / "perguntas.json"
PASTA_CACHE = ROOT / "cache"
ARQUIVO_CACHE = PASTA_CACHE / "respostas.db"

ANO_REFERENCIA = 2026
ANO_INICIO_JANELA = ANO_REFERENCIA - 4

LIMITE_LINHAS = 30
TEMPO_LIMITE_SEGUNDOS = 25
MAX_TENTATIVAS_SQL = 2

MODELO_PADRAO = "nvidia/nemotron-3.5-lightning:free"
FALLBACKS_PADRAO = (
    "google/gemma-4-26b-a4b-it:free",
    "z-ai/glm-5.2:free",
    "openrouter/free",
)

TABELAS_PERMITIDAS = frozenset(
    {
        "dim_movies",
        "fact_movies_performance",
        "dim_genres",
        "dim_people",
        "dim_companies",
        "dim_reviews",
        "movie_reviews",
        "bridge_movie_genre",
        "bridge_movie_person",
        "bridge_movie_company",
    }
)


def _flag(nome: str, padrao: str = "0") -> bool:
    return os.getenv(nome, padrao).strip().lower() in {"1", "true", "sim", "yes", "on"}


def caminho_banco() -> Path:
    informado = os.getenv("DB_PATH", "").strip()
    if informado:
        return Path(informado).expanduser().resolve()
    for nome in ("cinerocket.db", "cinerocket (1).db"):
        candidato = ROOT / nome
        if candidato.exists():
            return candidato.resolve()
    return (ROOT / "cinerocket.db").resolve()


def modelos() -> list[str]:
    principal = os.getenv("OPENROUTER_MODEL", MODELO_PADRAO).strip() or MODELO_PADRAO
    extras = os.getenv("OPENROUTER_FALLBACKS", ",".join(FALLBACKS_PADRAO))
    lista = [principal]
    for item in extras.split(","):
        nome = item.strip()
        if nome and nome not in lista:
            lista.append(nome)
    return lista


def chave_openrouter() -> str:
    return os.getenv("OPENROUTER_API_KEY", "").strip()


def cache_ativo() -> bool:
    return _flag("CACHE_ATIVO", "1")


def narrar_com_modelo() -> bool:
    return _flag("NARRAR", "0")
