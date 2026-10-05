from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from cinedata_agent.cache import CacheRespostas
from cinedata_agent.config import (
    MAX_TENTATIVAS_SQL,
    chave_openrouter,
    modelos,
    narrar_com_modelo,
)
from cinedata_agent.database import Banco
from cinedata_agent.guardrails import ErroConsulta
from cinedata_agent.resposta import redigir
from cinedata_agent.schema import prompt_sistema

FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "executar_sql",
            "description": "Executa um SELECT somente leitura na camada Gold e devolve as linhas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "Um único SELECT ou WITH ... SELECT."},
                    "objetivo": {
                        "type": "string",
                        "description": "O que a consulta responde, em uma frase curta.",
                    },
                },
                "required": ["sql", "objetivo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_sinopse",
            "description": "Busca filmes cujo enredo contém um termo. Use para perguntas de sinopse, não para números.",
            "parameters": {
                "type": "object",
                "properties": {
                    "termo": {"type": "string"},
                    "limite": {"type": "integer"},
                },
                "required": ["termo"],
            },
        },
    },
]

_BLOCO_SQL = re.compile(r"```sql\s*(.*?)```", re.IGNORECASE | re.DOTALL)


class ErroAgente(RuntimeError):
    pass


@dataclass
class ChamadaFerramenta:
    id: str
    nome: str
    argumentos: str


@dataclass
class MensagemModelo:
    content: Optional[str] = None
    tool_calls: list[ChamadaFerramenta] = field(default_factory=list)
    modelo: str = ""


Completador = Callable[[list[dict[str, Any]], str], MensagemModelo]


def _extrair_sql(texto: Optional[str]) -> Optional[str]:
    if not texto:
        return None
    bloco = _BLOCO_SQL.search(texto)
    if bloco:
        return bloco.group(1).strip()
    candidato = texto.strip()
    if re.match(r"(?is)^(select|with)\b", candidato):
        return candidato
    return None


def _historico_valido(historico: Optional[list[dict[str, Any]]]) -> list[dict[str, str]]:
    mensagens: list[dict[str, str]] = []
    for item in historico or []:
        papel = str(item.get("role", ""))
        if papel not in {"user", "assistant"}:
            continue
        conteudo = str(item.get("content", "")).strip()
        if not conteudo:
            continue
        mensagens.append({"role": papel, "content": conteudo[:2000]})
    return mensagens[-6:]


