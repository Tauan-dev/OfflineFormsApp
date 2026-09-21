# Reorganização e validação integral da coleta, qualidade dos dados e análises agroflorestais

## Why

O aplicativo já coleta dendrometria e fenologia offline e apresenta painéis de análise, mas a inspeção do código confirmou que **a camada analítica produz indicadores estruturalmente incorretos**, exibidos ao usuário como se fossem válidos. O caso mais grave: o formulário de fenologia grava exatamente `"vivo" | "morto" | "com dano"`, enquanto `classificarFito()` e `ESTADOS_OK` em `src/analytics/inventoryAnalytics.ts` classificam por um vocabulário totalmente diferente (`"bom"`, `"saudável"`, `"leve"`, `"severo"`…). Na prática, nenhuma árvore saudável é reconhecida como saudável, o "Indicador de Saúde" é permanentemente negativo e quase todo registro vira "⚠️ Alerta Fitossanitário".

Além disso, não existe contrato de dados, não existe tela de qualidade de dados, registros são excluídos silenciosamente dos cálculos, e o parser de CSV corrompe linhas quando a observação contém quebra de linha — exatamente o tipo de corrupção já observada nos dados históricos de julho. Sem um contrato canônico e sem rastreabilidade das exclusões, **nenhum número produzido hoje pelo app pode ser usado como evidência científica**.

Esta mudança é única e consolidada porque os problemas não são independentes: corrigir fitossanidade sem definir o vocabulário canônico, ou corrigir médias de DAP sem definir política de elegibilidade, apenas troca um erro por outro.

## What Changes

- **Contrato canônico de dados** para dendrometria, fenologia, inventário e dinâmica do povoamento: tipos, unidades, obrigatoriedade, e distinção explícita entre `zero`, `vazio`, `não medido` e `não aplicável`. Hoje essa distinção não existe — `toNum("")` e `toNum("MORTA")` produzem ambos `null`, indistinguíveis de um DAP legitimamente ausente.
- **BREAKING (metodológico, não de arquivo)**: correção do vocabulário fitossanitário. O indicador de saúde, os percentuais e os alertas passam a reconhecer `vivo`/`morto`/`com dano`. Valores históricos gravados permanecem intactos; muda apenas a interpretação.
- **BREAKING (metodológico)**: `classificarPovoamento()` deixa de tratar `mediaDap === null` como satisfazendo o limiar de DAP alto. Ausência de DAP passa a ser "indeterminado", nunca "Estabelecido".
- Política única e documentada de elegibilidade de DAP, aplicada de forma consistente a média, mínimo, máximo, área basal e distribuição diamétrica — hoje média/mín/máx usam DAP bruto (incluindo `0` e outliers) enquanto área basal e distribuição filtram `0 < DAP ≤ 300` silenciosamente.
- Contagens fenológicas passam a trafegar contagem bruta + denominador + percentual. A tela deixa de reconstruir contagens invertendo percentual arredondado (`Math.round(pct * total / 100)` em `StatsScreen.tsx`).
- Correção do parser CSV para respeitar campos entre aspas com quebra de linha, e normalização determinística das chaves `Parcela + Árvore` usadas no cruzamento dendro↔fenologia.
- **Nova capacidade: qualidade de dados** — tela e relatório expondo registros processados, válidos, rejeitados, duplicados, medições ausentes, exclusões de cálculo e o motivo de cada exclusão. Nada mais é descartado silenciosamente.
- **Nova capacidade: importação offline** de CSV/Excel com mapeamento de colunas, pré-visualização, validação bloqueante vs. aviso, e preservação do arquivo original.
- Evolução do modelo de coleta para separar **estado vital**, **condição fitossanitária** e **motivo de ausência de medição** — hoje colapsados num único campo de três opções, o que torna impossível representar multifuste, árvore tombada ou DAP não mensurável sem recorrer a texto livre.
- Métricas do arboreto (mortalidade, sobrevivência, área basal, diversidade, maior indivíduo, registros ecológicos, serrapilheira) especificadas com entrada, fórmula, unidade, critérios de inclusão/exclusão e exemplo numérico — **sem escolher metodologia que não esteja documentada**; toda lacuna vira decisão pendente registrada.
- Reorganização da navegação de Análises em blocos temáticos, preservando as telas cujo comportamento já está correto.
- Estratégia de compatibilidade e migração não destrutiva dos CSVs e do cadastro local de espécies.

Fora desta mudança: qualquer backend, API, sincronização em nuvem ou autenticação online. A aplicação permanece 100% offline.

## Capabilities

### New Capabilities

