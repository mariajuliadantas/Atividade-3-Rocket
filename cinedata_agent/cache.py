from __future__ import annotations

import json
import sqlite3
import threading
from typing import Any, Optional

from cinedata_agent.config import ARQUIVO_CACHE, cache_ativo


class CacheRespostas:
    def __init__(self, caminho=None, ativo: Optional[bool] = None):
        self.ativo = cache_ativo() if ativo is None else ativo
        self.caminho = caminho or ARQUIVO_CACHE
        self._trava = threading.Lock()
        self._conexao: Optional[sqlite3.Connection] = None
        if self.ativo:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            self._conexao = sqlite3.connect(self.caminho, check_same_thread=False)
            self._conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS respostas (
                    chave TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            self._conexao.commit()

    def obter(self, chave: str) -> Optional[dict[str, Any]]:
        if not self.ativo or self._conexao is None:
            return None
        with self._trava:
            linha = self._conexao.execute(
                "SELECT payload FROM respostas WHERE chave = ?", (chave,)
            ).fetchone()
        if not linha:
            return None
        dados = json.loads(linha[0])
        dados["cache"] = True
        return dados

    def guardar(self, chave: str, payload: dict[str, Any]) -> None:
        if not self.ativo or self._conexao is None:
            return
        copia = dict(payload)
        copia["cache"] = False
        with self._trava:
            self._conexao.execute(
                "INSERT OR REPLACE INTO respostas (chave, payload) VALUES (?, ?)",
                (chave, json.dumps(copia, ensure_ascii=False)),
            )
            self._conexao.commit()

    def fechar(self) -> None:
        if self._conexao is not None:
            with self._trava:
                self._conexao.close()
                self._conexao = None
