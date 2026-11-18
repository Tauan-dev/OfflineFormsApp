# Relatório da planilha real — DENDROMETRIA.xlsx_15-09_ATUAL.xlsx

Processado em 2026-11-17T17:49:26-03:00 · SHA-256 `07fdf7838a722b54ad9fcc821d826a275c0575845a3e0fd20e85de9a7523ff00`

## 1. Estrutura

- Planilhas: dendrometria, MAPA (processada: **dendrometria**; 'MAPA' contém apenas imagem).
- Linhas físicas: 1225 (cabeçalho + 1131 registros + 93 linhas vazias ignoradas).
- Cabeçalhos: Parcela, Árvore, Plantio, Replantio, Nome Comum, Data Medição, DAP (cm), HESG (m), HESGCOPA (m), HC (m), HT (m), Observação. Colunas M–Z vazias (sem valores).
- Plantio e Replantio: vazias em todos os registros.

## 2. Tipos reais das células (registros interpretados)

| Coluna | Tipos |
|---|---|
| Parcela | int: 1101, str: 30 |
| Árvore | int: 1117, str: 14 |
| Nome Comum | str: 1120, vazio: 11 |
| Data Medição | Timestamp: 1115, NaTType: 16 |
| DAP (cm) | texto: 747, data: 140, vazio: 130, decimal: 77, inteiro: 37 |
| HESG (m) | vazio: 547, inteiro: 306, texto: 242, decimal: 20, data: 16 |
| HESGCOPA (m) | inteiro: 702, vazio: 191, texto: 183, data: 39, decimal: 16 |
| HC (m) | vazio: 1069, inteiro: 53, texto: 9 |
| HT (m) | inteiro: 1007, vazio: 74, texto: 33, data: 9, decimal: 8 |
| Observação | vazio: 815, str: 316 |

## 3. Inconsistências encontradas

- **140 DAPs armazenados como data** pelo Excel (formato `d.m`; ex.: '12.4' virou 12/abr). Não reconstruídos: '12.05' e '12.5' geram a mesma data. Pista exibida apenas para revisão.
- **64 alturas armazenadas como data** (HESG, HESGCOPA, HT).
- **1 altura com número serial de data** (HT = 46151 na linha 299 ≈ 08/05/2026 → '8.5'); classificada EXTREMA e fora dos cálculos.
- **14 linhas de anotação de parcela** ('NÃO TEM ÁRVORES' na coluna Árvore): não são indivíduos nem mortos.
- 30 registros em parcelas com código alfanumérico (PX1–PX5), preservadas com ressalva.
- 59 observações mencionam morte ('MORTA'); sem coluna estruturada de estado vital.
- 49 DAPs vazios com lista de diâmetros/multifuste na observação; 72 menções de multifuste no total.
- 12 DAPs ausentes sem justificativa; 2 datas de medição ausentes.
- 12 registros com variação de grafia de espécie (Mucitaíba amarela / Mucitaíba-amarela), não unificados.
- 72 registros com 'Não identificada N'; 20 com dúvida de identificação na observação.
- Nenhuma duplicidade de Parcela + Árvore + Data; uma única campanha provável (19/05 a 28/08/2026).
- Números como texto ('45.5') são a maioria das células de DAP; interpretados por regra determinística.

## 4. Classificação dos registros

- VÁLIDO: 773
- VÁLIDO COM RESSALVA: 342
- INVÁLIDO: 14
- INCONCLUSIVO: 2
- Total: 1131

## 5. Indicadores calculados

