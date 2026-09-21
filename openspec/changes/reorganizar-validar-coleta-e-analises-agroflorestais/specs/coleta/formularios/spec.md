# Modelo de coleta

## Purpose

Define o que os formulários de campo devem ser capazes de registrar para que os indicadores sejam calculáveis sem inferência a partir de texto livre — em especial estado vital, condição fitossanitária, motivo de ausência de medição e registros ecológicos.

## ADDED Requirements

### Requirement: Estado vital separado da condição fitossanitária

O sistema SHALL registrar o estado vital do indivíduo e sua condição fitossanitária como campos distintos. O sistema MUST NOT exigir que o coletor escolha entre informar que o indivíduo está vivo e informar que apresenta dano.

*Status: CONFIRMADO NO CÓDIGO — `FITOSSANITARIO_OPTIONS = ["vivo", "morto", "com dano"]` colapsa duas dimensões ortogonais em um único campo de escolha única. Um indivíduo vivo com dano não pode ser representado sem perder uma das duas informações. Classificação: ERRO DE REGRA DE NEGÓCIO.*

*As categorias finais de cada campo são DECISÃO METODOLÓGICA NECESSÁRIA.*

#### Scenario: Indivíduo vivo com dano

- **WHEN** o coletor registra um indivíduo vivo que apresenta dano
- **THEN** ambas as informações são registradas
- **AND** o indivíduo é contabilizado como vivo nos indicadores de sobrevivência
- **AND** é contabilizado como danificado nos indicadores fitossanitários

#### Scenario: Indivíduo morto

- **WHEN** o coletor registra um indivíduo como morto
- **THEN** a condição fitossanitária não é exigida
- **AND** os campos de medição dendrométrica não são exigidos

#### Scenario: Compatibilidade com registros históricos

- **WHEN** um registro gravado no modelo anterior é lido
- **THEN** o valor `"vivo"` é interpretado como vivo sem dano aparente
- **AND** o valor `"com dano"` é interpretado como vivo com dano
- **AND** o valor `"morto"` é interpretado como morto
- **AND** o valor original permanece preservado no arquivo

### Requirement: Motivo de ausência de medição

Quando uma medição dendrométrica não for realizada, o sistema SHALL permitir registrar o motivo. O motivo registrado SHALL distinguir a medição como não aplicável da medição como não realizada.

*Status: CONFIRMADO NO CÓDIGO — não existe campo de motivo; hoje a única forma de registrar "árvore tombada" ou "DAP não mensurável" é a observação livre, que nenhum indicador consome. Classificação: DADO INSUFICIENTE.*

*A lista final de motivos é DECISÃO METODOLÓGICA NECESSÁRIA. Os candidatos levantados são: não medido, não aplicável, indivíduo morto, altura insuficiente, impedimento físico, indivíduo tombado, fuste danificado e outro.*

#### Scenario: DAP não mensurável

- **WHEN** o coletor registra um indivíduo cujo DAP não pode ser medido
- **THEN** o motivo é registrado em campo estruturado
- **AND** o indivíduo é contabilizado no denominador de cobertura da medição
- **AND** não é contabilizado como DAP igual a zero

#### Scenario: Motivo obrigatório quando a medição está ausente

- **WHEN** um indivíduo vivo é salvo sem DAP
- **THEN** o sistema solicita o motivo da ausência
- **AND** a ausência de motivo é reportada como ressalva, não como bloqueio para dados históricos

### Requirement: Indivíduo multifuste

O sistema SHALL permitir representar indivíduos com mais de um fuste sem que cada fuste seja contado como um indivíduo distinto.

*Status: HIPÓTESE A VALIDAR — a existência de indivíduos multifuste foi relatada pelo usuário; os dados de validação não estão disponíveis para confirmação. O modelo atual não possui nenhum campo de fuste. Classificação: DADO INSUFICIENTE.*

*A regra de composição do DAP de um indivíduo multifuste é DECISÃO METODOLÓGICA NECESSÁRIA.*

#### Scenario: Indivíduo com dois fustes medidos

- **WHEN** um indivíduo possui dois fustes com DAP medido
- **THEN** o total de indivíduos o conta uma única vez
- **AND** a contribuição do indivíduo para a área basal segue a regra metodológica definida
- **AND** a regra utilizada é declarada junto ao indicador

#### Scenario: Regra de composição não definida

- **WHEN** a regra de composição do DAP multifuste não foi aprovada
- **THEN** o sistema registra os fustes sem compor um DAP único
- **AND** reporta os indivíduos multifuste no relatório de qualidade

### Requirement: Observação livre preservada e não consumida como dado estruturado

O sistema SHALL preservar o campo de observação livre e MUST NOT derivar indicadores estruturados exclusivamente do seu conteúdo textual.

*Status: CONFIRMADO NO CÓDIGO — `interacoesFauna` é derivado da mera existência de texto em observação. Classificação: ERRO DE REGRA DE NEGÓCIO. Ver `analises/inventario`.*

#### Scenario: Observação livre mantida

- **WHEN** o coletor preenche a observação livre
- **THEN** o texto é preservado integralmente no arquivo
- **AND** é recuperável na leitura, inclusive com quebras de linha

#### Scenario: Indicador estruturado exigindo campo estruturado

- **WHEN** um indicador estruturado é apresentado
- **THEN** ele deriva de campos estruturados
- **AND** a busca textual em observações serve apenas como mecanismo auxiliar de localização

### Requirement: Registros ecológicos estruturados

O sistema SHALL prever campos estruturados para registros ecológicos associados ao indivíduo ou à parcela, com compatibilidade para observações históricas registradas em texto livre.

*Status: DECISÃO METODOLÓGICA NECESSÁRIA — os campos candidatos são epífitas, hemiepífitas, cipós, outras plantas associadas, ninhos, fauna observada e serrapilheira. Nenhum existe hoje. A escala de intensidade de serrapilheira é BLOQUEADO POR AUSÊNCIA DE DADO até que uma escala seja aprovada.*

#### Scenario: Registro ecológico em coleta nova

- **WHEN** o coletor registra a presença de epífitas em um indivíduo
- **THEN** o registro é gravado em campo estruturado
- **AND** o indicador correspondente o contabiliza sem depender de texto livre

#### Scenario: Observação histórica mencionando epífitas

- **WHEN** um registro histórico menciona epífitas apenas na observação livre
- **THEN** o sistema pode localizá-lo por busca textual
- **AND** não o converte automaticamente em ocorrência confirmada
- **AND** exige revisão manual antes de contabilizá-lo

#### Scenario: Expressão negativa em observação

- **WHEN** uma observação contém uma expressão negativa como "sem bromélias"
- **THEN** a busca textual não a apresenta como ocorrência confirmada
- **AND** o resultado é apresentado como candidato a revisão manual

#### Scenario: Intensidade de serrapilheira sem escala aprovada

- **WHEN** nenhuma escala de intensidade de serrapilheira foi aprovada
- **THEN** o sistema não oferece um campo de intensidade com categorias inventadas
- **AND** registra apenas o que a metodologia aprovada definir
