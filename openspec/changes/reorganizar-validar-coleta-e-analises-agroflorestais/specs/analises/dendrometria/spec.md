# Análise dendrométrica

## Purpose

Define como DAP e alturas são transformados em médias, extremos, área basal, distribuição diamétrica e ranking de maior indivíduo, com uma política de elegibilidade única e auditável para cada valor considerado ou excluído.

## ADDED Requirements

### Requirement: Política única de elegibilidade de DAP

Todos os indicadores derivados de DAP SHALL aplicar a mesma política de elegibilidade, declarada e auditável. O sistema MUST NOT usar conjuntos de valores diferentes para média, extremos, área basal e distribuição diamétrica sem que a diferença seja explícita e justificada.

*Status: CONFIRMADO NO CÓDIGO — em `calcDendroStats()`, `mediaDap`, `maxDap` e `minDap` usam `daps` (todo valor não nulo, incluindo `0` e valores acima de 300), enquanto `areaBasalTotal` e `distribuicaoDiametrica` usam `dapsValidos = daps.filter(d => d > 0 && d <= 300)`. O mesmo conjunto de dados produz dois universos distintos na mesma tela. Classificação: ERRO DE ALGORITMO.*

*A origem e a justificativa do limiar de 300 cm NÃO FORAM LOCALIZADAS no repositório nem em documentação. Classificação: DECISÃO METODOLÓGICA NECESSÁRIA — o limiar não deve ser mantido nem alterado sem definição.*

#### Scenario: Conjunto com DAP igual a zero

- **WHEN** o conjunto contém indivíduos com DAP igual a zero
- **THEN** a mesma decisão de inclusão ou exclusão é aplicada à média, ao mínimo, ao máximo, à área basal e à distribuição diamétrica
- **AND** a quantidade de valores excluídos é reportada

#### Scenario: Conjunto com valor extremo

- **WHEN** o conjunto contém um DAP acima do limiar de plausibilidade definido
- **THEN** o valor é tratado segundo a política única
- **AND** é reportado no relatório de qualidade como valor extremo
- **AND** não é removido silenciosamente de alguns indicadores e mantido em outros

#### Scenario: Nenhum DAP elegível

- **WHEN** nenhum indivíduo possui DAP elegível
- **THEN** todos os indicadores derivados de DAP são apresentados como indisponíveis
- **AND** a área basal total não é apresentada como zero

### Requirement: Área basal individual e total

A área basal individual SHALL ser calculada a partir do DAP em centímetros pela fórmula `g = π × DAP² / 40000`, resultando em metros quadrados. A área basal total SHALL ser a soma das áreas basais individuais elegíveis.

*Status: CONFIRMADO NO CÓDIGO — a implementação atual usa `Math.PI * (d/100/2)²`, algebricamente idêntica a `π × DAP² / 40000`. Classificação: COMPORTAMENTO CORRETO quanto à fórmula; o defeito está na política de elegibilidade e na ausência de reporte de cobertura.*

#### Scenario: Exemplo numérico de área basal individual

- **WHEN** um indivíduo possui DAP de 20 cm
- **THEN** sua área basal individual é 0,031416 m² com tolerância de 1×10⁻⁶
- **AND** o resultado é expresso em metros quadrados

#### Scenario: Soma de áreas basais

- **WHEN** três indivíduos elegíveis possuem DAP de 10 cm, 20 cm e 30 cm
- **THEN** a área basal total é 0,109956 m² com tolerância de 1×10⁻⁶
- **AND** o número de indivíduos considerados é apresentado junto ao resultado

#### Scenario: Indivíduo sem DAP válido

- **WHEN** um indivíduo não possui DAP elegível
- **THEN** ele não contribui para a área basal total
- **AND** é contabilizado no denominador de cobertura da medição de DAP
- **AND** aparece no relatório de qualidade

#### Scenario: Área basal por hectare

- **WHEN** a área das parcelas, o desenho amostral e o fator de expansão não estão definidos
- **THEN** o sistema não apresenta área basal por hectare
- **AND** apresenta apenas a área basal absoluta em metros quadrados

*Status: BLOQUEADO POR AUSÊNCIA DE DADO — área da parcela, unidade e desenho amostral não constam no repositório nem no contrato de dados atual.*

### Requirement: Alturas identificadas por variável

