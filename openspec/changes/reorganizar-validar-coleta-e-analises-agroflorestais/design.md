# Design — Reorganização e validação integral da coleta, qualidade dos dados e análises agroflorestais

## Context

Ver `proposal.md` § Why para a motivação. Esta seção registra apenas o estado técnico verificado e as restrições que moldam a abordagem.

**Inventário do código inspecionado** (React Native 0.81.5 / Expo SDK 54 / TypeScript 5.9, 100% offline, sem backend):

```
src/
├── services/excelService.ts        ← escrita e leitura de CSV, cabeçalhos, contratos de entrada
├── storage/fileManager.ts          ← I/O em FileSystem.documentDirectory
├── storage/speciesStorage.ts       ← kv-store de espécies (expo-sqlite/kv-store, NÃO é banco relacional)
├── utils/validators.ts             ← validação de formulário
├── analytics/
│   ├── dataLoader.ts               ← ponto único de leitura → parse → cálculo
│   ├── dendrometryAnalytics.ts     ← DAP, alturas, área basal, distribuição, maior árvore
│   ├── phenologyAnalytics.ts       ← flores/frutos/folhas, distribuição fitossanitária bruta
│   ├── inventoryAnalytics.ts       ← cruzamento, espécies, saúde, alertas, por parcela
│   └── populationDynamicsAnalytics.ts ← coortes, replantio, classificação do povoamento
└── screens/*Stats*.tsx             ← camada de exibição
```

**Fluxo de dados atual** (verificado):

```
Form1/Form2 ──save──▶ excelService.saveToCsv ──▶ dendometria.csv / fenologia.csv
                                                          │
                                                          ▼
                                            dataLoader.loadDendroRows / loadFenolRows
                                                          │  parseCsv → parseDendroRows/parseFenologiaRows
                                                          ▼
                                    calcDendroStats · calcPhenologyStats · calcInventoryStats
                                    calcParcelaStats · calcPopulationDynamics
                                                          │
                                                          ▼
                                                   telas *Stats*.tsx
```

Dois pontos desse fluxo são estrangulamentos que explicam a maioria dos defeitos: **`parseCsv`** (toda corrupção estrutural entra aqui) e **`dataLoader`** (único lugar onde um relatório de qualidade pode ser produzido sem tocar em cada tela).

**Restrições invioláveis:** sem rede, sem backend, sem autenticação; os arquivos CSV já gravados no dispositivo devem permanecer legíveis; nenhuma conversão destrutiva.

## Goals / Non-Goals

**Goals (design-level):**

- Introduzir um **ponto único de normalização e validação** entre o parsing e o cálculo, para que nenhuma função analítica precise repetir `trim()`/`toLowerCase()`/filtros de DAP com regras próprias.
- Tornar o **relatório de qualidade um subproduto obrigatório do carregamento**, não uma tela paralela que reimplementa a leitura.
- Mudar o **contrato de saída dos analytics** de "número solto" para "valor + denominador + excluídos + motivo", de modo que a correção da apresentação seja consequência do contrato, não disciplina do desenvolvedor.
- Permitir evolução do modelo de coleta **por adição de colunas**, sem reescrever arquivos existentes.

**Non-Goals (design-level):**

- Não substituir CSV por banco relacional. O CSV é requisito do usuário (abre no Excel, é compartilhável, é auditável a olho nu). Introduzir SQLite resolveria integridade mas quebraria o fluxo de trabalho existente.
- Não introduzir framework de estado global, camada de ORM ou geração de código.
- Não escolher metodologia científica. Onde o design encontra uma lacuna metodológica, ele para e registra a pendência.

## Decisions

### D1 — Camada de normalização entre parse e cálculo, em vez de correção pontual em cada função

**Escolhido:** introduzir um estágio explícito `parse → normalizar/validar → registros canônicos + diagnósticos → cálculo`.

**Alternativa considerada:** corrigir cada função defeituosa no lugar (`trim()` em `calcCobertura`, alinhar `classificarFito`, uniformizar filtro de DAP). É menor e mais rápido.

**Por que a correção mínima não basta:** os defeitos confirmados são majoritariamente de *divergência entre lugares que deveriam concordar* — `calcCobertura` normaliza diferente de `calcParcelaStats`; `mediaDap` filtra diferente de `areaBasalTotal`; `calcInventoryStats` duplica a contagem de saúde de `calcParcelaStats`. Corrigir cada ponto preserva a estrutura que produz a divergência e garante que ela reapareça. O estágio único elimina a classe inteira de defeito, não as instâncias.

