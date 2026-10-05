# Avaliação — respostas de referência

SQL das perguntas da atividade, executado direto no banco, sem chamar o modelo.

## Bilheteria e finanças

### Top 10 filmes com maior receita em R$

Top 10 filmes com maior receita em R$.

O primeiro resultado é Avatar: The Way Of Water (2022), com receita brl de R$ 12.390.136.500,54.

| titulo | ano lancamento | receita brl |
| --- | --- | --- |
| Avatar: The Way Of Water | 2022 | R$ 12.390.136.500,54 |
| Avengers: Endgame | 2019 | R$ 11.094.720.000,00 |
| Spider-man: No Way Home | 2021 | R$ 10.977.782.882,74 |
| Avengers: Infinity War | 2018 | R$ 7.190.430.847,63 |
| Top Gun: Maverick | 2022 | R$ 7.160.804.869,01 |
| Barbie | 2023 | R$ 6.856.159.007,38 |
| The Super Mario Bros. Movie | 2023 | R$ 6.838.413.799,10 |
| The Lion King | 2019 | R$ 6.227.552.146,58 |
| Frozen Ii | 2019 | R$ 6.094.028.191,32 |
| Jurassic World: Fallen Kingdom | 2018 | R$ 4.934.822.930,85 |

10 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT m.titulo, m.ano_lancamento, ROUND(f.receita_brl, 2) AS receita_brl
FROM dim_movies m
JOIN fact_movies_performance f ON f.sk_movie_id = m.sk_movie_id
WHERE f.receita_brl > 0
ORDER BY f.receita_brl DESC
LIMIT 10
```

</details>

### Lucro médio por gênero, considerando apenas filmes com receita informada

Lucro médio por gênero, considerando apenas filmes com receita informada.

O primeiro resultado é Science Fiction, com lucro medio brl de R$ 520.783.718,33.

| nome genero | lucro medio brl | qtd filmes |
| --- | --- | --- |
| Science Fiction | R$ 520.783.718,33 | 227 |
| Adventure | R$ 514.678.791,39 | 393 |
| Action | R$ 343.223.021,87 | 594 |
| Fantasy | R$ 335.448.446,35 | 255 |
| Family | R$ 324.648.758,33 | 264 |
| Animation | R$ 303.517.897,37 | 239 |
| War | R$ 194.016.703,28 | 91 |
| History | R$ 146.826.836,61 | 171 |
| Comedy | R$ 143.589.472,55 | 813 |
| Mystery | R$ 119.462.433,49 | 246 |
| Music | R$ 111.985.444,28 | 100 |
| Romance | R$ 98.645.875,99 | 312 |
| Crime | R$ 93.988.989,27 | 294 |
| Thriller | R$ 92.872.345,47 | 623 |
| Horror | R$ 92.805.277,20 | 383 |
| Drama | R$ 84.161.852,72 | 1.297 |
| Tv Movie | R$ 9.228.474,48 | 10 |
| Documentary | R$ 5.028.959,44 | 153 |
| Western | R$ -3.581.373,25 | 20 |

19 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT g.nome_genero, ROUND(AVG(f.lucro_brl), 2) AS lucro_medio_brl, COUNT(DISTINCT f.sk_movie_id) AS qtd_filmes
FROM dim_genres g
JOIN bridge_movie_genre bg ON bg.sk_genre_id = g.sk_genre_id
JOIN fact_movies_performance f ON f.sk_movie_id = bg.sk_movie_id
WHERE f.receita_brl > 0
GROUP BY g.sk_genre_id, g.nome_genero
ORDER BY lucro_medio_brl DESC
```

</details>

### Filmes com maior margem de lucro, entre os que possuem receita e orçamento informados

Filmes com maior margem de lucro, entre os que possuem receita e orçamento informados.

O primeiro resultado é Secret Superstar (2017), com margem de 0,998.

