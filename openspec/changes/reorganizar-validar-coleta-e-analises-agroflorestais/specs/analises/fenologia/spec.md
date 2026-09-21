# Análise fenológica

## Purpose

Define como presença, intensidade e estágio de flores, frutos e folhas são contabilizados e apresentados, garantindo que as contagens exibidas sejam as contagens reais e não reconstruções a partir de percentuais.

## ADDED Requirements

### Requirement: Contagem bruta fornecida pela camada analítica

A camada analítica SHALL fornecer, para cada indicador fenológico, a contagem bruta, o denominador utilizado, o percentual, o número de registros elegíveis e o número de registros excluídos. A camada de apresentação MUST NOT derivar contagem a partir de percentual.

*Status: CONFIRMADO NO CÓDIGO — `PhenologyStats` expõe apenas `pctFlores`, `pctFrutos` e `pctFolhas` (já arredondados por `Math.round`), e `StatsScreen.tsx:320,326,332` reconstrói as contagens com `Math.round((stats.pctFlores * stats.total) / 100)`. Classificação: ERRO DE APRESENTAÇÃO causado por contrato insuficiente.*

#### Scenario: Contagem exibida corresponde à contagem real

- **WHEN** 7 de 30 registros possuem flores
- **THEN** a contagem exibida é exatamente 7
- **AND** o percentual exibido é derivado da contagem, nunca o contrário

#### Scenario: Amostra pequena com arredondamento desfavorável

- **WHEN** 1 de 3 registros possui frutos
- **THEN** a contagem exibida é exatamente 1
- **AND** a contagem não é alterada pelo arredondamento do percentual

#### Scenario: Denominador apresentado

- **WHEN** um indicador fenológico é apresentado
- **THEN** o denominador utilizado é apresentado junto
- **AND** o usuário distingue "7 de 30" de "7 de 300"

### Requirement: Presença tratada como indicador de múltipla ocorrência

Presença de flores, frutos e folhas SHALL ser tratada como indicadores independentes e não mutuamente exclusivos. O sistema MUST NOT apresentá-los como uma distribuição cuja soma deva ser cem por cento.

*Status: CONFIRMADO NO CÓDIGO — `pctFlores`, `pctFrutos` e `pctFolhas` são calculados independentemente sobre o mesmo total, o que está correto; o defeito potencial é de apresentação, ao exibi-los agrupados como se compusessem um todo. Classificação: ERRO DE APRESENTAÇÃO.*

#### Scenario: Indivíduo com flores e frutos simultaneamente

- **WHEN** um indivíduo possui flores e frutos ao mesmo tempo
- **THEN** ele é contabilizado em ambos os indicadores
- **AND** a soma dos percentuais pode exceder cem por cento sem que isso constitua erro

#### Scenario: Distribuição de estágios

- **WHEN** a distribuição de estágios de floração é apresentada
- **THEN** ela é calculada apenas sobre os indivíduos com flores presentes
- **AND** as categorias são mutuamente exclusivas
- **AND** a soma das contagens é igual ao número de indivíduos com flores

### Requirement: Intensidade tratada como variável numérica

A intensidade de flores, frutos e folhas SHALL ser tratada conforme sua natureza declarada no contrato canônico. Quando numérica, o sistema MUST NOT agregá-la como categoria textual.

*Status: CONFIRMADO NO CÓDIGO — `validatePhenology()` valida `intensidade` como número entre 0 e 100 e o formulário a apresenta com unidade `%` e teclado decimal, mas `calcPhenologyStats()` a agrega via `countDistribution()` como se fosse categórica. Os valores `"35"`, `"35.0"` e `"35,0"` tornam-se três categorias distintas, e `intensidadePredomFlores` retorna a moda de textos, não uma estatística de intensidade. Classificação: ERRO DE ALGORITMO.*

#### Scenario: Mesma intensidade escrita de formas diferentes

- **WHEN** dois registros informam intensidade `"35"` e `"35,0"`
- **THEN** ambos são interpretados como o mesmo valor numérico
- **AND** não geram categorias distintas

#### Scenario: Estatística de intensidade

- **WHEN** a intensidade de floração é resumida
- **THEN** o sistema apresenta uma estatística apropriada a uma variável numérica
- **AND** declara qual estatística utilizou
- **AND** apresenta o número de registros com intensidade informada

#### Scenario: Presença sem intensidade informada

- **WHEN** um registro possui flores presentes mas intensidade não informada
- **THEN** ele compõe o indicador de presença
- **AND** não compõe o denominador da estatística de intensidade
- **AND** a diferença entre os denominadores é reportada

### Requirement: Estágio não aplicável quando há ausência

Quando a presença de um grupo fenológico é negativa, o estágio SHALL ser registrado como não aplicável e MUST NOT ser contabilizado em nenhuma distribuição de estágios.

*Status: CONFIRMADO NO CÓDIGO — o formulário já força o estágio para `"não aplicável"` quando a presença é negativa, e `calcPhenologyStats()` já filtra por `floresPresenca` antes de distribuir estágios. Classificação: COMPORTAMENTO CORRETO — preservar.*

#### Scenario: Grupo ausente

- **WHEN** um registro indica ausência de frutos
- **THEN** seu estágio de frutos não compõe a distribuição de estágios de frutos
- **AND** o registro compõe o denominador do percentual de presença de frutos
