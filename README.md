# CineData Analytics — agente Text-to-SQL

Agente em Python que responde perguntas em português sobre o catálogo de filmes da CineData. A pergunta vira um SELECT na camada Gold e a resposta usa os números que o SQLite devolveu.

Dá para usar pelo terminal ou pela página em `http://127.0.0.1:8000`.

## O que ele cobre

As categorias pedidas na atividade:

- bilheteria e finanças (receita, lucro médio, margem)
- popularidade e engajamento (popularidade, TMDB x IMDb, nota média por ano)
- elenco e equipe (ator, diretor, dupla ator–diretor)
- gêneros e produtoras
- avaliações dos usuários

Também há busca por termo na sinopse, guardrail que bloqueia escrita no banco, fallback entre modelos gratuitos da OpenRouter, cache de pergunta repetida e um conjunto de avaliação com SQL de referência.

Receita, faturamento e bilheteria são tratados como a mesma medida. O padrão é real (`receita_brl`).

## Arquivos da atividade usados aqui

| Arquivo | Uso |
| --- | --- |
| `Atividade GenAI - RocketLab 26.2 Perfis vdev.docx.pdf` | Enunciado |
| `cinerocket (1).db` | Camada Gold (SQLite). Também é aceito o nome `cinerocket.db` |
| `tutorial-openrouter.html` | Conta, chave, modelos `:free`, cota e erros 401/429/402 |

## Passo a passo

### 1. Chave da OpenRouter

