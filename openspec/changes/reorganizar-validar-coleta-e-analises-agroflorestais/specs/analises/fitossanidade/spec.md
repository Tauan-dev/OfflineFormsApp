# Análise fitossanitária

## Purpose

Define como o estado fitossanitário coletado em campo é classificado, agregado em percentuais, resumido em um indicador de saúde e traduzido em alertas ao usuário. É a capacidade com o defeito de maior impacto confirmado no sistema atual.

## ADDED Requirements

### Requirement: Vocabulário único entre coleta e análise

A classificação fitossanitária SHALL operar exatamente sobre o vocabulário que o formulário é capaz de gravar. O sistema MUST NOT classificar por palavras-chave que nenhum campo produz, e MUST NOT deixar valores gravados sem classificação.

*Status: CONFIRMADO NO CÓDIGO — `FITOSSANITARIO_OPTIONS = ["vivo", "morto", "com dano"]` em `Form2Screen.tsx:174` versus `KW_SAUDAVEL = ["bom","boa","saudável","saudavel","normal","ótimo","otimo"]`, `KW_DANO_LEVE`, `KW_DANO_SEV` e `ESTADOS_OK = ["bom","boa","normal","saudável","saudavel"]` em `inventoryAnalytics.ts`. Dos três valores possíveis, apenas `"morto"` casa com alguma palavra-chave. Classificação: ERRO DE INTEGRAÇÃO.*

#### Scenario: Registro marcado como vivo

- **WHEN** um registro de fenologia possui estado fitossanitário `"vivo"`
- **THEN** o registro é classificado em uma categoria de saúde definida
- **AND** não permanece em uma categoria residual não contabilizada
- **AND** não gera alerta fitossanitário

#### Scenario: Registro marcado como com dano

- **WHEN** um registro de fenologia possui estado fitossanitário `"com dano"`
- **THEN** o registro é classificado como apresentando dano
- **AND** é contabilizado no percentual de indivíduos com dano
- **AND** gera alerta fitossanitário

#### Scenario: Registro marcado como morto

- **WHEN** um registro de fenologia possui estado fitossanitário `"morto"`
- **THEN** o registro é classificado como morto
- **AND** não é contabilizado como indivíduo com dano

#### Scenario: Valor fora do vocabulário conhecido

- **WHEN** um registro possui um estado fitossanitário não previsto no vocabulário canônico
- **THEN** o registro é contabilizado em uma categoria explícita de valor não reconhecido
- **AND** a categoria aparece no relatório de qualidade com o valor original
- **AND** o valor não é silenciosamente ignorado no denominador

#### Scenario: Estado fitossanitário não informado

- **WHEN** um registro de fenologia possui o estado fitossanitário vazio
- **THEN** o registro é contabilizado como não avaliado
- **AND** não é contado como saudável nem como morto
- **AND** não é incluído no denominador dos percentuais de condição

*Nota: `validatePhenology()` em `validators.ts` não exige o campo fitossanitário, portanto registros com o campo vazio existem e devem ser tratados.*

### Requirement: Ausência de níveis de gravidade não coletados

O sistema MUST NOT reportar níveis de gravidade de dano que o formulário não é capaz de distinguir. Enquanto a coleta não diferenciar intensidade de dano, os indicadores SHALL reportar apenas a presença de dano.

*Status: CONFIRMADO NO CÓDIGO — `InventoryStats` expõe `pctDanoLeve` e `pctDanoSevero` como campos distintos, mas nenhuma entrada do formulário permite distingui-los. Classificação: INCOMPATIBILIDADE DE MODELO — o cálculo modela uma informação que o sistema nunca coleta. A introdução de graus de dano é DECISÃO METODOLÓGICA NECESSÁRIA.*

#### Scenario: Dados coletados sem gradação de dano