| Indicador | Valor | Unidade | Elegíveis/potenciais | Status |
|---|---|---|---|---|
| Total de linhas importadas (físicas, incl. cabeçalho e vazias) | 1225 | linhas | — | VÁLIDO |
| Registros válidos | 773 | registros | — | VÁLIDO |
| Registros válidos com ressalva | 342 | registros | — | VÁLIDO |
| Registros inválidos | 14 | registros | — | VÁLIDO |
| Registros inconclusivos | 2 | registros | — | VÁLIDO |
| Parcelas identificadas | 103 | parcelas | — | VÁLIDO |
| Indivíduos únicos identificáveis | 1117 | indivíduos | — | VÁLIDO |
| Espécies identificadas (riqueza observada) | 76 | táxons | — | VÁLIDO COM RESSALVA |
| Medições dendrométricas | 1115 | medições | — | VÁLIDO |
| Cobertura de DAP | 77.0815 | % | 861/1117 | VÁLIDO |
| Cobertura de altura total (HT) | 93.7332 | % | 1047/1117 | VÁLIDO |
| DAPs ausentes | 12 | registros | — | VÁLIDO |
| DAPs inválidos | 140 | registros | — | VÁLIDO |
| Duplicidades de medição (Parcela + Árvore + Data) | 0 | registros | — | VÁLIDO |
| Possíveis campanhas | 1 | campanhas | — | VÁLIDO COM RESSALVA |
| Observações que exigem revisão | 239 | registros | — | VÁLIDO |
| Contagem de DAP elegíveis | 861 | valores | 861/1117 | VÁLIDO |
| Média aritmética do DAP | 26.5412 | cm | 861/1117 | VÁLIDO |
| Mediana de DAP | 20.4 | cm | 861/1117 | VÁLIDO |
| Mínimo de DAP | 1.5 | cm | 861/1117 | VÁLIDO |
| Máximo de DAP | 125 | cm | 861/1117 | VÁLIDO |
| 1º quartil de DAP | 13.4 | cm | 861/1117 | VÁLIDO |
| 3º quartil de DAP | 35.5 | cm | 861/1117 | VÁLIDO |
| Desvio-padrão amostral de DAP | 19.0945 | cm | 861/1117 | VÁLIDO |
| Coeficiente de variação de DAP | 71.9429 | % | 861/1117 | VÁLIDO |
| Contagem de HESG elegíveis | 568 | valores | 568/1117 | VÁLIDO |
| Média de HESG | 4.48176 | m | 568/1117 | VÁLIDO |
| Mediana de HESG | 3.85 | m | 568/1117 | VÁLIDO |
| Mínimo de HESG | 0.2 | m | 568/1117 | VÁLIDO |
| Máximo de HESG | 23 | m | 568/1117 | VÁLIDO |
| 1º quartil de HESG | 2.45 | m | 568/1117 | VÁLIDO |
| 3º quartil de HESG | 6 | m | 568/1117 | VÁLIDO |
| Desvio-padrão amostral de HESG | 2.95828 | m | 568/1117 | VÁLIDO |
| Coeficiente de variação de HESG | 66.0072 | % | 568/1117 | VÁLIDO |
| HESG ausentes | 533 | registros | 568/1117 | VÁLIDO |
| Contagem de HESGCOPA elegíveis | 901 | valores | 901/1117 | VÁLIDO |
| Média de HESGCOPA | 7.77289 | m | 901/1117 | VÁLIDO |
| Mediana de HESGCOPA | 7.5 | m | 901/1117 | VÁLIDO |
| Mínimo de HESGCOPA | 0.3 | m | 901/1117 | VÁLIDO |
| Máximo de HESGCOPA | 25 | m | 901/1117 | VÁLIDO |
| 1º quartil de HESGCOPA | 5 | m | 901/1117 | VÁLIDO |
| 3º quartil de HESGCOPA | 10 | m | 901/1117 | VÁLIDO |
| Desvio-padrão amostral de HESGCOPA | 4.0025 | m | 901/1117 | VÁLIDO |
| Coeficiente de variação de HESGCOPA | 51.4931 | % | 901/1117 | VÁLIDO |
| HESGCOPA ausentes | 177 | registros | 901/1117 | VÁLIDO |
| Contagem de HC elegíveis | 62 | valores | 62/1117 | VÁLIDO |
| Média de HC | 9.00806 | m | 62/1117 | VÁLIDO |
| Mediana de HC | 8 | m | 62/1117 | VÁLIDO |
| Mínimo de HC | 2.5 | m | 62/1117 | VÁLIDO |
| Máximo de HC | 20 | m | 62/1117 | VÁLIDO |
| 1º quartil de HC | 6.625 | m | 62/1117 | VÁLIDO |
| 3º quartil de HC | 10.75 | m | 62/1117 | VÁLIDO |
| Desvio-padrão amostral de HC | 3.81164 | m | 62/1117 | VÁLIDO |
| Coeficiente de variação de HC | 42.3137 | % | 62/1117 | VÁLIDO |
| HC ausentes | 1055 | registros | 62/1117 | VÁLIDO |
| Contagem de HT elegíveis | 1047 | valores | 1047/1117 | VÁLIDO COM RESSALVA |
| Altura total média (HT) | 13.5548 | m | 1047/1117 | VÁLIDO COM RESSALVA |
| Mediana de HT | 13 | m | 1047/1117 | VÁLIDO COM RESSALVA |
| Mínimo de HT | 0.3 | m | 1047/1117 | VÁLIDO COM RESSALVA |
| Máximo de HT | 33 | m | 1047/1117 | VÁLIDO COM RESSALVA |
| 1º quartil de HT | 10 | m | 1047/1117 | VÁLIDO COM RESSALVA |
| 3º quartil de HT | 17 | m | 1047/1117 | VÁLIDO COM RESSALVA |
| Desvio-padrão amostral de HT | 5.87148 | m | 1047/1117 | VÁLIDO COM RESSALVA |
| Coeficiente de variação de HT | 43.3165 | % | 1047/1117 | VÁLIDO COM RESSALVA |
| HT ausentes | 60 | registros | 1047/1117 | VÁLIDO |
| Área basal total (G) | 72.2627 | m² | 861/1117 | VÁLIDO |
| Área basal média por indivíduo elegível | 0.0839288 | m² | 861/1117 | VÁLIDO |
| Maior área basal individual | 1.22718 | m² | 861/1117 | VÁLIDO |
| Área das parcelas com área conhecida (A) | 1.4112 | ha | 839/1117 | VÁLIDO COM RESSALVA |
| Área basal por hectare | 50.9132 | m²/ha | 839/1117 | VÁLIDO COM RESSALVA |
| Diâmetro quadrático médio (dg) | 32.6897 | cm | 861/1117 | VÁLIDO |
| Área basal total incluindo multifustes | 72.953 | m² | 884/1117 | VÁLIDO COM RESSALVA |
| Volume cilíndrico total (g × HT) | 1457.44 | m³ | 858/1117 | VÁLIDO COM RESSALVA |
| Volume comercial — equação de Spurr (Jorge, 1982) | 63.8375 | m³ | 55/1117 | VÁLIDO COM RESSALVA |
| Comprimento médio de copa | 6.55455 | m | 897/1117 | VÁLIDO COM RESSALVA |
| Proporção média de copa | 45.5506 | % | 897/1117 | VÁLIDO COM RESSALVA |
| Índice de Shannon (H') | 4.03501 | nats/indivíduo | 1117/1117 | VÁLIDO COM RESSALVA |
| Equabilidade de Pielou (J') | 0.931716 | adimensional | 1117/1117 | VÁLIDO COM RESSALVA |
| Índice de Simpson (1 − D) | 0.979942 | adimensional | 1117/1117 | VÁLIDO COM RESSALVA |
| Mortalidade | — | % | — | BLOQUEADO POR QUALIDADE OU METODOLOGIA |
| Sobrevivência | — | % | — | BLOQUEADO POR QUALIDADE OU METODOLOGIA |

## 6. Indicadores bloqueados ou pendentes

- **Mortalidade** — BLOQUEADO POR QUALIDADE OU METODOLOGIA: O arquivo não possui estado vital estruturado (coluna 'Estado vital' com vivo / morto / não localizado / não avaliado). Menções de 'MORTA' em Observação são texto livre e não sustentam o cálculo. '36 − registros' nunca é usado como número de mortos.
- **Sobrevivência** — BLOQUEADO POR QUALIDADE OU METODOLOGIA: O arquivo não possui estado vital estruturado (coluna 'Estado vital' com vivo / morto / não localizado / não avaliado). Menções de 'MORTA' em Observação são texto livre e não sustentam o cálculo. '36 − registros' nunca é usado como número de mortos.
- **Indicador composto de saúde** — PENDENTE DE DEFINIÇÃO: Escala e interpretação não definidas (M12); fitossanidade fora deste arquivo.
- **Dano leve / dano severo** — PENDENTE DE DEFINIÇÃO: Não há coleta de gradação de dano (D6 / M2).
- **Classificação definitiva do povoamento** — PENDENTE DE DEFINIÇÃO: Limiares sem origem documentada (M13).
- **Diâmetro médio de referência do projeto** — PENDENTE DE DEFINIÇÃO: dg e média aritmética são calculados e definidos pela literatura; qual deles será o 'diâmetro médio' oficial do projeto é decisão M5 da equipe.
- **Multifuste sem padrão estrutural** — PENDENTE DE DEFINIÇÃO: Indícios de multifuste cujos fustes não podem ser extraídos sem ambiguidade (números por extenso, listas sem quantidade declarada, contagem divergente, DAP da coluna diferente dos fustes): revisão humana. Os extraíveis seguem a regra de Finger (1992).
- **Mortalidade baseada apenas em registros ausentes** — PENDENTE DE DEFINIÇÃO: Ausência de registro não é morte.
- **Mortalidade / sobrevivência** — PENDENTE DE DEFINIÇÃO: O desenho (36 plantas por parcela) é documentado na literatura, mas o arquivo não tem estado vital estruturado (vivo / morto / não localizado / não avaliado). Dado ausente, não lacuna de método.
- **Intensidade de serrapilheira** — PENDENTE DE DEFINIÇÃO: Sem escala definida (M10).
- **Ocorrência confirmada de fauna** — PENDENTE DE DEFINIÇÃO: Texto livre gera apenas menções potenciais.
- **Nota (*) da definição de HESGCOPA** — PENDENTE DE DEFINIÇÃO: A imagem de definições das siglas traz um asterisco sem a nota correspondente. Comprimento e proporção de copa são calculados pela definição fornecida, com ressalva.

## 7. Conferência independente (leitura direta das células)

Recalculado sem a camada `analytics`, com regra simplificada equivalente para estas parcelas.

| Parcela | n (indep.) | n (analisador) | DAP médio indep. (cm) | DAP médio analisador | G indep. (m²) | G analisador | Erro abs. G | Conclusão |
|---|---|---|---|---|---|---|---|---|
| 1 | 15 | 15 | 50.38 | 50.38 | 4.05441617121 | 4.05441617121 | 0.00e+00 | CONFERE |
| 14 | 31 | 31 | 38.59354839 | 38.59354839 | 5.13313620129 | 5.13313620129 | 0.00e+00 | CONFERE |
| 16 | 2 | 2 | 8.5 | 8.5 | 0.0132732289614 | 0.0132732289614 | 0.00e+00 | CONFERE |
| 49 | 11 | 11 | 65.69090909 | 65.69090909 | 4.46477335982 | 4.46477335982 | 0.00e+00 | CONFERE |
| 75 | 10 | 10 | 29.49 | 29.49 | 1.17941435782 | 1.17941435782 | 0.00e+00 | CONFERE |
| PX5 | 13 | 13 | 14.10769231 | 14.10769231 | 0.2115517077 | 0.2115517077 | 0.00e+00 | CONFERE |

## 8. Arquivos gerados

- `DENDROMETRIA.xlsx_15-09_ATUAL_indicadores.csv`
- `DENDROMETRIA.xlsx_15-09_ATUAL_manifesto.json`
- `DENDROMETRIA.xlsx_15-09_ATUAL_multifustes.csv`
- `DENDROMETRIA.xlsx_15-09_ATUAL_registros_excluidos.csv`
- `DENDROMETRIA.xlsx_15-09_ATUAL_relatorio.html`
- `DENDROMETRIA.xlsx_15-09_ATUAL_relatorio_planilha.md`
- `DENDROMETRIA.xlsx_15-09_ATUAL_resultados.xlsx`