**Trade-off:** toca todos os arquivos de `src/analytics/`, aumentando a superfície de regressão. Mitigado pela Fase 1 ser puramente aditiva (o estágio novo roda e reporta antes de qualquer cálculo mudar de valor).

### D2 — Contrato de saída com denominador obrigatório

**Escolhido:** todo indicador quantitativo retorna valor, denominador, elegíveis, excluídos e motivos, em vez de `number | null`.

**Alternativa considerada:** manter `number | null` e adicionar campos de cobertura em paralelo. Menos invasivo.

**Por que não:** `null` hoje é ambíguo — significa simultaneamente "sem dados", "falha de leitura" e "não aplicável". `classificarPovoamento(mediaDap = null)` tratando ausência como limiar atendido é exatamente esse defeito materializado. Um tipo que não permite representar "valor sem denominador" torna o erro inexpressável.

**Trade-off:** as telas precisam ser ajustadas mesmo onde a exibição não muda.

### D3 — Reescrever `parseCsv` como máquina de estados sobre caracteres

**Escolhido:** varrer o texto inteiro caractere a caractere, alternando entre estado "dentro de aspas" e "fora de aspas", tratando `\r\n` dentro de aspas como conteúdo.

**Alternativa considerada:** adotar uma biblioteca de CSV.

**Por que não a biblioteca:** o escritor (`csvField`/`buildCsv`) já está correto e é trivial; o problema é exclusivamente o leitor. Introduzir dependência para corrigir ~30 linhas aumenta o tamanho do bundle offline sem ganho proporcional. A reescrita é pequena, testável exaustivamente e mantém a paridade escritor/leitor sob controle do projeto.

**Risco:** é o código que lê todos os dados históricos. Mitigado por bateria de testes de ida e volta antes de substituir, incluindo os casos que hoje falham.

### D4 — Evolução do CSV por adição de colunas ao final, identificada pelo cabeçalho

**Escolhido:** novas colunas (estado vital, motivo de ausência, fuste, registros ecológicos) são anexadas ao final do cabeçalho. A versão do formato é inferida do cabeçalho lido.

**Alternativa considerada:** arquivo de metadados com número de versão; ou migração que reescreve todos os arquivos.

**Por que não:** um arquivo de metadados pode se separar do CSV quando o usuário compartilha só o CSV — e o compartilhamento é um fluxo central do app. Reescrever arquivos existentes viola a restrição de não-destrutividade. Anexar ao final mantém a leitura posicional das colunas antigas válida e faz um arquivo antigo ser legível sem conversão: as colunas novas simplesmente vêm ausentes, o que o contrato canônico já sabe representar como "não coletado".

**Trade-off:** o cabeçalho cresce e a ordem das colunas passa a refletir história, não lógica. Aceitável frente à compatibilidade.

### D5 — Correção do vocabulário fitossanitário por mapeamento, não por reescrita de dados

**Escolhido:** `classificarFito` passa a operar sobre o vocabulário canônico `vivo | morto | com dano`, com mapeamento explícito de valores históricos e legados. Nenhum arquivo é reescrito.

**Alternativa considerada:** migrar os dados gravados para o vocabulário que a analítica espera (`bom`, `severo`…).

**Por que não:** os dados de campo são o registro primário; a analítica é derivada. Reescrever observações de campo para acomodar um bug de código é inaceitável cientificamente. Além disso, os valores gravados (`vivo`, `com dano`) são os semanticamente corretos — é o vocabulário da analítica que é espúrio, aparentemente herdado de outro modelo.

**Consequência a comunicar:** os números visíveis mudarão bruscamente. O indicador de saúde deve sair de permanentemente negativo para valores reais, e a lista de alertas deve encolher drasticamente. Isso precisa ser validado contra contagem manual antes de ser aceito como correto (Stage Gate 2).

### D6 — `pctDanoLeve` e `pctDanoSevero` removidos enquanto não houver coleta que os sustente

**Escolhido:** remover os indicadores de gradação de dano da saída e da apresentação, mantendo apenas presença de dano.

**Alternativa considerada:** manter os campos retornando zero.

**Por que não:** um indicador que retorna zero é lido pelo usuário como "não há dano severo", o que é uma afirmação sobre o campo que o sistema não tem base para fazer. Ausência de capacidade de medir não é ausência do fenômeno.

**Dependência:** se a metodologia decidir coletar gradação de dano, os indicadores voltam — mas como consequência da coleta, não antes dela.

### D7 — Política de DAP parametrizada e declarada, com o limiar em aberto

