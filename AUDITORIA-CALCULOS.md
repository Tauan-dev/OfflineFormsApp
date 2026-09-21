# Auditoria dos Cálculos — OfflineFormsApp (Coleta Verde)

Documento de referência gerado a partir de revisão manual, linha a linha, de toda a
camada de cálculo do app (`src/analytics/`) contra o que os formulários (`Form1Screen`,
`Form2Screen`) realmente coletam e contra o que cada tela de BI exibe.

**Este documento apenas descreve o estado atual e os problemas encontrados. Nenhuma
correção foi implementada.**

Última atualização: 2026-09-21.

---

## 1. Contexto da aplicação

**O que é:** OfflineFormsApp ("Coleta Verde") é um aplicativo de campo da CEPLAC para
coleta **offline** de dados de inventário florestal/agroflorestal — medições de
**dendrometria** (estrutura/crescimento das árvores: diâmetro, alturas) e
**fenologia** (fenômenos biológicos: floração, frutificação, folhas, estado
fitossanitário), organizadas por **parcela** e **árvore**. Depois de coletados, os
dados alimentam telas de estatística/BI no próprio dispositivo, sem depender de
conexão com a internet ou de um backend.

**Stack técnica:**
- React Native `0.81.5` + Expo SDK `54` (managed workflow), TypeScript, React `19.1`.
- Navegação: `@react-navigation/native-stack`
  ([AppNavigator.tsx](src/navigation/AppNavigator.tsx)).
- Sem backend/API — app 100% offline por design.
- Persistência dos registros de campo: dois arquivos **CSV** (`dendometria.csv`,
  `fenologia.csv`) gravados no `documentDirectory` do dispositivo via
  `expo-file-system` ([fileManager.ts](src/storage/fileManager.ts)). Não há banco de
  dados relacional para os registros de formulário.
- `expo-sqlite/kv-store` aparece nas dependências, mas é usado **apenas** como um
  key-value store simples para persistir a lista de espécies cadastradas pelo usuário
  ([speciesStorage.ts](src/storage/speciesStorage.ts): `DEFAULT_SPECIES` + espécies
  adicionadas em campo) — não guarda nenhum dado de dendometria/fenologia.
- Compartilhamento dos CSVs via `expo-sharing`
  ([DataScreen.tsx](src/screens/DataScreen.tsx)) — o técnico pode exportar/enviar o
  arquivo (WhatsApp, e-mail, Drive) para abrir depois em Excel/LibreOffice.

**Navegação / telas** ([AppNavigator.tsx](src/navigation/AppNavigator.tsx)):

```
Entry (tela inicial)
  └─ Home (menu principal)
       ├─ Form1  "Dendometria"      → formulário de dendrometria
       ├─ Form2  "Fenologia"        → formulário de fenologia
       ├─ Data   "Dados Salvos"     → ver/compartilhar/apagar os CSVs
       └─ StatsHome "Análises"      → menu de estatísticas
            ├─ DendrometryStats     "🌳 Dendometria"
            ├─ PhenologyStats       "🌸 Fenologia"
            ├─ InventoryStatsHome   "🌿 Inventário"
            │    ├─ InventoryStats     "🌿 Visão Geral"
            │    └─ InventoryParcela   "📍 Análise por Parcela"
            ├─ PopulationDynamics   "🌱 Dinâmica do Povoamento"
            └─ GeneralStats         "📊 Visão Geral" (dashboard consolidado)
```

**Formulários e campos coletados:**