| titulo | ano lancamento | margem | receita brl | orcamento brl |
| --- | --- | --- | --- | --- |
| Secret Superstar | 2017 | 0,998 | R$ 435.981.992,64 | R$ 908.293,25 |
| Unbound | 2018 | 0,996 | R$ 79.237.200,00 | R$ 301.856,00 |
| Me Against You: Mr. S's Vendetta | 2020 | 0,992 | R$ 39.739.450,00 | R$ 313.732,50 |
| Dragon Ball Super: Broly | 2018 | 0,992 | R$ 488.561.025,60 | R$ 3.908.400,00 |
| Ariana Grande - Positions Album (official Live Performances) / Vevo | 2021 | 0,992 | R$ 15.110.100,00 | R$ 125.917,50 |
| The Farewell | 2019 | 0,989 | R$ 86.412.849,80 | R$ 937.273,38 |
| The Villainess | 2017 | 0,986 | R$ 28.686.822,11 | R$ 410.400,00 |
| Terrifier 2 | 2022 | 0,983 | R$ 78.342.255,85 | R$ 1.300.050,00 |
| Get Out | 2017 | 0,982 | R$ 791.432.673,54 | R$ 13.944.150,00 |
| Tunnel | 2016 | 0,981 | R$ 164.129.665,63 | R$ 3.129.600,00 |

10 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT m.titulo, m.ano_lancamento,
       ROUND(f.lucro_brl * 1.0 / f.receita_brl, 4) AS margem,
       ROUND(f.receita_brl, 2) AS receita_brl,
       ROUND(f.orcamento_brl, 2) AS orcamento_brl
FROM dim_movies m
JOIN fact_movies_performance f ON f.sk_movie_id = m.sk_movie_id
WHERE f.receita_brl > 0
  AND f.orcamento_brl >= 100000
ORDER BY margem DESC
LIMIT 10
```

</details>

## Popularidade e engajamento

### Os 5 filmes mais populares

Os 5 filmes mais populares.

O primeiro resultado é Blue Beetle (2023), com popularidade de 2.994,36.

| titulo | ano lancamento | popularidade |
| --- | --- | --- |
| Blue Beetle | 2023 | 2.994,36 |
| Gran Turismo | 2023 | 2.680,59 |
| La Fellinette | 2020 | 2.020 |
| The Fear Footage 2: Curse Of The Tape | 2020 | 2.019 |
| Wwe Survivor Series 2018 | 2018 | 2.018 |

5 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT m.titulo, m.ano_lancamento, ROUND(f.popularidade, 3) AS popularidade
FROM dim_movies m
JOIN fact_movies_performance f ON f.sk_movie_id = m.sk_movie_id
WHERE f.popularidade IS NOT NULL
ORDER BY f.popularidade DESC
LIMIT 5
```

</details>

### Filmes com maior divergência entre a nota TMDB e a nota IMDb

Filmes com maior divergência entre a nota TMDB e a nota IMDb.

O primeiro resultado é Feride (2020), com divergencia de 8,1.

| titulo | ano lancamento | nota tmdb | nota imdb | divergencia |
| --- | --- | --- | --- | --- |
| Feride | 2020 | 10 | 1,9 | 8,1 |
| Connie Lynn | 2022 | 10 | 2,4 | 7,6 |
| Operation Mayfair | 2023 | 10 | 2,4 | 7,6 |
| The Adventures Of Açela | 2020 | 10 | 2,5 | 7,5 |
| Amityville Cop | 2021 | 10 | 2,5 | 7,5 |
| 1959 | 2021 | 1 | 8,4 | 7,4 |
| Impact Event | 2018 | 10 | 2,8 | 7,2 |
| Chhalawa | 2019 | 10 | 3 | 7 |
| Morine | 2018 | 1 | 8 | 7 |
| Tantura | 2022 | 1,5 | 8,5 | 7 |

10 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT m.titulo, m.ano_lancamento, ROUND(f.nota_tmdb, 3) AS nota_tmdb, ROUND(f.nota_imdb, 3) AS nota_imdb,
       ROUND(ABS(f.nota_tmdb - f.nota_imdb), 3) AS divergencia
FROM dim_movies m
JOIN fact_movies_performance f ON f.sk_movie_id = m.sk_movie_id
WHERE f.nota_tmdb > 0
  AND f.nota_imdb IS NOT NULL
  AND f.qtd_imdb >= 500