**Escolhido:** uma única política de elegibilidade aplicada a todos os indicadores de DAP, com os limiares expostos como configuração declarada e exibida ao usuário junto aos indicadores.

**Por que não fixar agora:** o limiar de 300 cm não tem origem localizável no repositório. Fixá-lo seria inventar metodologia. Parametrizá-lo permite implementar a *consistência* (que é o defeito confirmado) na Fase 2, e preencher o *valor* quando a decisão metodológica chegar, sem retrabalho estrutural.

## Risks / Trade-offs

| Risco | Mitigação |
|---|---|
| Correção da fitossanidade muda drasticamente números já vistos e mina a confiança do usuário no app | Stage Gate 2 exige validação contra contagem manual em um conjunto conhecido, com antes/depois documentado, antes de liberar |
| Reescrita de `parseCsv` corrompe leitura de dados históricos reais | Testes de ida e volta obrigatórios antes da substituição; leitura dos arquivos reais do dispositivo comparada registro a registro entre parser antigo e novo, com divergências analisadas individualmente |
| Mudança do contrato dos analytics gera regressão silenciosa nas telas | Fase 2 não altera nenhuma tela até que os cálculos estejam validados; a tipagem forte torna o não-tratamento do novo contrato um erro de compilação |
| Novas colunas quebram arquivos abertos em Excel pelo usuário | Colunas apenas ao final; cabeçalho detectável; arquivo antigo permanece válido |
| Escopo amplo leva a uma mudança que nunca fecha | Fases com Stage Gates independentes; Fases 1 e 2 entregam valor sozinhas e são aplicáveis sem as demais |
| Decisões metodológicas pendentes bloqueiam a implementação inteira | Fases 1, 2, 5 e 6 não dependem de nenhuma decisão metodológica. Apenas 3, 4 e 7 dependem |
| `saveToCsv` reescreve o arquivo inteiro a cada gravação; interrupção perde histórico | Gravação atômica (escrita em temporário + troca) na Fase 1; risco preexistente, não introduzido |

## Migration Plan

**Estratégia: aditiva e reversível por fase.** Nenhum arquivo de dados é reescrito, convertido ou apagado em nenhuma fase.

1. **Detecção** — na leitura, identificar a versão do formato pelo cabeçalho. Nenhuma ação se for a versão corrente.
2. **Backup** — antes da primeira gravação que use o cabeçalho novo, copiar o arquivo existente com sufixo datado no mesmo diretório. Verificar a cópia antes de prosseguir.
3. **Transformação** — não há transformação de conteúdo. Arquivos antigos são lidos com as colunas novas ausentes, representadas como "não coletado".
4. **Validação** — após a primeira gravação no formato novo, reler o arquivo e comparar a contagem de registros com a anterior. Divergência aborta e restaura o backup.
5. **Rollback** — restaurar o backup datado. Como nenhuma informação é destruída, o rollback é sempre possível enquanto o backup existir.
6. **Relatório** — informar ao usuário que a migração ocorreu, quantos registros foram preservados e onde está o backup.
7. **Falha** — em qualquer erro, manter o arquivo original intacto e reportar. O app permanece funcional em modo somente leitura sobre o formato antigo.

O cadastro local de espécies (`speciesStorage`) não é afetado: é um kv-store independente dos CSVs.

## Matriz de rastreabilidade

