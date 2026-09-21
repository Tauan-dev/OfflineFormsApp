# Dinâmica do povoamento, mortalidade e replantio

## Purpose

Define como coortes de plantio, replantio, mortalidade e sobrevivência são derivados dos dados coletados, impedindo que ausência de registro seja interpretada como morte e que ausência de medição seja interpretada como bom desempenho.

## ADDED Requirements

### Requirement: Ausência de DAP nunca satisfaz limiar de DAP

Um critério de classificação que dependa de DAP SHALL exigir DAP disponível. Quando o DAP médio for indisponível, o sistema MUST NOT considerar qualquer limiar de DAP como atendido.

*Status: CONFIRMADO NO CÓDIGO — `classificarPovoamento()` em `populationDynamicsAnalytics.ts:419` avalia `(mediaDap === null || mediaDap >= 15)`, de modo que um povoamento sem nenhum DAP medido satisfaz a condição de "DAP alto" e pode ser classificado como "Estabelecido". Classificação: ERRO DE FÓRMULA.*

#### Scenario: Povoamento sem nenhum DAP medido

- **WHEN** nenhum indivíduo possui DAP elegível
- **AND** a taxa de replantio é baixa e há três ou mais espécies
- **THEN** o povoamento não é classificado como "Estabelecido"
- **AND** a classificação é apresentada como indeterminada por ausência de dado dendrométrico

#### Scenario: Povoamento com DAP medido acima do limiar

- **WHEN** o DAP médio elegível atinge o limiar definido
- **AND** os demais critérios são atendidos
- **THEN** a classificação correspondente é aplicada
- **AND** o número de indivíduos com DAP medido é apresentado junto

#### Scenario: Laudo automático sem DAP

- **WHEN** o texto interpretativo automático é gerado sem DAP disponível
- **THEN** ele não afirma maturidade nem robustez estrutural
- **AND** declara explicitamente a ausência de dado dendrométrico

### Requirement: Limiares de classificação com origem documentada

Os limiares numéricos que definem a classificação do povoamento e a interpretação automática SHALL ter sua origem metodológica documentada. Limiares sem origem MUST NOT ser apresentados como conclusão técnica.

*Status: DECISÃO METODOLÓGICA NECESSÁRIA — os limiares de DAP (8, 10, 12, 15, 20 cm), de taxa de replantio (10, 25, 50 por cento), de número de espécies (3) e de índice de sucesso (0,5 e 0,8) estão codificados em `populationDynamicsAnalytics.ts` sem nenhuma referência de origem. Classificação: REGRA NÃO DEFINIDA.*

#### Scenario: Limiar sem origem definida

- **WHEN** um limiar não possui origem metodológica documentada
- **THEN** o indicador dele derivado não é apresentado como laudo conclusivo
- **AND** o sistema apresenta os valores brutos que o compõem

### Requirement: Mortalidade exige denominador definido

O sistema SHALL calcular mortalidade e sobrevivência apenas sobre um denominador de indivíduos implantados explicitamente definido e verificável. Ausência de registro de um indivíduo MUST NOT ser interpretada como morte.

*Status: BLOQUEADO POR AUSÊNCIA DE DADO — a informação de que cada parcela teria 36 indivíduos implantados foi relatada pelo usuário, mas o contrato de dados atual não possui campo de número de indivíduos implantados por parcela, e os arquivos de validação não estão disponíveis. Classificação: DADO INSUFICIENTE.*

#### Scenario: Denominador de implantação não informado

- **WHEN** o número de indivíduos implantados de uma parcela não está registrado
- **THEN** a mortalidade e a sobrevivência dessa parcela são apresentadas como indisponíveis
- **AND** o sistema não assume um denominador padrão

#### Scenario: Parcela com menos indivíduos registrados que o implantado

- **WHEN** uma parcela possui menos indivíduos registrados do que o número implantado informado
- **THEN** a diferença é apresentada como indivíduos não registrados
- **AND** não é apresentada como indivíduos mortos

#### Scenario: Indivíduo explicitamente marcado como morto