ORDER BY divergencia DESC
LIMIT 10
```

</details>

### Nota média IMDb por ano de lançamento

Nota média IMDb por ano de lançamento.

| ano lancamento | nota media imdb | qtd filmes |
| --- | --- | --- |
| 2016 | 6,338 | 10.381 |
| 2017 | 6,339 | 11.189 |
| 2018 | 6,272 | 11.327 |
| 2019 | 6,259 | 11.637 |
| 2020 | 6,244 | 9.534 |
| 2021 | 6,23 | 9.578 |
| 2022 | 6,23 | 9.887 |
| 2023 | 6,225 | 7.809 |
| 2024 | 6,155 | 1.621 |
| 2025 | 6,575 | 4 |
| 2026 | 7,5 | 1 |
| 2027 | 6,4 | 2 |
| 2029 | 3,8 | 1 |

13 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT m.ano_lancamento, ROUND(AVG(f.nota_imdb), 3) AS nota_media_imdb, COUNT(*) AS qtd_filmes
FROM dim_movies m
JOIN fact_movies_performance f ON f.sk_movie_id = m.sk_movie_id
WHERE f.nota_imdb IS NOT NULL
  AND m.ano_lancamento IS NOT NULL
GROUP BY m.ano_lancamento
ORDER BY m.ano_lancamento
```

</details>

## Elenco e equipe

### Ator com mais participações em filmes lançados nos últimos 5 anos

Ator com mais participações em filmes lançados nos últimos 5 anos.

O primeiro resultado é Eric Roberts, com participacoes de 54.

| nome pessoa | participacoes |
| --- | --- |
| Eric Roberts | 54 |
| David Love | 37 |
| Anton Pelizzari | 37 |
| Cameron Nichols | 37 |
| Jazzyjoeyjr | 37 |

5 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT p.nome_pessoa, COUNT(DISTINCT m.sk_movie_id) AS participacoes
FROM dim_people p
JOIN bridge_movie_person b ON b.sk_person_id = p.sk_person_id
JOIN dim_movies m ON m.sk_movie_id = b.sk_movie_id
WHERE p.tipo_pessoa = 'Ator'
  AND m.status_filme = 'Lançado'
  AND m.ano_lancamento BETWEEN 2022 AND 2026
GROUP BY p.sk_person_id, p.nome_pessoa
ORDER BY participacoes DESC
LIMIT 5
```

</details>

### Diretores com maior nota média (mínimo de 5 filmes)

Diretores com maior nota média (mínimo de 5 filmes).

O primeiro resultado é Yūichirō Hayashi, com nota media imdb de 9,188.

| nome pessoa | nota media imdb | qtd filmes |
| --- | --- | --- |
| Yūichirō Hayashi | 9,188 | 8 |
| Jun Shishido | 9,188 | 8 |
| Tokio Igarashi | 9 | 5 |
| Spencer Susser | 8,3 | 6 |
| Digpal Lanjekar | 8,18 | 5 |
| Park Jun-soo | 8,14 | 5 |
| Paul Dugdale | 8,127 | 11 |
| Tony Grech-smith | 8,1 | 6 |
| Joel Guerra | 8,086 | 7 |
| Adam Condal | 8,06 | 5 |

10 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT p.nome_pessoa, ROUND(AVG(f.nota_imdb), 3) AS nota_media_imdb, COUNT(DISTINCT m.sk_movie_id) AS qtd_filmes
FROM dim_people p
JOIN bridge_movie_person b ON b.sk_person_id = p.sk_person_id
JOIN dim_movies m ON m.sk_movie_id = b.sk_movie_id
JOIN fact_movies_performance f ON f.sk_movie_id = m.sk_movie_id
WHERE p.tipo_pessoa = 'Diretor'
  AND f.nota_imdb IS NOT NULL
  AND f.qtd_imdb >= 100
GROUP BY p.sk_person_id, p.nome_pessoa
HAVING COUNT(DISTINCT m.sk_movie_id) >= 5
ORDER BY nota_media_imdb DESC
LIMIT 10
```

</details>

### Dupla ator–diretor que mais trabalhou junta