| # | Problema | Dado | Regra / fórmula | Arquivo · função | Tela consumidora | Spec | Critério de aceitação | Status |
|---|---|---|---|---|---|---|---|---|
| R1 | Vocabulário fitossanitário incompatível | `Estado Fitossanitário` | classificação por vocabulário canônico | `inventoryAnalytics.ts` · `classificarFito`, `ESTADOS_OK` | GeneralStats, InventoryParcela, Stats | `analises/fitossanidade` | Registro `"vivo"` classificado como saudável; `"com dano"` como danificado; zero registros em categoria residual | ERRO DE INTEGRAÇÃO · CONFIRMADO NO CÓDIGO |
| R2 | Alertas disparam para indivíduos saudáveis | `Estado Fitossanitário` | alerta apenas para estado problemático | `inventoryAnalytics.ts` · `alertasFito` | StatsScreen | `analises/fitossanidade` | Conjunto 100% `"vivo"` produz lista de alertas vazia | ERRO DE ALGORITMO · CONFIRMADO NO CÓDIGO |
| R3 | Gradação de dano sem entrada que a sustente | — | não reportar o que não se coleta | `inventoryAnalytics.ts` · `pctDanoLeve`, `pctDanoSevero` | GeneralStats, InventoryParcela | `analises/fitossanidade` | Indicadores de gradação ausentes da saída e da tela | INCOMPATIBILIDADE DE MODELO · CONFIRMADO NO CÓDIGO |
| R4 | Indicador de saúde sem denominador e sem escala | `Estado Fitossanitário` | `pctSaudavel − (pctDanoSevero + pctMorto)` sobre `length \|\| 1` | `inventoryAnalytics.ts` · `calcInventoryStats`, `calcParcelaStats` | GeneralStats, InventoryParcela | `analises/fitossanidade` | Sem registros avaliados ⇒ indisponível, nunca zero; denominador exibido | ERRO DE FÓRMULA · CONFIRMADO NO CÓDIGO |
| R5 | `mediaDap === null` satisfaz limiar de DAP alto | `DAP (cm)` | ausência ≠ limiar atendido | `populationDynamicsAnalytics.ts:419` · `classificarPovoamento` | PopulationDynamics | `analises/dinamica-povoamento` | Conjunto sem DAP nunca classifica como "Estabelecido" | ERRO DE FÓRMULA · CONFIRMADO NO CÓDIGO |
| R6 | Política de DAP inconsistente entre indicadores | `DAP (cm)` | política única de elegibilidade | `dendrometryAnalytics.ts` · `calcDendroStats` | DendrometryStats | `analises/dendrometria` | Média, mín, máx, área basal e distribuição usam o mesmo conjunto; excluídos reportados | ERRO DE ALGORITMO · CONFIRMADO NO CÓDIGO |
| R7 | Limiar de 300 cm sem origem | `DAP (cm)` | — | `dendrometryAnalytics.ts` | DendrometryStats | `analises/dendrometria` | Limiar declarado e exibido, ou substituído por decisão aprovada | DECISÃO METODOLÓGICA NECESSÁRIA |
| R8 | Contagem reconstruída de percentual arredondado | presença flores/frutos/folhas | contagem bruta ≠ `round(pct×total/100)` | `StatsScreen.tsx:320,326,332`; `phenologyAnalytics.ts` | StatsScreen | `analises/fenologia` | 1 de 3 exibe exatamente 1 | ERRO DE APRESENTAÇÃO · CONFIRMADO NO CÓDIGO |
| R9 | Intensidade numérica agregada como categoria | `Flores/Frutos/Folhas Intensidade` | variável numérica | `phenologyAnalytics.ts` · `countDistribution` | PhenologyStats | `analises/fenologia` | `"35"` e `"35,0"` não geram categorias distintas | ERRO DE ALGORITMO · CONFIRMADO NO CÓDIGO |
| R10 | Registro contado como indivíduo | Parcela + Árvore | indivíduo único no cruzamento | `inventoryAnalytics.ts` · `countEspecies`, `totalArvores` | InventoryStats | `analises/inventario` | Indivíduo nos dois arquivos conta 1 vez | ERRO DE REGRA DE NEGÓCIO · CONFIRMADO NO CÓDIGO |
| R11 | Ordenação por `totalDendro`, exibição de `totalGeral` | Nome Comum | abundância / frequência distintas | `inventoryAnalytics.ts` · `countEspecies` | InventoryStats | `analises/inventario` | Indicador ordenado e exibido pela mesma grandeza, rotulada | ERRO DE APRESENTAÇÃO · CONFIRMADO NO CÓDIGO |
| R12 | Chave de cruzamento não normalizada | Parcela + Árvore | normalização canônica única | `inventoryAnalytics.ts` · `calcCobertura` | InventoryStats | `dados/contrato-canonico`, `analises/inventario` | `"P1 "`+`"7"` cruza com `"p1"`+`"07"` conforme regra | ERRO DE IMPLEMENTAÇÃO · CONFIRMADO NO CÓDIGO |
| R13 | `interacoesFauna` = qualquer observação preenchida | Observações | indicador estruturado exige campo estruturado | `inventoryAnalytics.ts` · `interacoesFauna` | GeneralStats, InventoryParcela | `analises/inventario`, `coleta/formularios` | Observação sem menção a fauna não é contada | ERRO DE REGRA DE NEGÓCIO · CONFIRMADO NO CÓDIGO |
| R14 | `parseCsv` quebra em campo com aspas e newline | Observação | CSV com aspas | `excelService.ts` · `parseCsv` | todas | `dados/persistencia-csv` | Ida e volta preserva observação multilinha; nenhuma linha espúria | ERRO DE IMPLEMENTAÇÃO · CONFIRMADO NO CÓDIGO |
| R15 | Mapeamento posicional sem verificar cabeçalho | todas | cabeçalho é contrato | `dendrometryAnalytics.ts` · `parseDendroRows`; `phenologyAnalytics.ts` · `parseFenologiaRows` | todas | `dados/importacao`, `dados/persistencia-csv` | Coluna deslocada é detectada, não interpretada por posição | ERRO DE INTEGRAÇÃO · CONFIRMADO NO CÓDIGO |
| R16 | Falha de leitura vira conjunto vazio | arquivo | erro ≠ vazio | `dataLoader.ts` · `catch { return [] }` | todas | `dados/contrato-canonico` | Falha reportada; distinta de ausência de dados | ERRO DE IMPLEMENTAÇÃO · CONFIRMADO NO CÓDIGO |
| R17 | Exclusões silenciosas de cálculo | `DAP (cm)` | rastreabilidade obrigatória | `dendrometryAnalytics.ts` · filtro `dapsValidos` | DendrometryStats | `dados/qualidade` | Nº de excluídos e motivo acessíveis por indicador | ERRO DE IMPLEMENTAÇÃO · CONFIRMADO NO CÓDIGO |
| R18 | Parcela sem fenologia ordenada como pior saúde | Parcela | indisponível ≠ zero | `inventoryAnalytics.ts` · `calcParcelaStats` | InventoryParcela | `analises/inventario` | Parcela sem fenologia fora do ranking de saúde | ERRO DE APRESENTAÇÃO · CONFIRMADO NO CÓDIGO |
| R19 | Registro sem parcela vira parcela `"Sem parcela"` | Parcela | registro não identificável | `populationDynamicsAnalytics.ts` | PopulationDynamics | `dados/contrato-canonico` | Não incrementa total de parcelas; aparece na qualidade | ERRO DE APRESENTAÇÃO · CONFIRMADO NO CÓDIGO |
| R20 | `isReplanted` aceita qualquer texto; `extractYear` devolve lixo | `Replantio`, `Plantio` | semântica declarada do campo | `populationDynamicsAnalytics.ts` · `isReplanted`, `extractYear` | PopulationDynamics | `analises/dinamica-povoamento` | Texto não interpretável é reportado, não vira coorte | ERRO DE ALGORITMO · CONFIRMADO NO CÓDIGO |
| R21 | Replantio equiparado a mortalidade no laudo | `Replantio` | conceitos distintos | `populationDynamicsAnalytics.ts` · `interpretarDinamica`, `gerarTextoAutomatico` | PopulationDynamics | `analises/dinamica-povoamento` | Texto não afirma mortalidade a partir de replantio | ERRO DE REGRA DE NEGÓCIO · CONFIRMADO NO CÓDIGO |
| R22 | Limiares de classificação sem origem | vários | — | `populationDynamicsAnalytics.ts` | PopulationDynamics | `analises/dinamica-povoamento` | Limiar documentado ou indicador não apresentado como laudo | REGRA NÃO DEFINIDA |
| R23 | Estado vital e fitossanidade colapsados | `Estado Fitossanitário` | dimensões ortogonais | `Form2Screen.tsx:174` | Form2 | `coleta/formularios` | Vivo + com dano representável simultaneamente | ERRO DE REGRA DE NEGÓCIO · CONFIRMADO NO CÓDIGO |
| R24 | Sem motivo de ausência de medição | `DAP`, alturas | não medido ≠ zero ≠ N/A | `Form1Screen.tsx`, `validators.ts` | Form1 | `coleta/formularios`, `dados/contrato-canonico` | Motivo registrável em campo estruturado | DADO INSUFICIENTE |
| R25 | Sem representação de multifuste | — | indivíduo ≠ fuste | modelo de dados | Form1 | `coleta/formularios` | Multifuste não conta como 2 indivíduos | DADO INSUFICIENTE · HIPÓTESE A VALIDAR |
| R26 | Área basal por hectare não calculável | área da parcela | fator de expansão | — | DendrometryStats | `analises/dendrometria` | Não apresentar por hectare sem área e desenho amostral | BLOQUEADO POR AUSÊNCIA DE DADO |
| R27 | Mortalidade sem denominador de implantação | nº implantado/parcela | ausência de registro ≠ morte | — | PopulationDynamics | `analises/dinamica-povoamento` | Mortalidade indisponível sem denominador registrado | BLOQUEADO POR AUSÊNCIA DE DADO |
| R28 | Índice de diversidade não definido | Nome Comum | — | — | InventoryStats | `analises/inventario` | Apenas riqueza até aprovação de índice | DECISÃO METODOLÓGICA NECESSÁRIA |
| R29 | HESG e HESGCOPA coletadas e nunca analisadas | `HESG`, `HESGCOPA` | variável de altura declarada | `dendrometryAnalytics.ts` | DendrometryStats | `analises/dendrometria` | Participação declarada explicitamente | DECISÃO METODOLÓGICA NECESSÁRIA |
| R30 | "Maior indivíduo" sem critério nomeado | `DAP`, `HT` | critério explícito | `dendrometryAnalytics.ts` · `maiorArvore` | DendrometryStats | `analises/dendrometria` | Critério, unidade e data da medição apresentados | ERRO DE APRESENTAÇÃO · CONFIRMADO NO CÓDIGO |
| R31 | `saveToCsv` reescreve arquivo inteiro sem atomicidade | arquivo | integridade na gravação | `excelService.ts` · `saveToCsv` | todas | `dados/persistencia-csv` | Interrupção mantém conteúdo anterior recuperável | PROBLEMA RELACIONADO · CONFIRMADO NO CÓDIGO |
| R32 | Fitossanitário não obrigatório ⇒ vazio no denominador | `Estado Fitossanitário` | não avaliado ≠ saudável | `validators.ts` · `validatePhenology` | Form2, GeneralStats | `analises/fitossanidade` | Vazio não compõe denominador de condição | ERRO DE REGRA DE NEGÓCIO · CONFIRMADO NO CÓDIGO |

