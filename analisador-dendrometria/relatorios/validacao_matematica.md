# Validação matemática dos indicadores

Analisador 1.1.0 · metodologia dendro-2026.11-r1. Gerado por `validar_indicadores.py`.

Critério: |produzido − esperado| ≤ atol + rtol·|esperado| (Burden & Faires). Erro relativo = erro absoluto / |esperado|.

| Indicador | Fórmula | Variáveis | Unidade | Fixture | Exemplo manual | Esperado | Produzido | Erro absoluto | Erro relativo | Tolerância | Conclusão |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Área seccional individual (g) | g = π·DAP²/40000 | DAP (cm) | m² | — | DAP = 20 cm → π·400/40000 | 0.0314159265358979 | 0.0314159265358979 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Área basal total (G) | G = Σ π·DAPᵢ²/40000 | DAPᵢ (cm) | m² | area_basal.csv | DAP 10, 20, 30 cm (seção 32) | 0.109955742875643 | 0.109955742875643 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Área basal média por indivíduo | Ḡ = G / n | G, n | m² | area_basal.csv | 0,109955742876 / 3 | 0.0366519142918809 | 0.0366519142918809 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Maior área basal individual | max(gᵢ) | gᵢ | m² | area_basal.csv | g(30) = π·900/40000 | 0.0706858347057703 | 0.0706858347057703 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Média aritmética do DAP | Σxᵢ/n | DAP | cm | valido.csv | 150/5 | 30 | 30 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| Mediana do DAP | valor central | DAP | cm | valido.csv | 10,20,[30],40,50 | 30 | 30 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| 1º quartil do DAP | tipo 7: x₍₁₊₀,₂₅·(n−1)₎ | DAP | cm | valido.csv | posição 1 → 20 | 20 | 20 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| 3º quartil do DAP | tipo 7: x₍₁₊₀,₇₅·(n−1)₎ | DAP | cm | valido.csv | posição 3 → 40 | 40 | 40 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| Mínimo do DAP | min | DAP | cm | valido.csv | 10 | 10 | 10 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| Máximo do DAP | max | DAP | cm | valido.csv | 50 | 50 | 50 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| Desvio-padrão amostral do DAP | √[Σ(xᵢ−x̄)²/(n−1)] | DAP | cm | valido.csv | √(1000/4) = √250 | 15.8113883008419 | 15.8113883008419 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-09 | APROVADO |
| Coeficiente de variação do DAP | s/x̄·100 | s, x̄ | % | valido.csv | 15,8113883/30·100 | 52.704627669473 | 52.704627669473 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-09 | APROVADO |
| Contagem de DAPs elegíveis | n | — | valores | valido.csv | 5 | 5 | 5 | 0.000e+00 | 0.000e+00 | atol=0; rtol=0 | APROVADO |
| Altura total média (HT) | Σ HTᵢ/n | HT | m | valido.csv | (8+12+15+18+20)/5 | 14.6 | 14.6 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| Volume cilíndrico total | Σ gᵢ·HTᵢ | DAP, HT | m³ | valido.csv | Σ π·DAP²/40000·HT | 7.68904801966102 | 7.68904801966102 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Volume comercial (Spurr) | Σ [b₀ + b₁·DAP²·HC] | DAP, HC | m³ | valido.csv | 2 árvores com HC: (20 cm, 6 m) e (40 cm, 8 m) | 1.024318026 | 1.024318026 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Indivíduos únicos | nº pares (Parcela, Árvore) | — | indivíduos | valido.csv | 5 | 5 | 5 | 0.000e+00 | 0.000e+00 | atol=0; rtol=0 | APROVADO |
| Riqueza observada | nº espécies distintas | — | táxons | valido.csv | Ipê, Cedro, Jatobá | 3 | 3 | 0.000e+00 | 0.000e+00 | atol=0; rtol=0 | APROVADO |
| Cobertura de DAP | elegíveis/potenciais·100 | — | % | valido.csv | 5/5·100 | 100 | 100 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=0 | APROVADO |
| Área basal por hectare (decisão do usuário) | ABₕₐ = G / A | G (m²), A (ha) | m²/ha | ab_hectare.csv | 0,424115 / 0,10 (exemplo do documento de fórmulas) | 4.24115008234622 | 4.24115008234622 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Área basal por hectare — parcela sem árvores na área | ABₕₐ = G / Σaⱼ | G, aⱼ | m²/ha | ab_hectare.csv | 0,424115 / (0,10 + 0,10) | 2.12057504117311 | 2.12057504117311 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Área basal por hectare — predefinição ESARM (144 m²) | ABₕₐ = G / Σaⱼ | G, aⱼ = 0,0144 ha | m²/ha | ab_hectare.csv | 0,424115 / (2 × 0,0144) | 14.7262155637022 | 14.7262155637022 | 1.776e-15 | 1.206e-16 | atol=1e-12; rtol=1e-09 | APROVADO |
| Diâmetro quadrático médio (literatura) | dg = √(Σ DAP² / n) | DAPᵢ (cm) | cm | ab_hectare.csv | √(5400 / 4) = √1350 | 36.7423461417477 | 36.7423461417477 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| Área basal com multifustes (Finger, 1992) | gᵢ = Σⱼ π·dᵢⱼ²/40000 | dᵢⱼ (cm) | m² | multifuste.csv | g(20) + π·169/40000 + g(44,4) + π·129,28/40000 | 0.209673035293236 | 0.209673035293236 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Comprimento médio de copa | HT − HESGCOPA | HT, HESGCOPA (m) | m | copa.csv | (10−4)=6; (20−5)=15; média 10,5 | 10.5 | 10.5 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| Proporção média de copa | (HT − HESGCOPA)/HT × 100 | HT, HESGCOPA (m) | % | copa.csv | 60 %; 75 %; média 67,5 % | 67.5 | 67.5 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| DAP equivalente (Stewart & Salazar, 1992) | d_eq = √(Σ dⱼ²) | dⱼ (cm) | cm | — | √(3² + 4² + 12²) = 13 | 13 | 13 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=1e-12 | APROVADO |
| Índice de Shannon (H') | −Σ pᵢ ln pᵢ | nᵢ | nats/ind. | valido.csv | p = 0,4; 0,4; 0,2 | 1.05492016798614 | 1.05492016798614 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Equabilidade de Pielou (J') | H' / ln S | H', S | — | valido.csv | 1,054920 / ln 3 | 0.960229717860761 | 0.960229717860761 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Índice de Simpson (1 − D) | 1 − Σ nᵢ(nᵢ−1)/[N(N−1)] | nᵢ, N | — | valido.csv | 1 − 4/20 | 0.8 | 0.8 | 0.000e+00 | 0.000e+00 | atol=1e-12; rtol=1e-09 | APROVADO |
| Dominância relativa (Cedro) | Gᵢ / G × 100 | DAP (cm) | % | valido.csv | (900+1600)/5500 × 100 | 45.4545454545455 | 45.4545454545455 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=0 | APROVADO |
| Mortalidade (estado vital estruturado) | mortos/implantados·100 | — | % | estado_vital.csv | 1/(36+36)·100 | 1.38888888888889 | 1.38888888888889 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=0 | APROVADO |
| Sobrevivência (estado vital estruturado) | vivos/implantados·100 | — | % | estado_vital.csv | 3/72·100 | 4.16666666666667 | 4.16666666666667 | 0.000e+00 | 0.000e+00 | atol=1e-09; rtol=0 | APROVADO |