Dupla ator–diretor que mais trabalhou junta.

O primeiro resultado é Joe Anoa'i, com filmes juntos de 37.

| ator | diretor | filmes juntos |
| --- | --- | --- |
| Joe Anoa'i | Kevin Dunn | 37 |
| Colby Lopez | Kevin Dunn | 32 |
| David Love | Chad Payne | 31 |
| Anton Pelizzari | Chad Payne | 31 |
| Cameron Nichols | Chad Payne | 31 |

5 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT a.nome_pessoa AS ator, d.nome_pessoa AS diretor, COUNT(DISTINCT ba.sk_movie_id) AS filmes_juntos
FROM bridge_movie_person ba
JOIN dim_people a ON a.sk_person_id = ba.sk_person_id AND a.tipo_pessoa = 'Ator'
JOIN bridge_movie_person bd ON bd.sk_movie_id = ba.sk_movie_id
JOIN dim_people d ON d.sk_person_id = bd.sk_person_id AND d.tipo_pessoa = 'Diretor'
GROUP BY a.sk_person_id, a.nome_pessoa, d.sk_person_id, d.nome_pessoa
ORDER BY filmes_juntos DESC
LIMIT 5
```

</details>

## Gêneros e produtoras

### Quantidade de filmes por gênero

Quantidade de filmes por gênero.

O primeiro resultado é Drama, com qtd filmes de 28.086.

| nome genero | qtd filmes |
| --- | --- |
| Drama | 28.086 |
| Documentary | 18.082 |
| Comedy | 16.048 |
| Horror | 8.674 |
| Thriller | 8.540 |
| Romance | 6.209 |
| Action | 5.028 |
| Animation | 3.911 |
| Crime | 3.902 |
| Tv Movie | 3.336 |
| Science Fiction | 3.218 |
| Family | 3.140 |
| Fantasy | 2.722 |
| Mystery | 2.713 |
| Music | 2.384 |
| Adventure | 2.376 |
| History | 1.993 |
| War | 804 |
| Western | 355 |

19 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT g.nome_genero, COUNT(DISTINCT bg.sk_movie_id) AS qtd_filmes
FROM dim_genres g
JOIN bridge_movie_genre bg ON bg.sk_genre_id = g.sk_genre_id
GROUP BY g.sk_genre_id, g.nome_genero
ORDER BY qtd_filmes DESC
```

</details>

### Produtora com maior lucro total

Produtora com maior lucro total.

O primeiro resultado é Marvel Studios, com lucro total brl de R$ 66.534.521.937,88.

| nome produtora | lucro total brl | qtd filmes |
| --- | --- | --- |
| Marvel Studios | R$ 66.534.521.937,88 | 19 |
| Universal Pictures | R$ 63.940.587.138,21 | 101 |
| Walt Disney Pictures | R$ 44.264.683.968,06 | 37 |
| Columbia Pictures | R$ 43.624.937.070,78 | 59 |
| Warner Bros. Pictures | R$ 38.516.333.904,02 | 68 |

5 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT c.nome_produtora, ROUND(SUM(f.lucro_brl), 2) AS lucro_total_brl, COUNT(DISTINCT f.sk_movie_id) AS qtd_filmes
FROM dim_companies c
JOIN bridge_movie_company bc ON bc.sk_company_id = c.sk_company_id
JOIN fact_movies_performance f ON f.sk_movie_id = bc.sk_movie_id
WHERE f.receita_brl > 0
GROUP BY c.sk_company_id, c.nome_produtora
ORDER BY lucro_total_brl DESC
LIMIT 5
```

</details>

### Gênero com maior margem de lucro média

Gênero com maior margem de lucro média.

O primeiro resultado é Horror, com margem media de 0,747.

| nome genero | margem media | qtd filmes |
| --- | --- | --- |
| Horror | 0,747 | 168 |
| Adventure | 0,687 | 246 |
| Animation | 0,683 | 97 |
| Science Fiction | 0,682 | 134 |
| Family | 0,676 | 142 |

5 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT g.nome_genero,
       ROUND(SUM(f.lucro_brl) * 1.0 / SUM(f.receita_brl), 4) AS margem_media,
       COUNT(DISTINCT f.sk_movie_id) AS qtd_filmes
FROM dim_genres g
JOIN bridge_movie_genre bg ON bg.sk_genre_id = g.sk_genre_id
JOIN fact_movies_performance f ON f.sk_movie_id = bg.sk_movie_id
WHERE f.receita_brl > 0
  AND f.orcamento_brl > 0
GROUP BY g.sk_genre_id, g.nome_genero
ORDER BY margem_media DESC
LIMIT 5
```