## Controle de escopo

**[ESCOPO ATUAL]** — R1–R6, R8–R21, R23, R24, R30–R32, mais a tela de qualidade de dados e a reorganização da navegação.

**[PROBLEMA RELACIONADO]** — R31 (atomicidade de gravação): preexistente e independente dos cálculos, mas endereçado aqui por baixo custo e alto impacto. R25 (multifuste): afeta a análise mas depende de decisão metodológica.

**[MELHORIA FUTURA]** — importação de Excel binário (a de CSV é escopo atual); busca textual assistida em observações históricas; índices de diversidade após aprovação; área basal por hectare após definição do desenho amostral; registros ecológicos estruturados além dos campos aprovados.

## Plano de execução por fases

### Fase 1 — Contrato de dados e diagnóstico

- **Critério de entrada:** proposta aprovada.
- **Dependências:** nenhuma. **Não depende de nenhuma decisão metodológica.**
- **Entregáveis:** `parseCsv` reescrito com máquina de estados; normalização canônica única de chaves, números e datas; tipos canônicos com estados ausente/zero/N/A/inválido; coleta de diagnósticos no `dataLoader`; gravação atômica; detecção de versão por cabeçalho.
- **Módulos:** `excelService.ts`, `fileManager.ts`, `dataLoader.ts`, novo módulo de normalização/diagnóstico.
- **Testes:** ida e volta do CSV (vírgula, aspas, multilinha, campo final vazio); normalização idempotente; leitura dos arquivos reais comparada entre parser antigo e novo.
- **Critério de saída:** nenhum valor de indicador muda nesta fase; o relatório de diagnóstico é produzido e os arquivos reais são lidos sem perda.
- **Rollback:** total — fase puramente aditiva no caminho de leitura.
- **Stage Gate 1:** o parser novo lê os arquivos reais do usuário com paridade registro a registro em relação ao antigo, e as divergências encontradas são todas explicadas por correção de bug (não por regressão).

