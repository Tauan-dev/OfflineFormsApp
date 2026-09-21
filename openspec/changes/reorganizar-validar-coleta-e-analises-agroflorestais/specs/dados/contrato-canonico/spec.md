# Contrato canônico dos dados

## Purpose

Define o significado, o tipo, a unidade e os estados válidos de cada campo coletado em dendrometria e fenologia, e estabelece como um indivíduo, uma medição e uma campanha são identificados. É o contrato do qual toda validação, todo cálculo e toda apresentação derivam.

## ADDED Requirements

### Requirement: Distinção entre ausência, zero e não-aplicabilidade

O sistema SHALL representar, para todo campo de medição numérica, quatro estados mutuamente distintos: valor medido (incluindo zero legítimo), não medido, não aplicável e valor inválido. O sistema MUST NOT colapsar esses estados em um único valor nulo.

*Status: CONFIRMADO NO CÓDIGO — `toNum()` em `dendrometryAnalytics.ts` retorna `null` tanto para `""` quanto para `"MORTA"` quanto para texto arbitrário. Classificação: ERRO DE REGRA DE NEGÓCIO.*

#### Scenario: Campo de medição vazio

- **WHEN** um registro possui a coluna DAP vazia
- **THEN** o campo é representado como "não medido"
- **AND** o registro não é contado como DAP igual a zero
- **AND** o registro não é excluído do denominador de cobertura da medição

#### Scenario: Campo de medição com texto não numérico

- **WHEN** um registro possui a coluna DAP com o conteúdo `"MORTA"`
- **THEN** o campo é representado como "valor inválido" com o texto original preservado
- **AND** o registro é reportado na qualidade dos dados com o valor original
- **AND** o valor original não é sobrescrito nem convertido por inferência

#### Scenario: Medição zero legítima

- **WHEN** um registro possui DAP igual a `0` informado explicitamente
- **THEN** o sistema trata o valor como medição presente de valor zero
- **AND** a política de elegibilidade do indicador consumidor decide se o valor entra no cálculo
- **AND** a decisão de exclusão é registrada com motivo

#### Scenario: Medição não aplicável

- **WHEN** um indivíduo é registrado com motivo de ausência de medição informado
- **THEN** o campo de medição é representado como "não aplicável"
- **AND** o motivo informado acompanha o registro

### Requirement: Normalização determinística de texto, número e chave

O sistema SHALL aplicar uma normalização única e determinística a identificadores e valores textuais antes de qualquer comparação, agregação ou cruzamento. A normalização MUST ser idempotente e MUST preservar o valor original para exibição e auditoria.

*Status: CONFIRMADO NO CÓDIGO — `calcCobertura()` em `inventoryAnalytics.ts` cruza com `` `${r.parcela}|${r.arv}` `` sem `trim()` nem normalização, enquanto `calcParcelaStats()` usa `r.parcela.trim()`. Classificação: ERRO DE IMPLEMENTAÇÃO.*

#### Scenario: Chave com espaços em branco

- **WHEN** um registro de dendrometria tem parcela `"P1 "` e outro de fenologia tem parcela `"P1"`, ambos com árvore `"7"`
- **THEN** os dois registros são reconhecidos como o mesmo indivíduo no cruzamento
- **AND** o valor exibido ao usuário é a forma canônica única

#### Scenario: Diferença de caixa em identificador

- **WHEN** registros usam `"p1"` e `"P1"` para a mesma parcela
- **THEN** ambos são agregados sob a mesma parcela
- **AND** a forma exibida é determinística e não depende da ordem de leitura do arquivo

#### Scenario: Zeros à esquerda no número da árvore

- **WHEN** um arquivo contém árvore `"07"` e outro contém `"7"` na mesma parcela
- **THEN** o sistema aplica a regra de normalização definida no contrato
- **AND** se a regra os unificar, a unificação é reportada na qualidade dos dados como normalização aplicada
- **AND** se a regra os mantiver distintos, ambos aparecem como indivíduos distintos sem fusão silenciosa

#### Scenario: Separador decimal variável

- **WHEN** um valor numérico é informado como `"12,5"` ou `"12.5"`
- **THEN** ambos são interpretados como o mesmo número
- **AND** um valor com dois separadores como `"1.2,5"` é classificado como inválido, não truncado

### Requirement: Identidade de indivíduo, medição e campanha

O sistema SHALL distinguir a identidade permanente de um indivíduo da identidade de uma medição desse indivíduo. Múltiplas medições do mesmo indivíduo em datas diferentes MUST ser representáveis sem que uma sobrescreva a outra e sem que sejam contadas como indivíduos distintos.

*Status: HIPÓTESE A VALIDAR — o código atual usa `Parcela + Árvore` como chave única e `calcDendroStats()` reporta `total = rows.length` como número de árvores, o que confunde registro com indivíduo. A existência de múltiplas campanhas nos dados históricos é afirmada pelo usuário mas NÃO PÔDE SER CONFIRMADA NOS DADOS (arquivos ausentes). Classificação: DADO INSUFICIENTE.*