- **Form1 — Dendometria** (grava em `dendometria.csv`, ver `DENDOMETRY_HEADERS` em
  [excelService.ts:155](src/services/excelService.ts#L155)): Parcela, Árvore,
  Plantio (data), Replantio (data, opcional), Nome Comum (espécie, via
  `SpeciesSelector`), Data Medição, DAP (cm), HESG (m), HESGCOPA (m), HC (m), HT (m),
  Observação.
- **Form2 — Fenologia** (grava em `fenologia.csv`, ver `PHENOLOGY_HEADERS` em
  [excelService.ts:200](src/services/excelService.ts#L200)): Parcela, Árvore, Nome
  Comum, e para cada um dos grupos **Flores / Frutos / Folhas** → Presença +
  Intensidade (0–100%) + Estágio; **Estado Fitossanitário** (select fixo — ver Seção
  3); Observações.

A chave `Parcela + Árvore` é o que permite cruzar um registro de dendrometria com um
de fenologia da mesma árvore — é essa chave que `inventoryAnalytics.ts` usa para
combinar as duas fontes (ver Seção 2 e o item 4.7).

**Fluxo de uso esperado em campo:** o técnico abre o app sem internet, escolhe
Dendometria e/ou Fenologia, preenche um formulário por árvore (podendo repetir
"salvar e continuar" para a mesma parcela), os dados vão se acumulando nos dois CSVs
locais, e a qualquer momento ele pode abrir "Análises" para ver estatísticas já
calculadas sobre o que foi coletado até ali, ou "Dados Salvos" para exportar o CSV.

---

## 2. Visão geral da arquitetura de dados e cálculo

```
Form1Screen (Dendometria)          Form2Screen (Fenologia)
  parcela, árvore, plantio,          parcela, árvore, espécie,
  replantio (data), espécie,         flores/frutos/folhas
  DAP, HESG, HESGCOPA, HC, HT        (presença+intensidade+estágio),
        │                            Estado Fitossanitário
        ▼                                  │
  dendometria.csv                          ▼
        │                            fenologia.csv
        └──────────────┬───────────────────┘
                        ▼
              src/analytics/*.ts
     ┌──────────────────┼───────────────────┐
     ▼                  ▼                   ▼
dendrometryAnalytics  phenologyAnalytics  inventoryAnalytics
     .ts                  .ts             (cruza os dois)
                                                │
                                                ▼
                                  populationDynamicsAnalytics.ts
                                  (coortes, replantio, classificação)
                        │
                        ▼
        Telas de BI (StatsScreen, GeneralStatsScreen,
        DendrometryStatsScreen, PhenologyStatsScreen,
        InventoryStatsScreen, InventoryParcelaScreen,
        PopulationDynamicsScreen)
        — apenas formatam/exibem os números já calculados,
          não recalculam nada por conta própria (exceto os
          pontos listados no item 4 abaixo).
```

**Formato dos dados:** CSV com BOM UTF-8, separador vírgula, decimal aceito com `,` ou `.`
(`toNum()` em `dendrometryAnalytics.ts` converte `,`→`.`). Sem cabeçalho re-lido (a
primeira linha do CSV é sempre descartada como header ao carregar).

**Campo "Estado Fitossanitário" (Form2Screen):** é um `SelectField` com opções
**fixas e únicas**: `FITOSSANITARIO_OPTIONS = ["vivo", "morto", "com dano"]`
([Form2Screen.tsx:174](src/screens/Form2Screen.tsx#L174)). Isso é central para o
Bug #1 abaixo.

---

## 3. 🔴 Bug crítico — Indicador de Saúde e Alertas Fitossanitários quebrados

**Onde:** [inventoryAnalytics.ts](src/analytics/inventoryAnalytics.ts) — funções
`classificarFito()` (linha 191) e `alertasFito()` (linha 139).

**O que acontece:**

```
Form2Screen só grava:        classificarFito() reconhece por palavra-chave:
  "vivo"                       KW_SAUDAVEL  = bom, boa, saudável, normal, ótimo
  "morto"                      KW_DANO_LEVE = leve, médio, moderado, amarelo, atacado
  "com dano"                   KW_DANO_SEV  = severo, grave, crítico, seco, doente
                                KW_MORTO     = morto, morta, dead, seco

  "vivo"      → não bate em nenhuma lista → cai em "outro" (descartado)
  "com dano"  → não bate em nenhuma lista → cai em "outro" (descartado)
  "morto"     → bate em KW_MORTO → ✓ único caso classificado corretamente
```

**Consequências mensuráveis:**

- `pctSaudavel`, `pctDanoLeve`, `pctDanoSevero` (calculados em `calcInventoryStats` e
  `calcParcelaStats`) ficam estruturalmente perto de zero, **independente da real
  condição das árvores em campo**, porque nenhum registro `"vivo"` ou `"com dano"` é
  contado nessas categorias.
- `indicadorSaude = pctSaudavel - (pctDanoSevero + pctMorto)` — exibido como
  "Indicador de Saúde" / "Condição Geral da Área" em
  [GeneralStatsScreen.tsx:211-218](src/screens/GeneralStatsScreen.tsx#L211) e por
  parcela em [InventoryParcelaScreen.tsx](src/screens/InventoryParcelaScreen.tsx) —
  não reflete a realidade: uma área 100% saudável ("vivo") tende a mostrar indicador
  baixo ou zerado, porque nenhuma árvore viva é contada como "saudável".
- `alertasFito()` usa `ESTADOS_OK = ["bom","boa","normal","saudável","saudavel"]`
  ([inventoryAnalytics.ts:137](src/analytics/inventoryAnalytics.ts#L137)). Como
  `"vivo"` não está nessa lista, **toda árvore viva também é listada como
  "⚠️ Alerta Fitossanitário"** na seção Inventário de
  [StatsScreen.tsx:508-520](src/screens/StatsScreen.tsx#L508).

**Resumo do impacto:** os únicos números confiáveis hoje relacionados a saúde são os
que dependem exclusivamente de `pctMorto` (contagem literal de `"morto"`). Todo o
restante do indicador de saúde e os alertas fitossanitários estão, na prática,
mostrando dados que não correspondem à condição real das árvores.

**Nota:** em `phenologyAnalytics.ts`, a distribuição bruta do campo fitossanitário
(`countDistribution`, usada em `PhenologyStatsScreen`) **não** tem esse problema —
ali os valores `"vivo"/"morto"/"com dano"` são apenas contados literalmente, sem
tentativa de reclassificação por palavra-chave. O bug existe apenas na
reclassificação feita em `inventoryAnalytics.ts`.

---

## 4. 🟠 Outros problemas confirmados

### 4.1 "Espécie mais frequente" não é necessariamente a mais frequente

**Onde:** `countEspecies()` em
[inventoryAnalytics.ts:74-134](src/analytics/inventoryAnalytics.ts#L74).

- A lista `topEspecies` (e, por consequência, `especieMaisFrequente` e
  `top3Especies`) é ordenada por `b.totalDendro - a.totalDendro` (linha 132),
  ignorando `totalFenol` como critério primário — apesar de existir o campo
  `totalGeral = totalDendro + totalFenol` já calculado.
- Uma espécie com poucos registros de dendometria mas muitos de fenologia nunca
  aparece no topo, mesmo tendo `totalGeral` maior que outras.
- O campo `pct` de cada espécie (linha 123-127) é calculado só sobre
  `dendroRows.filter(...).length`, ignorando fenologia. Uma espécie presente
  **somente** na fenologia (não aparece em nenhum registro de dendometria)
  mostra `pct: 0%`, mesmo tendo dezenas de observações.
- A variável `totalIndividuos` (linhas 99-113) é calculada mas **nunca usada** —
  código morto que sugere uma tentativa anterior de calcular o percentual de forma
  diferente (talvez sobre o total combinado), abandonada no meio.

### 4.2 Contagem reconstruída a partir de percentual arredondado (fenologia)

**Onde:** [StatsScreen.tsx:318-335](src/screens/StatsScreen.tsx#L318).

```ts
count={Math.round((stats.pctFlores * stats.total) / 100)}
```

- A interface `PhenologyStats` não expõe as contagens brutas (`comFlores`,
  `comFrutos`, `comFolhas`), só os percentuais já arredondados. A tela reconstrói
  a contagem revertendo o arredondamento.
- Em amostras pequenas isso produz um número exibido diferente do real. Exemplo:
  1 árvore com flor em 200 → `pctFlores = round(1/200*100) = round(0.5) = 1%` →
  reconstrução: `round(1*200/100) = round(2.0) = 2`. A tela mostraria **"2"**
  onde a contagem real é **1**.

### 4.3 `classificarPovoamento` trata "sem dado de DAP" como "DAP alto"

**Onde:**
[populationDynamicsAnalytics.ts:417-422](src/analytics/populationDynamicsAnalytics.ts#L417).

```ts
if ((mediaDap === null || mediaDap >= 15) && taxaReplantio <= 10 && numEspecies >= 3)
  → classificação "Estabelecido"
```

- Quando não há nenhum DAP medido (`mediaDap === null`), a condição é tratada como
  satisfeita (equivalente a um DAP alto), o que é o oposto do que faria sentido
  (ausência de dado ≠ povoamento maduro).

### 4.4 Filtragem de DAP inconsistente entre métricas

**Onde:** [dendrometryAnalytics.ts](src/analytics/dendrometryAnalytics.ts).

- `mediaDap`, `maxDap`, `minDap` (linhas 135-138) usam **todos** os valores de DAP
  não-nulos, incluindo `0` ou valores `> 300 cm`.
- `areaBasalTotal` (linha 193-201) e `distribuicaoDiametrica` (linha 203-227) usam
  apenas `dapsValidos = daps.filter(d => d > 0 && d <= 300)` — excluem
  silenciosamente `DAP ≤ 0` e `DAP > 300`.
- Resultado: é possível, por exemplo, `minDap` mostrar `0 cm` enquanto essa mesma
  árvore nunca aparece em nenhuma faixa da distribuição diamétrica nem contribui
  para a área basal — sem nenhum aviso na tela sobre a exclusão.
- O formulário (`validators.ts`, `validatePositiveNumber`) só rejeita valores
  negativos — `DAP = 0` passa na validação de entrada normalmente.

### 4.5 Percentuais que não somam 100%

**Onde:** praticamente todos os "breakdowns" (top espécies, classes diamétricas,
estágios fenológicos, categorias de saúde) em `dendrometryAnalytics.ts`,
`phenologyAnalytics.ts` e `inventoryAnalytics.ts`.

- Cada percentual é calculado com `Math.round()` de forma independente por
  categoria (não há distribuição do resto / "largest remainder method"). A soma
  exibida de todas as categorias de uma mesma distribuição pode dar, por exemplo,
  99% ou 101%. Efeito cosmético, mas pode gerar dúvida em quem lê o relatório em
  campo.

### 4.6 Palavra-chave duplicada sem efeito prático

**Onde:**
[inventoryAnalytics.ts:180-189](src/analytics/inventoryAnalytics.ts#L180) —
`"seco"` aparece tanto em `KW_DANO_SEV` quanto em `KW_MORTO`.

- Como a ordem de checagem em `classificarFito()` testa `morto` antes de
  `danoSevero`, a entrada de `"seco"` em `KW_DANO_SEV` nunca tem efeito — é
  código redundante/confuso. Reforça o diagnóstico do Bug #1: essas listas foram
  escritas pensando em um vocabulário de texto livre que o app nunca chegou a
  usar (o campo é um select fixo desde sempre, aparentemente).

### 4.7 Chave de cruzamento de cobertura não normalizada

**Onde:** `calcCobertura()` em
[inventoryAnalytics.ts:158-168](src/analytics/inventoryAnalytics.ts#L158).

```ts
const keysFenol = new Set(fenolRows.map((r) => `${r.parcela}|${r.arv}`));
const cruzadas = dendroRows.filter((r) => keysFenol.has(`${r.parcela}|${r.arv}`));
```

- Diferente de outras funções do mesmo arquivo (ex.: `calcParcelaStats`), aqui
  `parcela` e `arv` não passam por `.trim()` antes da comparação. Se algum CSV for
  editado manualmente fora do app (Excel/LibreOffice) e ganhar espaços extras, o
  cálculo de `coberturaDados` (% de árvores com dendometria E fenologia) pode ser
  subestimado. Baixo risco no fluxo normal do app (os campos vêm de `Input` com
  `keyboardType="numeric"`), mas vale registrar.

### 4.8 `isReplanted()` cobre um formato de dado que o formulário não produz

**Onde:** [populationDynamicsAnalytics.ts:110-123](src/analytics/populationDynamicsAnalytics.ts#L110).

- A função trata o campo `replantio` como podendo ser um texto booleano
  (`"não"`, `"n"`, `"0"`, `"false"`, `"no"` → não replantado; qualquer outro
  texto não vazio → replantado).
- Mas no formulário, `replantio` é um `DateInput` validado por `validateDate()`
  (formato `DD/MM/AAAA`) — na prática, o campo só é sempre vazio (`""`) ou uma
  data válida, nunca literalmente `"não"`/`"false"`/etc. Não é um bug ativo
  (o comportamento resultante está correto: vazio = não replantado, data = 
  replantado), mas é código defensivo para um formato de dado que o app atual
  nunca gera — indício de que a função foi escrita para uma versão diferente do
  formulário, ou pensando em edição manual do CSV.

---

## 5. Resumo por severidade

| # | Severidade | Item | Afeta |
|---|---|---|---|
| 3 | 🔴 Crítica | Vocabulário `vivo/morto/com dano` não bate com keywords de `classificarFito`/`alertasFito` | Indicador de Saúde (geral e por parcela), Alertas Fitossanitários |
| 4.1 | 🟠 Média | "Espécie mais frequente" ranqueada só por dendometria | Espécie Mais Frequente, Top 3/8 Espécies, `pct` por espécie |
| 4.2 | 🟠 Média | Contagem de fenologia reconstruída a partir de % arredondado | Barras "Flores/Frutos/Folhas" em StatsScreen |
| 4.3 | 🟠 Média | `mediaDap === null` tratado como DAP alto | Classificação do Povoamento ("Estabelecido") |
| 4.4 | 🟠 Média | Filtragem de DAP inconsistente entre métricas | minDap/maxDap/mediaDap vs. área basal/distribuição diamétrica |
| 4.5 | 🟡 Baixa | Percentuais não somam 100% | Todos os breakdowns em %/barras |
| 4.6 | 🟡 Baixa | `"seco"` duplicado em duas listas de keywords | Nenhum efeito hoje (código morto/confuso) |
| 4.7 | 🟡 Baixa | Chave de cobertura sem `.trim()` | `coberturaDados` (só em CSV editado manualmente) |
| 4.8 | ⚪ Informativo | `isReplanted()` cobre formato de dado inexistente no form atual | Nenhum (comportamento correto hoje) |

---

## 6. Não coberto por esta auditoria

- Não foram revisados: `src/components/*` (além dos usados diretamente pelos
  formulários), navegação/UX (`src/navigation/*`), persistência de arquivo em si
  além do fluxo de leitura/escrita já descrito na Seção 1.
- Não foi feita auditoria de UX/acessibilidade, apenas de corretude dos cálculos.
- Nenhuma correção foi proposta ou implementada — este documento é só o
  levantamento.
