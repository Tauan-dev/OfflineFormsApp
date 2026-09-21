# Inventário e análise por parcela

## Purpose

Define o cruzamento entre dendrometria e fenologia, a contagem de indivíduos e espécies, e os indicadores de abundância, frequência, riqueza e diversidade — distinguindo rigorosamente registro de indivíduo.

## ADDED Requirements

### Requirement: Registro não é sinônimo de indivíduo

O sistema SHALL distinguir número de registros de número de indivíduos. Um mesmo indivíduo presente em dendrometria e em fenologia MUST NOT ser contado como dois indivíduos.

*Status: CONFIRMADO NO CÓDIGO — `calcInventoryStats()` define `totalArvores = dendroRows.length`, contando registros; `EspecieInventario.totalGeral = totalDendro + totalFenol` soma registros de arquivos diferentes para o mesmo indivíduo; `especieMaisFrequenteCount` é exibido a partir de `totalGeral`, embora a ordenação use `totalDendro`. Classificação: ERRO DE REGRA DE NEGÓCIO.*

#### Scenario: Indivíduo presente nos dois arquivos

- **WHEN** o mesmo par Parcela + Árvore aparece em dendrometria e em fenologia
- **THEN** o total de indivíduos o conta uma única vez
- **AND** os totais de registros por arquivo permanecem disponíveis separadamente

#### Scenario: Indivíduo presente apenas em fenologia

- **WHEN** um indivíduo possui registro fenológico e nenhum registro dendrométrico
- **THEN** ele é contabilizado no total de indivíduos
- **AND** não é contabilizado nos indicadores que exigem medição dendrométrica

#### Scenario: Rótulo do indicador

- **WHEN** uma contagem é apresentada
- **THEN** o rótulo identifica se a contagem é de registros, de medições ou de indivíduos

### Requirement: Abundância, frequência e riqueza distintas

O sistema SHALL apresentar separadamente, com rótulos inequívocos, a abundância de indivíduos por espécie, a frequência de ocorrência em parcelas, a frequência relativa e a riqueza de espécies. Cada um MUST ter seu denominador declarado.

*Status: CONFIRMADO NO CÓDIGO — `countEspecies()` ordena por `totalDendro` mas exibe `totalGeral`, e calcula `pct` sobre o total de registros dendrométricos enquanto o texto de apoio sugere proporção do conjunto todo. O indicador rotulado "espécie mais frequente" é, na verdade, a espécie com mais registros dendrométricos. Classificação: ERRO DE APRESENTAÇÃO e ERRO DE ALGORITMO.*

*A definição de qual indicador o arboreto adota como "espécie mais frequente" é DECISÃO METODOLÓGICA NECESSÁRIA.*

#### Scenario: Espécie abundante em uma única parcela

- **WHEN** uma espécie possui muitos indivíduos concentrados em uma parcela e outra espécie possui poucos indivíduos distribuídos em todas as parcelas
- **THEN** a primeira lidera a abundância
- **AND** a segunda lidera a frequência em parcelas
- **AND** os dois indicadores são apresentados como grandezas distintas

#### Scenario: Denominador do percentual de espécie

- **WHEN** o percentual de uma espécie é apresentado
- **THEN** o denominador utilizado é declarado
- **AND** a soma dos percentuais das espécies sobre o mesmo denominador não excede cem por cento

#### Scenario: Riqueza de espécies

- **WHEN** a riqueza é apresentada
- **THEN** ela representa o número de espécies distintas observadas
- **AND** espécies grafadas com diferenças de caixa ou espaçamento são contadas uma única vez
- **AND** registros sem nome comum não são contados como uma espécie

### Requirement: Índice de diversidade não presumido

O sistema MUST NOT apresentar um índice de diversidade sem que o índice tenha sido explicitamente definido pela metodologia do estudo.

*Status: DECISÃO METODOLÓGICA NECESSÁRIA — nenhum índice de diversidade existe no código atual, e `MÉTRICAS PARA ESTUDO DO ARBORETO.docx` não está disponível para consulta. Classificação: BLOQUEADO POR AUSÊNCIA DE DADO.*