class AgenteCineData:
    def __init__(
        self,
        banco: Optional[Banco] = None,
        cache: Optional[CacheRespostas] = None,
        completador: Optional[Completador] = None,
        lista_modelos: Optional[list[str]] = None,
        narrar: Optional[bool] = None,
    ):
        self.banco = banco or Banco()
        self.cache = cache if cache is not None else CacheRespostas()
        self.completador = completador
        self.lista_modelos = lista_modelos or modelos()
        self.narrar = narrar_com_modelo() if narrar is None else narrar
        self._cliente = None

    def perguntar(
        self,
        pergunta: str,
        historico: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        texto = (pergunta or "").strip()
        if not texto:
            raise ValueError("Escreva uma pergunta.")
        if len(texto) > 2000:
            raise ValueError("A pergunta passou de 2000 caracteres.")

        anteriores = _historico_valido(historico)
        chave = _chave_cache(texto, anteriores, self.lista_modelos[0])
        em_cache = self.cache.obter(chave)
        if em_cache is not None:
            return em_cache

        mensagens: list[dict[str, Any]] = [
            {"role": "system", "content": prompt_sistema()},
            *anteriores,
            {"role": "user", "content": texto},
        ]
        consultas: list[dict[str, Any]] = []
        ultimo_resultado: Optional[dict[str, Any]] = None
        modelo_usado = ""

        for tentativa in range(MAX_TENTATIVAS_SQL):
            mensagem = self._completar(mensagens, "auto")
            modelo_usado = mensagem.modelo or modelo_usado
            if not mensagem.tool_calls:
                sql_solto = _extrair_sql(mensagem.content)
                if sql_solto and tentativa == 0:
                    mensagem.tool_calls = [
                        ChamadaFerramenta("sql-texto", "executar_sql", json.dumps({"sql": sql_solto, "objetivo": texto}))
                    ]
                else:
                    resposta = {
                        "resposta": (mensagem.content or "Não consegui montar uma consulta para essa pergunta.").strip(),
                        "consultas": consultas,
                        "tabela": _tabela(ultimo_resultado),
                        "modelo": modelo_usado,
                        "cache": False,
                    }
                    if consultas:
                        self.cache.guardar(chave, resposta)
                    return resposta

            mensagens.append(_mensagem_assistente(mensagem))
            for chamada in mensagem.tool_calls[:2]:
                conteudo, resultado = self._executar_ferramenta(chamada)
                mensagens.append(
                    {"role": "tool", "tool_call_id": chamada.id, "content": conteudo}
                )
                if resultado and "erro" not in resultado:
                    consultas.append(
                        {
                            "objetivo": resultado.get("objetivo") or texto,
                            "sql": resultado.get("sql"),
                            "linhas": len(resultado.get("linhas") or []),
                        }
                    )
                    ultimo_resultado = resultado
                elif resultado and resultado.get("erro"):
                    ultimo_resultado = resultado

            if ultimo_resultado and "erro" not in ultimo_resultado:
                break

        if not ultimo_resultado or "erro" in (ultimo_resultado or {}):
            detalhe = (ultimo_resultado or {}).get("erro", "sem resultado")
            raise ErroAgente(f"Não consegui consultar a camada Gold. Último retorno: {detalhe}")

        if self.narrar:
            texto_final = self._narrar(mensagens, ultimo_resultado)
            modelo_usado = texto_final[1] or modelo_usado
            corpo = texto_final[0]
        else:
            corpo = redigir(str(ultimo_resultado.get("objetivo") or texto), ultimo_resultado)

        resposta = {
            "resposta": corpo,
            "consultas": consultas,
            "tabela": _tabela(ultimo_resultado),
            "modelo": modelo_usado,
            "cache": False,
        }
        self.cache.guardar(chave, resposta)
        return resposta

    def _narrar(self, mensagens: list[dict[str, Any]], resultado: dict[str, Any]) -> tuple[str, str]:
        pacote = json.dumps(
            {"colunas": resultado.get("colunas"), "linhas": resultado.get("linhas")},
            ensure_ascii=False,
        )
        mensagens.append(
            {
                "role": "user",
                "content": (
                    "Escreva a resposta final em português, em até 2 parágrafos, "
                    "usando somente os números abaixo. Não invente valores nem filmes. "
                    "Se citar dinheiro, use reais.\n"
                    + pacote
                ),
            }
        )
        mensagem = self._completar(mensagens, "none")
        texto = (mensagem.content or "").strip() or redigir(
            str(resultado.get("objetivo") or ""), resultado
        )
        return texto, mensagem.modelo

    def _executar_ferramenta(self, chamada: ChamadaFerramenta) -> tuple[str, dict[str, Any]]:
        try:
            argumentos = json.loads(chamada.argumentos or "{}")
        except json.JSONDecodeError:
            erro = {"erro": "Os argumentos da ferramenta não são JSON válido."}
            return json.dumps(erro, ensure_ascii=False), erro

        try:
            if chamada.nome == "executar_sql":
                resultado = self.banco.executar(str(argumentos.get("sql", "")))
                resultado["objetivo"] = str(argumentos.get("objetivo") or "").strip()
            elif chamada.nome == "buscar_sinopse":
                resultado = self.banco.buscar_sinopse(
                    str(argumentos.get("termo", "")),
                    int(argumentos.get("limite") or 5),
                )
                resultado["objetivo"] = f"Sinopses que citam '{resultado['termo']}'"
            else:
                erro = {"erro": f"Ferramenta desconhecida: {chamada.nome}"}
                return json.dumps(erro, ensure_ascii=False), erro
        except ErroConsulta as erro:
            pacote = {"erro": str(erro)}
            return json.dumps(pacote, ensure_ascii=False), pacote

        pacote = {
            "colunas": resultado["colunas"],
            "linhas": resultado["linhas"],
            "total": len(resultado["linhas"]),
        }
        return json.dumps(pacote, ensure_ascii=False), resultado

    def _completar(self, mensagens: list[dict[str, Any]], tool_choice: str) -> MensagemModelo:
        if self.completador is not None:
            mensagem = self.completador(mensagens, tool_choice)
            mensagem.modelo = mensagem.modelo or "teste"
            return mensagem
        return self._completar_openrouter(mensagens, tool_choice)

    def _completar_openrouter(self, mensagens: list[dict[str, Any]], tool_choice: str) -> MensagemModelo:
        if not chave_openrouter():
            raise ErroAgente(
                "Defina OPENROUTER_API_KEY no arquivo .env. "
                "O passo a passo está em tutorial-openrouter.html e no README."
            )
        from openai import APIConnectionError, APIStatusError, OpenAI

        if self._cliente is None:
            self._cliente = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=chave_openrouter(),
                timeout=90,
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "CineData Analytics Rocket Lab",
                },
            )

        ultimo_erro = "nenhum modelo respondeu"
        for modelo in self.lista_modelos:
            try:
                resposta = self._cliente.chat.completions.create(
                    model=modelo,
                    messages=mensagens,
                    tools=FERRAMENTAS,
                    tool_choice=tool_choice,
                    temperature=0,
                    max_tokens=1200,
                )
            except APIStatusError as erro:
                ultimo_erro = f"{modelo}: HTTP {erro.status_code}"
                if erro.status_code == 401:
                    raise ErroAgente(
                        "A chave da OpenRouter foi recusada (401). Confira se ela começa com sk-or-v1-."
                    ) from erro
                if erro.status_code == 402:
                    raise ErroAgente(
                        "A OpenRouter retornou 402 (saldo). Modelos :free não deveriam cobrar; "
                        "verifique se a conta não está com saldo negativo."
                    ) from erro
                continue
            except APIConnectionError as erro:
                ultimo_erro = f"{modelo}: falha de rede ({erro})"
                continue

            escolha = resposta.choices[0].message
            chamadas = []
            for chamada in escolha.tool_calls or []:
                chamadas.append(
                    ChamadaFerramenta(
                        id=chamada.id,
                        nome=chamada.function.name,
                        argumentos=chamada.function.arguments or "{}",
                    )
                )
            return MensagemModelo(content=escolha.content, tool_calls=chamadas, modelo=modelo)

        raise ErroAgente(
            "Nenhum modelo gratuito respondeu. "
            "Se foi 429 de provider lotado, tente de novo mais tarde ou troque OPENROUTER_MODEL. "
            "Se a cota diária de 50 pedidos acabou, o reset é à meia-noite UTC (21h em Brasília). "
            f"Último erro: {ultimo_erro}."
        )


def _mensagem_assistente(mensagem: MensagemModelo) -> dict[str, Any]:
    if not mensagem.tool_calls:
        return {"role": "assistant", "content": mensagem.content or ""}
    return {
        "role": "assistant",
        "content": mensagem.content,
        "tool_calls": [
            {
                "id": chamada.id,
                "type": "function",
                "function": {"name": chamada.nome, "arguments": chamada.argumentos},
            }
            for chamada in mensagem.tool_calls
        ],
    }


def _tabela(resultado: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not resultado or "erro" in resultado:
        return None
    return {"colunas": resultado.get("colunas") or [], "linhas": resultado.get("linhas") or []}


def _chave_cache(pergunta: str, historico: list[dict[str, str]], modelo: str) -> str:
    bruto = json.dumps({"p": pergunta, "h": historico, "m": modelo}, ensure_ascii=False)
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()