1. Abra `tutorial-openrouter.html` no navegador (ou [openrouter.ai](https://openrouter.ai)).
2. Crie a conta e uma chave em [openrouter.ai/keys](https://openrouter.ai/keys).
3. Na pasta do projeto:

```bash
cp .env.example .env
```

4. Cole a chave em `OPENROUTER_API_KEY`. Ela começa com `sk-or-v1-`.

A conta gratuita tem 50 pedidos por dia em modelos `:free`. Cada pergunta gasta 1 pedido (2 se o SQL vier errado e o agente corrigir; 3 se `NARRAR=1`). Pedidos que falham também contam. O contador zera à meia-noite UTC, 21h em Brasília.

### 2. Ambiente Python

Na pasta do projeto, com Python 3.9 ou superior:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Não é preciso instalar banco, Docker nem conta em nuvem. O SQLite já vem com o Python. Baixe `cinerocket (1).db` na pasta da atividade e deixe o arquivo na raiz do projeto. O código também aceita o nome `cinerocket.db`. Para outro caminho, preencha `DB_PATH` no `.env`. Esse arquivo não vai para o GitHub: ele tem cerca de 580 MB e o limite por arquivo é 100 MB.

### 3. Conferir o banco sem gastar cota

Isto roda só o SQL de referência das perguntas da atividade, sem chamar modelo:

```bash
python -m cinedata_agent.avaliar
```

Para gravar o relatório:

```bash
python -m cinedata_agent.avaliar --salvar
```

O arquivo fica em `avaliacao/resultados.md`.

Os testes automatizados também não usam a OpenRouter:

```bash
python -m unittest discover -s tests -v
```

### 4. Fazer uma pergunta

Uma pergunta e encerra:

```bash
python -m cinedata_agent "Top 10 filmes com maior receita em R$"
```

Conversa, com memória até você digitar `limpar` ou `sair`:

```bash
python -m cinedata_agent
```

JSON completo (resposta, SQL e linhas):

```bash
python -m cinedata_agent --json "Os 5 filmes mais populares"
```

### 5. Abrir a página

```bash
uvicorn cinedata_agent.api:app --reload
```

Acesse [http://127.0.0.1:8000](http://127.0.0.1:8000). A faixa do topo mostra se o banco abriu e se a chave está configurada. Os botões preenchem as perguntas da atividade; a consulta parte do agente, não de um SQL fixo.

`Ctrl+Enter` ou `Cmd+Enter` envia a pergunta. "Lembrar desta conversa" manda as últimas falas para o modelo, para perguntas de continuação ("e em dólares?").

## Como o agente decide

1. O modelo recebe o esquema das 10 tabelas, o dicionário de gêneros (os nomes estão em inglês) e as regras de negócio.
2. Ele chama a ferramenta `executar_sql` ou, se a pergunta for de enredo, `buscar_sinopse`.
3. O guardrail recusa qualquer coisa que não seja um único `SELECT` / `WITH` nas tabelas da Gold. O arquivo abre em modo somente leitura.
4. O resultado volta com no máximo 30 linhas e estoura aos 25 segundos.
5. O texto final sai das linhas retornadas. Com `NARRAR=1` no `.env`, o modelo redige um parágrafo em cima desses números e gasta um pedido a mais.

Se o modelo devolver HTTP 429 ou estiver fora do ar, a mesma pergunta segue para o próximo da lista:

1. `nvidia/nemotron-3.5-lightning:free`
2. `google/gemma-4-26b-a4b-it:free`
3. `z-ai/glm-5.2:free`
4. `openrouter/free`

Uma pergunta idêntica, com o mesmo histórico, é respondida pelo cache em `cache/respostas.db` e não consome cota. Apague essa pasta para forçar de novo.

## Regras de leitura dos números

Estão no prompt e no SQL de `avaliacao/perguntas.json`.

- Valores em real, salvo pedido explícito de dólar.
- Receita informada: valor maior que zero.
- Margem do filme: `lucro_brl / receita_brl`, com orçamento de pelo menos R$ 100.000 no ranking. Orçamentos de centavos deixam a margem artificialmente em 100%.
- Margem média de gênero: `SUM(lucro) / SUM(receita)`, não a média simples das margens (outliers negativos distorcem a média).
- Divergência TMDB x IMDb: as duas notas preenchidas, nota TMDB acima de zero e pelo menos 500 votos no IMDb.
- Últimos 5 anos: lançamentos de 2022 a 2026, com status `Lançado`. A data de referência é 05/10/2026.
- Diretores: nota IMDb com pelo menos 100 votos e no mínimo 5 filmes.
- Avaliações de usuários: a tabela agregada `dim_reviews`. A divergência com o IMDb exige pelo menos 5 avaliações.
- O lucro de um filme entra inteiro em cada produtora ligada a ele. A ponte não tem percentual.

Gêneros no banco: Action, Adventure, Animation, Comedy, Crime, Documentary, Drama, Family, Fantasy, History, Horror, Music, Mystery, Romance, Science Fiction, Thriller, Tv Movie, War, Western. "Ação" vira `Action`, "ficção científica" vira `Science Fiction`.

## Estrutura

```
cinedata_agent/agente.py      laço do agente e fallback de modelos
cinedata_agent/guardrails.py  SQL somente leitura
cinedata_agent/database.py    SQLite em mode=ro
cinedata_agent/schema.py      esquema e regras enviados ao modelo
cinedata_agent/cli.py         terminal
cinedata_agent/api.py         FastAPI
cinedata_agent/static/        página
cinedata_agent/avaliar.py     roda as perguntas sem o modelo
avaliacao/perguntas.json      SQL esperado de cada categoria
tests/                        guardrail, banco, agente e API
```

## Erros comuns

| Sintoma | O que fazer |
| --- | --- |
| 401 | A chave não está no `.env` ou não começa com `sk-or-v1-` |
| 429 com provider lotado | O agente já troca de modelo. Se todos falharem, espere e tente de novo |
| 429 de cota | 50 pedidos no dia. Veja [openrouter.ai/activity](https://openrouter.ai/activity). Reset às 21h (Brasília) |
| 402 | Saldo negativo na conta. Modelo `:free` não deveria cobrar |
| Banco não encontrado | Deixe `cinerocket (1).db` na raiz ou defina `DB_PATH` |

## O que entra no repositório

O `.gitignore` já deixa de fora o que não deve ser publicado:

| Fica de fora | Motivo |
| --- | --- |
| `.env` | Chave da OpenRouter |
| `cinerocket (1).db` e os arquivos `-wal` / `-shm` | Banco grande demais para o GitHub |
| `.venv/`, `__pycache__/`, `cache/` | Ambiente local e cache de respostas |

No repositório ficam o código, os testes, `requirements.txt`, `.env.example`, o `README`, o enunciado em PDF e o `tutorial-openrouter.html`.

Quem clonar o projeto precisa de duas coisas que não vêm no Git: criar o `.env` a partir do exemplo e colocar o `cinerocket (1).db` na raiz.