### Fase 2 — Correções críticas dos cálculos

- **Critério de entrada:** Stage Gate 1 aprovado.
- **Dependências:** Fase 1. **Não depende de decisão metodológica** (os limiares ficam parametrizados com o valor atual até decisão).
- **Entregáveis:** R1–R6, R8–R13, R16–R21, R30, R32. Contrato de saída com denominador. Remoção da gradação de dano.
- **Módulos:** todos em `src/analytics/`; `StatsScreen.tsx` apenas onde a reconstrução de contagem exige.
- **Testes:** por indicador, entrada → cálculo manual → esperado → produzido → tolerância → conclusão. Casos: zero, ausência, inválido, extremo, divisão por zero, múltiplas parcelas, duplicidade, morto, com dano, DAP ausente.
- **Critério de saída:** todo indicador expõe denominador; nenhum indicador retorna zero para "sem dados"; cálculos conferem com verificação manual.
- **Rollback:** por indicador.
- **Stage Gate 2:** validação assistida pelo usuário em um conjunto conhecido, com antes/depois documentado, **especialmente do indicador de saúde e dos alertas**, cuja mudança será visualmente drástica.

### Fase 3 — Evolução do modelo de coleta

- **Critério de entrada:** Stage Gate 2 aprovado **e** decisões metodológicas M1, M2, M3 resolvidas.
- **Dependências:** Fases 1–2; decisões metodológicas.
- **Entregáveis:** estado vital separado da condição fitossanitária; motivo de ausência de medição; representação de multifuste; colunas novas anexadas ao final.
- **Módulos:** `Form1Screen.tsx`, `Form2Screen.tsx`, `validators.ts`, `excelService.ts`, contrato canônico.
- **Testes:** compatibilidade de leitura de arquivos da versão anterior; representação de vivo-com-dano; backup e rollback da migração.
- **Critério de saída:** arquivo antigo continua legível; novo registro preenche as colunas novas; migração reversível.
- **Rollback:** restauração do backup datado.
- **Stage Gate 3:** confirmação em dispositivo com dados reais de que nenhum registro foi perdido.