#### Scenario: Índice não definido

- **WHEN** nenhum índice de diversidade foi aprovado pela metodologia
- **THEN** o sistema apresenta apenas a riqueza observada
- **AND** não calcula nem exibe Shannon, Simpson, Pielou ou equivalente

#### Scenario: Índice definido posteriormente

- **WHEN** um índice for aprovado pela metodologia
- **THEN** o sistema o apresenta nomeado, com sua base logarítmica ou parametrização declarada
- **AND** apresenta o número de indivíduos e de espécies que compõem o cálculo

### Requirement: Cruzamento por chave normalizada

O cruzamento entre dendrometria e fenologia SHALL utilizar a chave canônica normalizada definida no contrato de dados, e SHALL reportar os registros que não encontraram correspondência.

*Status: CONFIRMADO NO CÓDIGO — `calcCobertura()` usa `` `${r.parcela}|${r.arv}` `` sem normalização, divergindo de `calcParcelaStats()`, que aplica `trim()`. A cobertura reportada pode ser subestimada por diferenças de espaçamento. Classificação: ERRO DE IMPLEMENTAÇÃO.*

#### Scenario: Chaves equivalentes com formatação divergente

- **WHEN** dendrometria registra parcela `"P1"` árvore `"07"` e fenologia registra `"p1 "` árvore `"7"`
- **THEN** o cruzamento os reconhece como o mesmo indivíduo conforme a regra de normalização canônica
- **AND** a cobertura reflete o cruzamento efetivo

#### Scenario: Cobertura apresentada

- **WHEN** a cobertura de dados é apresentada
- **THEN** o número de indivíduos cruzados e o número total de indivíduos são apresentados
- **AND** os registros não cruzados são acessíveis no relatório de qualidade

### Requirement: Parcela sem dados suficientes

Uma parcela sem registros suficientes para um indicador SHALL apresentar esse indicador como indisponível e MUST NOT ser ordenada ou comparada como se possuísse valor medido.

*Status: CONFIRMADO NO CÓDIGO — `calcParcelaStats()` retorna `pctSaudavel = 0` e `indicadorSaude = 0` para parcelas sem fenologia, e o resultado é ordenado por `indicadorSaude` decrescente, misturando parcelas sem dados com parcelas medidas. Classificação: ERRO DE APRESENTAÇÃO.*

#### Scenario: Parcela apenas com dendrometria

- **WHEN** uma parcela possui registros dendrométricos e nenhum fenológico
- **THEN** seus indicadores de condição são apresentados como indisponíveis
- **AND** ela não é posicionada no ranking de saúde entre parcelas com dados

#### Scenario: Ordenação determinística

- **WHEN** parcelas são ordenadas por um indicador
- **THEN** parcelas com indicador indisponível são agrupadas separadamente
- **AND** o critério de desempate é determinístico

### Requirement: Interações com fauna não inferidas de texto livre

O sistema MUST NOT apresentar como indicador de interação com fauna uma contagem derivada apenas da existência de texto em campo de observação livre.

*Status: CONFIRMADO NO CÓDIGO — `interacoesFauna` é definido como `fenolRows.filter(r => r.observacao.trim().length > 0).length`, ou seja, conta qualquer observação preenchida, independentemente de seu conteúdo. Uma observação sobre o solo ou sobre a medição é contada como interação com fauna. Classificação: ERRO DE REGRA DE NEGÓCIO.*

#### Scenario: Observação sem menção a fauna

- **WHEN** um registro possui observação livre sobre condições de acesso à árvore
- **THEN** ele não é contabilizado como interação com fauna

#### Scenario: Indicador renomeado enquanto não houver campo estruturado

- **WHEN** não existe campo estruturado de registro ecológico
- **THEN** o sistema apresenta o indicador como número de registros com observação preenchida
- **AND** não o rotula como interação com fauna