- **WHEN** um indivíduo possui estado vital registrado como morto
- **THEN** ele compõe a mortalidade
- **AND** a mortalidade declara quantos indivíduos foram efetivamente avaliados

#### Scenario: Parcela parcialmente coletada

- **WHEN** a coleta de uma parcela ainda está em andamento
- **THEN** o sistema não apresenta a mortalidade como definitiva
- **AND** apresenta a cobertura da coleta na parcela

### Requirement: Replantio com semântica explícita

O campo de replantio SHALL ter semântica única e declarada. O sistema MUST NOT tratar qualquer conteúdo não vazio como evidência de replantio sem que isso esteja definido no contrato de dados.

*Status: CONFIRMADO NO CÓDIGO — `isReplanted()` retorna verdadeiro para qualquer texto que não esteja na lista de negações, incluindo uma observação acidental no campo; `validateDendrometry()` exige que o campo seja uma data `DD/MM/AAAA`, mas dados importados ou históricos podem conter outros conteúdos. `extractYear()` retorna o texto bruto como se fosse um ano quando nenhum padrão de ano é encontrado, produzindo coortes rotuladas com lixo textual. Classificação: ERRO DE ALGORITMO.*

#### Scenario: Campo de replantio com data válida

- **WHEN** o campo de replantio contém uma data válida
- **THEN** o indivíduo é contabilizado como replantado
- **AND** o ano do replantio é extraído da data

#### Scenario: Campo de replantio com conteúdo não interpretável

- **WHEN** o campo de replantio contém texto que não é uma data nem uma negação conhecida
- **THEN** o registro é reportado no relatório de qualidade
- **AND** não é contabilizado como replantado sem decisão explícita
- **AND** o conteúdo não é usado como rótulo de ano

#### Scenario: Taxa de replantio e mortalidade distinguidas

- **WHEN** a taxa de replantio é apresentada
- **THEN** ela é rotulada como taxa de replantio
- **AND** não é apresentada como taxa de mortalidade

*Status: CONFIRMADO NO CÓDIGO — `interpretarDinamica()` e `gerarTextoAutomatico()` afirmam que a taxa de replantio "indica mortalidade", equiparando os dois conceitos sem justificativa. Classificação: ERRO DE REGRA DE NEGÓCIO.*

### Requirement: Informações de replantio a representar

O contrato de dados SHALL permitir registrar, quando disponíveis, a ocorrência do replantio, sua data, a espécie original, a espécie replantada e o indivíduo substituído. Quando uma dessas informações não puder ser determinada a partir dos dados existentes, o sistema SHALL reportar a limitação.

*Status: CONFIRMADO NO CÓDIGO — o arquivo atual possui apenas um campo `Replantio`, insuficiente para distinguir espécie original de espécie replantada. Classificação: DADO INSUFICIENTE para os dados históricos; ESCOPO ATUAL para coletas futuras.*

#### Scenario: Espécie original desconhecida

- **WHEN** um indivíduo replantado não possui registro da espécie original
- **THEN** o sistema apresenta a espécie original como não registrada
- **AND** não assume que a espécie atual é a espécie original

#### Scenario: Efeito do replantio sobre a contagem de indivíduos

- **WHEN** um indivíduo replantado é contabilizado
- **THEN** o sistema declara se ele é contado como um indivíduo ou como substituição de um indivíduo anterior
- **AND** a regra adotada é a mesma em todos os indicadores

### Requirement: Coortes derivadas de anos válidos

Coortes de plantio SHALL ser formadas apenas a partir de anos válidos. Registros sem ano de plantio interpretável SHALL formar um grupo explícito de indeterminados.

#### Scenario: Registro sem ano de plantio

- **WHEN** um registro não possui ano de plantio interpretável
- **THEN** ele compõe um grupo rotulado como indeterminado
- **AND** não compõe o cálculo da amplitude temporal

#### Scenario: Amplitude temporal

- **WHEN** a amplitude temporal é apresentada
- **THEN** ela considera apenas anos válidos
- **AND** é apresentada como indisponível quando houver menos de dois anos válidos distintos