### Fase 4 — Métricas do arboreto

- **Critério de entrada:** Stage Gate 3 aprovado **e** decisões M4–M9 resolvidas.
- **Dependências:** Fase 3 (motivo de ausência e estado vital são entradas de mortalidade/sobrevivência).
- **Entregáveis:** métricas documentadas com entrada, fórmula, unidade, inclusão/exclusão, casos-limite e exemplo numérico. Métricas bloqueadas permanecem não implementadas e explicitamente listadas.
- **Testes:** exemplo numérico verificado manualmente por métrica.
- **Critério de saída:** nenhuma métrica implementada sem definição metodológica registrada.
- **Rollback:** por métrica.
- **Stage Gate 4:** conferência das métricas contra cálculo manual do usuário sobre os dados de validação.

### Fase 5 — Importação segura

- **Critério de entrada:** Stage Gate 1 aprovado (independe das Fases 2–4).
- **Dependências:** Fase 1.
- **Entregáveis:** seleção local, mapeamento de colunas, pré-visualização, validação bloqueante vs. aviso, detecção de colisão, preservação do original, resumo final. CSV primeiro; Excel conforme decisão de dependência offline.
- **Testes:** arquivo com colunas deslocadas, linhas quebradas, tipos incompatíveis, chaves duplicadas, registros sem parcela; importação em modo avião; cancelamento não grava nada.
- **Critério de saída:** nenhuma importação grava antes da confirmação; original preservado.
- **Rollback:** total — funcionalidade isolada.
- **Stage Gate 5:** importação de um arquivo real reconhecidamente problemático produzindo relatório de erros correto sem gravar dados inválidos.

### Fase 6 — Reorganização das telas

- **Critério de entrada:** Stage Gate 2 aprovado.
- **Dependências:** Fase 2 (as telas consomem o contrato novo). Independe das Fases 3–5.
- **Entregáveis:** blocos temáticos de análise; tela de qualidade dos dados; cobertura exibida em cada tela; acesso a exclusões.
- **Módulos:** `AppNavigator.tsx`, `StatsHomeScreen.tsx`, telas `*Stats*`.
- **Testes:** todas as análises previamente acessíveis continuam acessíveis; operação sem conectividade; tela sem dados distinta de tela com falha de leitura.
- **Critério de saída:** nenhuma análise correta foi removida; qualidade de dados no primeiro nível.
- **Rollback:** por rota.
- **Stage Gate 6:** navegação validada em dispositivo pelo usuário.

### Fase 7 — Migração, regressão e validação final

- **Critério de entrada:** Stage Gates das fases executadas aprovados.
- **Dependências:** todas as fases executadas.
- **Entregáveis:** execução da migração com backup, validação, rollback e relatório; suíte de regressão completa; matriz de rastreabilidade com resultado por linha.
- **Testes:** regressão de todas as funcionalidades existentes; operação offline ponta a ponta; coleta → gravação → leitura → cálculo → exibição → exportação → compartilhamento.
- **Critério de saída:** toda linha da matriz com resultado esperado atingido ou pendência registrada.
- **Rollback:** restauração de backup.
- **Stage Gate 7:** aceite final do usuário sobre os dados reais.

```
Fase 1 ──▶ Fase 2 ──▶ Fase 3 ──▶ Fase 4 ──┐
   │          │                            ├──▶ Fase 7
   │          └──▶ Fase 6 ─────────────────┤
   └──▶ Fase 5 ──────────────────────────  ┘

Fases 1, 2, 5, 6: sem bloqueio metodológico.
Fases 3, 4: bloqueadas por decisões metodológicas.
```

## Critérios para considerar a implementação concluída