- **WHEN** os registros contêm apenas os estados `vivo`, `morto` e `com dano`
- **THEN** o sistema apresenta percentual de indivíduos com dano sem subdividi-lo
- **AND** não apresenta percentuais de dano leve e dano severo

#### Scenario: Dados históricos com percentuais de gradação

- **WHEN** dados já coletados são reprocessados
- **THEN** nenhum registro existente é alterado
- **AND** os indicadores de gradação deixam de ser exibidos sem que os dados de origem sejam modificados

### Requirement: Indicador de saúde com definição explícita

O indicador de saúde SHALL ter sua fórmula, sua escala e seu denominador declarados junto ao valor apresentado, e SHALL ser apresentado como indisponível quando não houver registros avaliados.

*Status: CONFIRMADO NO CÓDIGO — `indicadorSaude = pctSaudavel - (pctDanoSevero + pctMorto)` é calculado sobre `totalFenol = fenolRows.length || 1`, incluindo registros com campo vazio no denominador. Combinado ao erro de vocabulário, o valor é estruturalmente negativo. A escala do indicador (faixa, sinal e interpretação) é DECISÃO METODOLÓGICA NECESSÁRIA.*

#### Scenario: Nenhum registro fenológico avaliado

- **WHEN** não há registros com estado fitossanitário informado
- **THEN** o indicador de saúde é apresentado como indisponível
- **AND** não é apresentado como zero

#### Scenario: Denominador do indicador

- **WHEN** o indicador de saúde é apresentado
- **THEN** o número de registros avaliados que compõem o denominador é apresentado junto
- **AND** registros não avaliados não compõem o denominador

#### Scenario: Todos os indivíduos vivos e sem dano

- **WHEN** todos os registros avaliados possuem estado `"vivo"`
- **THEN** o indicador de saúde atinge o extremo favorável de sua escala
- **AND** nenhum alerta fitossanitário é gerado

### Requirement: Alertas restritos a condições problemáticas

O sistema SHALL gerar alerta fitossanitário apenas para estados que representem problema segundo o vocabulário canônico.

*Status: CONFIRMADO NO CÓDIGO — `alertasFito()` filtra por `!ESTADOS_OK.includes(estado)`; como `"vivo"` não está em `ESTADOS_OK`, todo indivíduo saudável é listado como alerta em `StatsScreen.tsx`. Classificação: ERRO DE ALGORITMO.*

#### Scenario: Conjunto integralmente saudável

- **WHEN** todos os registros avaliados possuem estado `"vivo"`
- **THEN** a lista de alertas fitossanitários está vazia
- **AND** o sistema informa explicitamente a ausência de alertas

#### Scenario: Conjunto com indivíduos danificados

- **WHEN** parte dos registros possui estado `"com dano"`
- **THEN** apenas esses registros compõem os alertas
- **AND** o percentual do alerta é calculado sobre os registros avaliados

### Requirement: Consistência entre visão geral e visão por parcela

Os percentuais e o indicador de saúde SHALL usar a mesma classificação e a mesma política de denominador na visão geral e na visão por parcela.

*Status: CONFIRMADO NO CÓDIGO — `calcInventoryStats()` e `calcParcelaStats()` duplicam a mesma lógica de contagem, ambas usando `|| 1` como proteção de denominador. Classificação: ERRO DE IMPLEMENTAÇÃO por duplicação divergente em potencial.*

#### Scenario: Parcela sem registros fenológicos

- **WHEN** uma parcela possui registros dendrométricos mas nenhum registro fenológico
- **THEN** seus percentuais de condição são apresentados como indisponíveis
- **AND** não são apresentados como zero por cento
- **AND** a parcela não é ordenada como se tivesse a pior saúde

#### Scenario: Agregação geral coerente com as parcelas

- **WHEN** os indicadores gerais e por parcela são calculados sobre o mesmo conjunto
- **THEN** a contagem total de cada categoria na visão geral é igual à soma das contagens por parcela
- **AND** eventuais registros sem parcela são reportados separadamente