- `dados/contrato-canonico`: modelo canônico de dendrometria, fenologia e identidade de indivíduo/medição/campanha; tipos, unidades, valores sentinela, normalização de texto, números, datas, parcela e árvore; regras de duplicidade.
- `dados/qualidade`: relatório e tela de qualidade de dados; classificação de registros em aceito / aceito com ressalva / rejeitado; rastreabilidade obrigatória de toda exclusão de cálculo.
- `dados/importacao`: importação offline de CSV e Excel com seleção local, mapeamento de colunas, pré-visualização, validação bloqueante vs. aviso e preservação do original.
- `dados/persistencia-csv`: leitura/escrita de CSV, incluindo campos entre aspas com quebra de linha, BOM, integridade do arquivo e compatibilidade com os arquivos existentes.
- `coleta/formularios`: modelo de coleta — estado vital, condição fitossanitária, motivo de ausência de medição, fuste, replantio e registros ecológicos.
- `analises/dendrometria`: DAP, alturas (HESG, HESGCOPA, HC, HT), área basal, distribuição diamétrica, maior indivíduo.
- `analises/fenologia`: flores, frutos, folhas — presença, intensidade, estágio; contagens brutas e denominadores.
- `analises/fitossanidade`: classificação fitossanitária, percentuais, indicador de saúde e alertas.
- `analises/inventario`: cruzamento dendrometria × fenologia, espécies, abundância, frequência, riqueza, diversidade, análise por parcela.
- `analises/dinamica-povoamento`: coortes, replantio, mortalidade, sobrevivência e classificação do povoamento.
- `navegacao/analises`: organização das telas de análise e exposição obrigatória da qualidade dos dados.

### Modified Capabilities

Nenhuma. O diretório `openspec/specs/` está vazio — esta é a primeira formalização de specs do projeto, portanto todas as capacidades acima são novas mesmo quando descrevem código já existente.

## Impact

**Código confirmado como afetado:**

| Arquivo | Natureza do impacto |
|---|---|
| `src/analytics/inventoryAnalytics.ts` | Vocabulário fitossanitário, `classificarFito`, `ESTADOS_OK`, `countEspecies`, normalização de chave em `calcCobertura` |
| `src/analytics/dendrometryAnalytics.ts` | Política de elegibilidade de DAP, `maiorArvore` (critério), classes diamétricas, contrato de saída |
| `src/analytics/phenologyAnalytics.ts` | Contagem bruta + denominador; tratamento de `intensidade` numérica hoje agregada como categoria textual |
| `src/analytics/populationDynamicsAnalytics.ts` | `classificarPovoamento` com `mediaDap === null`; semântica de `replantio`; denominador de mortalidade |
| `src/analytics/dataLoader.ts` | Passa a propagar relatório de qualidade junto com as estatísticas; hoje engole exceções com `catch { return [] }` |
| `src/services/excelService.ts` | `parseCsv` (quebra de linha em campo com aspas), contrato de cabeçalhos, versionamento de arquivo |
| `src/utils/validators.ts` | Validação alinhada ao contrato canônico; `fitossanitario` hoje não é obrigatório |
| `src/screens/Form1Screen.tsx`, `src/screens/Form2Screen.tsx` | Novos campos de estado vital / motivo de ausência; `FITOSSANITARIO_OPTIONS` |
| `src/screens/StatsScreen.tsx` | Remoção da reconstrução de contagem a partir de percentual arredondado |
| `src/screens/GeneralStatsScreen.tsx`, `InventoryParcelaScreen.tsx`, `InventoryStatsScreen.tsx`, `DendrometryStatsScreen.tsx`, `PhenologyStatsScreen.tsx`, `PopulationDynamicsScreen.tsx` | Consumo dos novos contratos e exibição de cobertura/exclusões |
| `src/navigation/AppNavigator.tsx`, `src/screens/StatsHomeScreen.tsx` | Reorganização das rotas de análise |

**Dados:** os arquivos `dendometria.csv` e `fenologia.csv` já gravados no dispositivo devem continuar legíveis. Nenhuma conversão destrutiva. Qualquer migração exige backup, validação e rollback.

**Dependências:** a importação de arquivos exigirá um seletor de documentos local (ex.: `expo-document-picker`) e, para Excel, um parser XLSX offline. Ambas são decisões de design, não de escopo — nenhuma introduz dependência de rede.

**Riscos:** corrigir a fitossanidade mudará visivelmente os números já vistos pelo usuário (o indicador de saúde deve sair de permanentemente negativo para valores reais). Isso é a correção, não uma regressão, mas precisa ser comunicado e validado contra contagem manual antes de ser aceito.

**Bloqueio conhecido:** `MÉTRICAS PARA ESTUDO DO ARBORETO.docx`, `dendrometria_julho.xlsx` e os CSVs originais **não estão presentes** no diretório de trabalho. Sem eles, as hipóteses sobre os dados (valores lidos como data, `"MORTA"` em coluna de DAP, linhas deslocadas, multifuste, 36 indivíduos por parcela) permanecem **não confirmadas nos dados**, e as métricas do arboreto não podem ter sua metodologia fixada. Ver `design.md` §Pendências.