#### Scenario: Mesmo indivíduo medido em duas campanhas

- **WHEN** o mesmo par Parcela + Árvore aparece com duas datas de medição distintas
- **THEN** o sistema reconhece um indivíduo e duas medições
- **AND** o total de indivíduos não é incrementado duas vezes
- **AND** os indicadores declaram qual campanha ou qual critério de seleção de medição utilizaram

#### Scenario: Chave duplicada dentro da mesma campanha

- **WHEN** o mesmo par Parcela + Árvore aparece duas vezes com a mesma data de medição
- **THEN** o sistema classifica a ocorrência como duplicidade
- **AND** a duplicidade é reportada na qualidade dos dados
- **AND** nenhum dos registros é descartado silenciosamente

#### Scenario: Espécie divergente para a mesma árvore

- **WHEN** o mesmo par Parcela + Árvore aparece com nomes comuns diferentes em dendrometria e fenologia
- **THEN** o sistema reporta a divergência na qualidade dos dados
- **AND** não elege automaticamente uma das espécies como correta

### Requirement: Registro sem parcela ou sem árvore

O sistema SHALL tratar registros sem parcela ou sem identificação de árvore como não identificáveis, reportá-los explicitamente e excluí-los de qualquer indicador que dependa de identidade.

*Status: CONFIRMADO NO CÓDIGO — `calcInventoryStats()` conta `totalArvores = dendroRows.length` incluindo registros sem parcela; `calcPopulationDynamics()` agrupa registros sem parcela sob a chave literal `"Sem parcela"`, que passa a ser exibida como se fosse uma parcela real. Classificação: ERRO DE APRESENTAÇÃO.*

#### Scenario: Registro sem parcela

- **WHEN** um registro não possui valor de parcela
- **THEN** ele não é contabilizado como pertencente a nenhuma parcela
- **AND** não incrementa o total de parcelas
- **AND** aparece no relatório de qualidade como registro não identificável

#### Scenario: Registro sem número de árvore

- **WHEN** um registro possui parcela mas não possui número de árvore
- **THEN** ele não participa do cruzamento entre dendrometria e fenologia
- **AND** o motivo da não participação é reportado

### Requirement: Validação de datas

O sistema SHALL validar datas quanto a formato, existência no calendário e coerência temporal, e MUST rejeitar valores numéricos seriais de planilha interpretados como data sem conversão explícita.

*Status: CONFIRMADO NO CÓDIGO — `validateDate()` em `validators.ts` já valida formato `DD/MM/AAAA`, existência e intervalo de ano; a coerência entre data de medição e ano de plantio NÃO é validada. Classificação: MELHORIA OPCIONAL para o formulário, ESCOPO ATUAL para a importação.*

#### Scenario: Data inexistente no calendário

- **WHEN** um registro informa a data `31/02/2025`
- **THEN** o registro é marcado com erro de data
- **AND** o erro identifica o campo e a linha

#### Scenario: Data de medição anterior ao plantio

- **WHEN** a data de medição de um indivíduo é anterior ao seu ano de plantio
- **THEN** o sistema emite um aviso de incoerência temporal
- **AND** o aviso é não bloqueante para dados já salvos

#### Scenario: Valor serial de planilha em coluna de data

- **WHEN** uma coluna de data contém um número serial como `45123`
- **THEN** o sistema não o interpreta silenciosamente como data
- **AND** reporta o valor como requerendo decisão explícita de conversão

### Requirement: Rastreabilidade de exclusões

Todo registro ou valor excluído de um cálculo SHALL ser contabilizado e acompanhado de um motivo legível. O sistema MUST NOT reduzir um denominador sem expor a redução.

*Status: CONFIRMADO NO CÓDIGO — `areaBasalTotal` e `distribuicaoDiametrica` filtram `d > 0 && d <= 300` sem reportar quantos valores foram descartados; `loadDendroRows()` em `dataLoader.ts` usa `catch { return [] }`, transformando falha de leitura em conjunto vazio indistinguível de arquivo sem dados. Classificação: ERRO DE IMPLEMENTAÇÃO.*

#### Scenario: Valor excluído de um indicador

- **WHEN** um valor de DAP é excluído do cálculo de área basal por não atender à política de elegibilidade
- **THEN** o indicador informa quantos valores foram considerados e quantos foram excluídos
- **AND** o motivo da exclusão é identificável por registro

#### Scenario: Falha de leitura do arquivo

- **WHEN** a leitura de um arquivo de dados falha
- **THEN** o sistema reporta a falha ao usuário
- **AND** não apresenta os indicadores como se o conjunto de dados estivesse vazio

#### Scenario: Arquivo legitimamente ausente

- **WHEN** o arquivo de dados ainda não existe porque nenhuma coleta foi feita
- **THEN** o sistema informa ausência de dados
- **AND** distingue essa situação de uma falha de leitura