Todo indicador de altura SHALL identificar explicitamente qual variável utilizou entre HESG, HESGCOPA, HC e HT. O sistema MUST NOT apresentar "altura média" sem qualificação.

*Status: CONFIRMADO NO CÓDIGO — `DendroStats` expõe `mediaHt`, `maxHt` e `mediaHc`, mas HESG e HESGCOPA são coletadas e nunca analisadas. O rótulo apresentado ao usuário precisa declarar a variável. Classificação: ERRO DE APRESENTAÇÃO.*

*O significado exato de HESG e HESGCOPA e seu papel nos indicadores do arboreto é DECISÃO METODOLÓGICA NECESSÁRIA.*

#### Scenario: Altura total média

- **WHEN** a altura total média é apresentada
- **THEN** o rótulo identifica a variável HT
- **AND** a unidade metro é apresentada
- **AND** o número de indivíduos com HT medida é apresentado

#### Scenario: Altura ausente

- **WHEN** parte dos indivíduos não possui a altura da variável utilizada
- **THEN** esses indivíduos não compõem o denominador da média
- **AND** a cobertura da medição é apresentada

#### Scenario: Variável coletada e não analisada

- **WHEN** HESG e HESGCOPA possuem valores coletados
- **THEN** o sistema declara explicitamente se essas variáveis participam ou não de algum indicador
- **AND** não as apresenta como se estivessem incorporadas aos indicadores de altura

### Requirement: Diâmetro médio com método declarado

O indicador de diâmetro médio SHALL declarar se representa a média aritmética dos DAPs ou o diâmetro quadrático. O sistema MUST NOT substituir um método pelo outro.

*Status: CONFIRMADO NO CÓDIGO — a implementação atual calcula média aritmética simples. A escolha entre média aritmética e diâmetro quadrático para os relatórios do arboreto é DECISÃO METODOLÓGICA NECESSÁRIA.*

#### Scenario: Método declarado junto ao valor

- **WHEN** o diâmetro médio é apresentado
- **THEN** o método de cálculo é identificado
- **AND** a unidade centímetro é apresentada

### Requirement: Maior indivíduo com critério nomeado

O sistema SHALL nomear o critério de cada ranking de maior indivíduo e SHALL apresentar parcela, número da árvore, espécie, valor, unidade, data da medição e critério utilizado.

*Status: CONFIRMADO NO CÓDIGO — `maiorArvore` é determinado exclusivamente por maior DAP, mas apresentado sem qualificação do critério e sem a data da medição. Classificação: ERRO DE APRESENTAÇÃO.*

#### Scenario: Ranking por DAP

- **WHEN** o maior indivíduo por DAP é apresentado
- **THEN** o critério "maior DAP" é identificado
- **AND** parcela, árvore, espécie, valor com unidade e data da medição são apresentados

#### Scenario: Empate no critério

- **WHEN** dois indivíduos possuem o mesmo valor no critério
- **THEN** o sistema apresenta o empate de forma determinística
- **AND** não seleciona um deles por ordem de leitura do arquivo

#### Scenario: Múltiplos rankings

- **WHEN** mais de um ranking de maior indivíduo é apresentado
- **THEN** cada ranking é nomeado por seu critério
- **AND** nenhum deles é rotulado genericamente como "maior indivíduo"

### Requirement: Distribuição diamétrica com classes fechadas

As classes diamétricas SHALL cobrir integralmente o domínio dos valores elegíveis sem sobreposição e sem lacuna, e o intervalo de cada classe SHALL ser explícito quanto a seus limites.

*Status: CONFIRMADO NO CÓDIGO — as classes usam `d > min && d <= max`, formando intervalos semiabertos consistentes; os valores fora de `0 < d ≤ 300` não pertencem a nenhuma classe e não são reportados. Classificação: ERRO DE APRESENTAÇÃO quanto ao rótulo das classes e ERRO DE ALGORITMO quanto aos valores sem classe.*

#### Scenario: Valor no limite de classe

- **WHEN** um indivíduo possui DAP exatamente igual ao limite entre duas classes
- **THEN** ele é atribuído a exatamente uma classe
- **AND** o rótulo da classe indica sem ambiguidade qual limite é inclusivo

#### Scenario: Soma das classes

- **WHEN** a distribuição diamétrica é apresentada
- **THEN** a soma das contagens das classes é igual ao número de valores elegíveis
- **AND** valores não elegíveis são apresentados separadamente com seu motivo