**33 de 33 indicadores aprovados.**

## Indicadores não validados (bloqueados ou pendentes)

- Área basal por hectare na planilha real: calculada com a predefinição da literatura (arboreto ESARM, 144 m²; parcelas PX1–PX5 fora do desenho publicado ficam excluídas) — VÁLIDO COM RESSALVA.
- Escolha do 'diâmetro médio oficial' (média aritmética × dg) — decisão M5 da equipe.
- Multifustes sem padrão estrutural — revisão humana.
- Mortalidade/sobrevivência na planilha real — BLOQUEADO POR QUALIDADE OU METODOLOGIA (sem estado vital estruturado).
- Indicador de saúde, dano leve/severo, serrapilheira, classificação do povoamento, papel de Nota (*) da definição de HESGCOPA — não fornecida.

## Tolerâncias

- **contagem**: atol=0, rtol=0 — Contagens são inteiras: comparação exata.
- **dap_cm**: atol=1e-09, rtol=1e-12 — Estatísticas de DAP (cm): resolução de campo 0,1 cm ≫ 1e-9 cm.
- **altura_m**: atol=1e-09, rtol=1e-12 — Estatísticas de altura (m): resolução de campo 0,1 m ≫ 1e-9 m.
- **dispersao**: atol=1e-09, rtol=1e-09 — Desvio-padrão e CV envolvem raiz quadrada e divisão; rtol 1e-9.
- **area_basal_m2**: atol=1e-12, rtol=1e-09 — g ~ 1e-4 a 1 m²; atol 1e-12 m² e rtol 1e-9 cobrem o erro de π·d²/40000 em dupla precisão.
- **volume_m3**: atol=1e-12, rtol=1e-09 — Produto de g por altura ou polinômio de Spurr: mesma ordem de erro da área basal.
- **percentual**: atol=1e-09, rtol=0 — Percentuais (0–100): erro absoluto de 1e-9 ponto percentual.
- **indice**: atol=1e-12, rtol=1e-09 — Índices de diversidade (ordem 0–10): soma de termos p·ln p com math.fsum; atol 1e-12 e rtol 1e-9 ficam muito acima do erro de arredondamento.