1. Todo item [ESCOPO ATUAL] da matriz possui resultado verificado ou pendência formalmente registrada.
2. Nenhum indicador apresenta valor sem denominador e sem cobertura.
3. Nenhum registro é excluído de um cálculo sem aparecer no relatório de qualidade com motivo.
4. Os arquivos CSV preexistentes do usuário são lidos sem perda de registro nem de campo.
5. O aplicativo opera integralmente sem rede em todos os fluxos.
6. Nenhuma metodologia foi alterada ou introduzida sem decisão registrada e aprovada.
7. Todos os cálculos relevantes foram conferidos contra cálculo manual, com tolerância declarada.

## Decisões metodológicas pendentes

| ID | Decisão | Requisitos dependentes | Fase bloqueada |
|---|---|---|---|
| M1 | Categorias finais de **estado vital** | R23, `coleta/formularios` | 3 |
| M2 | Categorias finais de **condição fitossanitária**; haverá gradação de dano? | R3, R23, `analises/fitossanidade` | 3 |
| M3 | Lista final de **motivos de ausência de medição** | R24, `coleta/formularios` | 3 |
| M4 | **Limiar de plausibilidade de DAP** — origem dos 300 cm ou valor aprovado | R7, `analises/dendrometria` | 4 |
| M5 | **Diâmetro médio**: média aritmética ou diâmetro quadrático | `analises/dendrometria` | 4 |
| M6 | Papel de **HESG e HESGCOPA** nos indicadores | R29 | 4 |
| M7 | Critério de **"maior indivíduo"** — DAP, HT, área basal ou múltiplos rankings | R30 | 4 |
| M8 | **Índice de diversidade**, se algum | R28, `analises/inventario` | 4 |
| M9 | Definição de **"espécie mais frequente"** — abundância, frequência em parcelas ou frequência relativa | R11 | 4 |
| M10 | **Escala de intensidade de serrapilheira** | `coleta/formularios` | 4 |
| M11 | **Regra de composição de DAP multifuste** | R25 | 3 |
| M12 | **Escala e interpretação do indicador de saúde** | R4 | 2 (parametrizável; não bloqueia) |
| M13 | **Origem dos limiares** de classificação do povoamento | R22 | 4 |
| M14 | Regra de **normalização de zeros à esquerda** no número da árvore | R12 | 1 (decidível no contrato) |
| M15 | Contagem de indivíduo **replantado**: novo indivíduo ou substituição | `analises/dinamica-povoamento` | 4 |

## Informações necessárias para continuar

Os arquivos de referência citados na solicitação **não estão presentes** no diretório de trabalho nem em `C:\Users\Tauan Neres\Documents\CEPLAC\`. Sua ausência impede confirmar nos dados as hipóteses sobre corrupção e impede fixar a metodologia das métricas do arboreto:

1. **`MÉTRICAS PARA ESTUDO DO ARBORETO.docx`** — sem ele, M4 a M10 e M13 não podem ser resolvidas, e a Fase 4 não pode iniciar.
2. **`dendrometria_julho.xlsx`** — sem ele, as hipóteses de valores lidos como data, texto em coluna de DAP, linhas deslocadas, colunas deslocadas, chaves duplicadas, múltiplas campanhas e multifuste permanecem **não confirmadas nos dados**. A Fase 5 pode ser especificada, mas não validada contra o caso real.
3. **CSVs originais de dendrometria e fenologia** — necessários para o Stage Gate 1 (paridade do parser) e para o Stage Gate 2 (validação do indicador de saúde contra contagem manual).
4. **Número de indivíduos implantados por parcela**, com as exceções (parcelas incompletas, especiais, parcialmente perdidas) — sem esse dado registrado por parcela, mortalidade e sobrevivência permanecem não calculáveis (R27).
5. **Área das parcelas, unidade e desenho amostral** — sem eles, área basal por hectare permanece não calculável (R26).

Itens 1 a 3 podem ser disponibilizados copiando os arquivos para o diretório do projeto. Itens 4 e 5 são informações metodológicas do estudo.

## Open Questions

- A separação entre estado vital e condição fitossanitária deve ser retroativa na apresentação dos dados históricos, ou os dados antigos devem ser exibidos com a ressalva de terem sido coletados no modelo anterior? Não altera specs nem tarefas; é decisão de apresentação, resolvível na Fase 6.
- A importação de Excel binário exigirá um parser XLSX offline. A escolha da biblioteca é deferível até a Fase 5 e não afeta o contrato de importação, que é idêntico para CSV e Excel.
