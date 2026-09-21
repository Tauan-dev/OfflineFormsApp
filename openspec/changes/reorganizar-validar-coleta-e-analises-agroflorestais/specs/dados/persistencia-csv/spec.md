# Persistência em CSV

## Purpose

Garante que um registro salvo no dispositivo seja lido de volta exatamente como foi gravado, incluindo observações com vírgulas, aspas e quebras de linha, e que os arquivos já existentes continuem legíveis após qualquer evolução do formato.

## ADDED Requirements

### Requirement: Ida e volta sem perda

O sistema SHALL garantir que todo registro gravado seja recuperado na leitura com os mesmos valores por campo. A leitura MUST interpretar corretamente campos delimitados por aspas que contenham vírgula, aspas escapadas ou quebra de linha.

*Status: CONFIRMADO NO CÓDIGO — `csvField()` em `excelService.ts` escapa corretamente quebras de linha envolvendo o campo em aspas, mas `parseCsv()` inicia com `text.split(/\r?\n/)` antes de qualquer tratamento de aspas. Um registro com observação multilinha é gravado corretamente e lido de forma corrompida, deslocando colunas da linha e criando uma linha espúria. Classificação: ERRO DE IMPLEMENTAÇÃO — este é o mecanismo pelo qual o próprio aplicativo pode gerar as "linhas deslocadas" relatadas nos dados históricos.*

#### Scenario: Observação com quebra de linha

- **WHEN** um registro é salvo com observação contendo quebra de linha
- **AND** o arquivo é lido de volta
- **THEN** o registro é recuperado como uma única linha lógica
- **AND** todos os campos permanecem em suas colunas originais
- **AND** nenhuma linha adicional é criada

#### Scenario: Observação com vírgula e aspas

- **WHEN** um registro é salvo com observação contendo vírgula e aspas duplas
- **AND** o arquivo é lido de volta
- **THEN** o texto da observação é recuperado idêntico ao original
- **AND** as colunas seguintes não são deslocadas

#### Scenario: Campo final vazio

- **WHEN** um registro é salvo com o último campo vazio
- **AND** o arquivo é lido de volta
- **THEN** o registro possui o mesmo número de campos que o cabeçalho
- **AND** o último campo é recuperado como vazio, não como ausente

### Requirement: Compatibilidade com arquivos existentes

O sistema SHALL ler os arquivos `dendometria.csv` e `fenologia.csv` já presentes no dispositivo sem exigir conversão prévia e MUST NOT apagar, truncar ou reescrever esses arquivos sem backup verificado.

*Status: CONFIRMADO NO CÓDIGO — `saveToCsv()` reescreve o arquivo inteiro a cada gravação; uma interrupção durante a escrita pode comprometer todo o histórico. Classificação: PROBLEMA RELACIONADO — risco de perda de dados, endereçável nesta mudança.*

#### Scenario: Arquivo gravado por versão anterior

- **WHEN** o aplicativo atualizado abre um arquivo gravado pela versão anterior
- **THEN** todos os registros existentes são lidos
- **AND** nenhum campo é perdido

#### Scenario: Gravação interrompida

- **WHEN** a gravação do arquivo é interrompida antes de concluir
- **THEN** o conteúdo anterior permanece recuperável
- **AND** o sistema informa que a última gravação não foi concluída

### Requirement: Identificação da versão do formato

O sistema SHALL ser capaz de determinar qual versão do contrato de dados um arquivo segue, a partir de seu cabeçalho, sem depender de metadado externo.

#### Scenario: Cabeçalho da versão corrente

- **WHEN** o arquivo possui o cabeçalho da versão corrente
- **THEN** o sistema o identifica e o lê diretamente

#### Scenario: Cabeçalho de versão anterior

- **WHEN** o arquivo possui o cabeçalho de uma versão anterior
- **THEN** o sistema o identifica como tal
- **AND** aplica a estratégia de migração definida antes de calcular indicadores
- **AND** informa ao usuário que uma migração foi necessária

#### Scenario: Cabeçalho irreconhecível

- **WHEN** o cabeçalho não corresponde a nenhuma versão conhecida
- **THEN** o sistema não tenta interpretar o arquivo por posição
- **AND** reporta o arquivo como incompatível
