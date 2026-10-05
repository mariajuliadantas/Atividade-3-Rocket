from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from cinedata_agent.agente import AgenteCineData, ErroAgente
from cinedata_agent.config import ARQUIVO_PERGUNTAS, chave_openrouter
from cinedata_agent.database import Banco
from cinedata_agent.guardrails import ErroConsulta

DIRETORIO_ESTATICO = Path(__file__).resolve().parent / "static"

app = FastAPI(title="CineData Analytics", version="1.0.0")
app.mount("/static", StaticFiles(directory=DIRETORIO_ESTATICO), name="static")

_agente: Optional[AgenteCineData] = None
_banco = Banco()


def agente() -> AgenteCineData:
    global _agente
    if _agente is None:
        _agente = AgenteCineData(banco=_banco)
    return _agente


class Pedido(BaseModel):
    pergunta: str = Field(..., min_length=1, max_length=2000)
    historico: Optional[List[Dict[str, Any]]] = None


@app.get("/")
def pagina() -> FileResponse:
    return FileResponse(DIRETORIO_ESTATICO / "index.html")


@app.get("/api/saude")
def saude() -> dict:
    try:
        resumo = _banco.resumo()
    except ErroConsulta as erro:
        raise HTTPException(status_code=500, detail=str(erro)) from erro
    return {
        "ok": True,
        "banco": resumo["arquivo"],
        "filmes": resumo["filmes"],
        "tabelas": len(resumo["tabelas"]),
        "chave_configurada": bool(chave_openrouter()),
    }


@app.get("/api/exemplos")
def exemplos() -> list:
    import json

    return json.loads(ARQUIVO_PERGUNTAS.read_text(encoding="utf-8"))


@app.post("/api/perguntar")
def perguntar(pedido: Pedido) -> dict:
    try:
        return agente().perguntar(pedido.pergunta, pedido.historico)
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro
    except ErroAgente as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from erro