</details>

## Avaliações dos usuários

### Filmes mais avaliados pelos usuários

Filmes mais avaliados pelos usuários.

O primeiro resultado é Die Hart 2: Die Harter (2024), com qtd avaliacoes usuarios de 13.

| titulo | ano lancamento | qtd avaliacoes usuarios | nota media usuarios |
| --- | --- | --- | --- |
| Die Hart 2: Die Harter | 2024 | 13 | 4,99 |
| Die Hart 2: Die Harter | 2024 | 12 | 6,49 |
| Die Hart: Die Harter | 2024 | 11 | 5,56 |
| Die Hart: Die Harter | 2024 | 10 | 4,04 |
| Die Hart: Die Harter | 2024 | 10 | 5,97 |
| Die Hart: Die Harter | 2024 | 10 | 4,45 |
| Die Hart 2: Die Harter | 2024 | 10 | 5,42 |
| Die Hart 2: Die Harter | 2024 | 9 | 4,99 |
| Die Hart 2: Die Harter | 2024 | 9 | 5,04 |
| Die Hart 2: Die Harter | 2024 | 9 | 6,43 |

10 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT m.titulo, m.ano_lancamento, r.qtd_avaliacoes_usuarios, ROUND(r.nota_media_usuarios, 3) AS nota_media_usuarios
FROM dim_reviews r
JOIN dim_movies m ON m.sk_movie_id = r.sk_movie_id
ORDER BY r.qtd_avaliacoes_usuarios DESC
LIMIT 10
```

</details>

### Filmes em que a nota média dos usuários mais diverge da nota IMDb

Filmes em que a nota média dos usuários mais diverge da nota IMDb.

O primeiro resultado é Emesis Blue (2023), com divergencia de 4,87.

| titulo | ano lancamento | nota media usuarios | nota imdb | divergencia |
| --- | --- | --- | --- | --- |
| Emesis Blue | 2023 | 3,03 | 7,9 | 4,87 |
| Emesis Blue | 2023 | 3,13 | 7,9 | 4,77 |
| Emesis Blue | 2023 | 3,3 | 7,9 | 4,6 |
| Emesis Blue | 2023 | 3,51 | 7,9 | 4,39 |
| Emesis Blue | 2023 | 3,92 | 7,9 | 3,98 |
| Emesis Blue | 2023 | 4,1 | 7,9 | 3,8 |
| Emesis Blue | 2023 | 4,17 | 7,9 | 3,73 |
| Emesis Blue | 2023 | 4,3 | 7,9 | 3,6 |
| Emesis Blue | 2023 | 4,44 | 7,9 | 3,46 |
| Spider-man: Lotus | 2023 | 6,37 | 3,1 | 3,27 |

10 linha(s) vindas da camada Gold, em consulta somente leitura.

<details><summary>SQL</summary>

```sql
SELECT m.titulo, m.ano_lancamento,
       ROUND(r.nota_media_usuarios, 3) AS nota_media_usuarios,
       ROUND(f.nota_imdb, 3) AS nota_imdb,
       ROUND(ABS(r.nota_media_usuarios - f.nota_imdb), 3) AS divergencia
FROM dim_reviews r
JOIN dim_movies m ON m.sk_movie_id = r.sk_movie_id
JOIN fact_movies_performance f ON f.sk_movie_id = m.sk_movie_id
WHERE r.nota_media_usuarios IS NOT NULL
  AND f.nota_imdb IS NOT NULL
  AND r.qtd_avaliacoes_usuarios >= 5
ORDER BY divergencia DESC
LIMIT 10
```

</details>
