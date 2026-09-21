# Importação offline de dados

## Purpose

Permite trazer planilhas CSV e Excel já existentes para dentro do aplicativo sem conexão com a internet, validando a estrutura antes de aceitar qualquer registro e sem jamais sobrescrever dados de campo já coletados de forma silenciosa.

## ADDED Requirements

### Requirement: Importação integralmente offline

A importação SHALL operar sem qualquer acesso à rede. O sistema MUST NOT enviar o arquivo ou seu conteúdo a qualquer serviço externo.

*Status: ESCOPO ATUAL — capacidade inexistente hoje.*

#### Scenario: Dispositivo sem conexão

- **WHEN** o usuário importa um arquivo com o dispositivo em modo avião
- **THEN** a importação é concluída normalmente
- **AND** nenhuma operação de rede é tentada

### Requirement: Validação antes da gravação

O sistema SHALL validar integralmente o arquivo e apresentar o resultado ao usuário antes de gravar qualquer registro. Nenhum registro MUST ser persistido antes da confirmação explícita do usuário.

#### Scenario: Pré-visualização antes de confirmar

- **WHEN** o usuário seleciona um arquivo para importação
- **THEN** o sistema exibe uma pré-visualização das linhas interpretadas e o resumo de validação
- **AND** nenhum dado é gravado até que o usuário confirme

#### Scenario: Usuário cancela após a pré-visualização

- **WHEN** o usuário cancela na tela de pré-visualização
- **THEN** nenhum registro é gravado
- **AND** os arquivos de dados existentes permanecem inalterados

### Requirement: Mapeamento explícito de colunas

O sistema SHALL permitir ao usuário mapear cada coluna do arquivo de origem para um campo do contrato canônico, e MUST NOT assumir a ordem das colunas como correta sem confirmação quando o cabeçalho não corresponder exatamente ao esperado.

*Status: CONFIRMADO NO CÓDIGO — `parseDendroRows()` e `parseFenologiaRows()` mapeiam estritamente por índice posicional (`r[0]`, `r[1]`, …), sem verificar o cabeçalho. Um arquivo com colunas deslocadas é lido sem nenhum erro. Classificação: ERRO DE INTEGRAÇÃO.*

#### Scenario: Cabeçalho idêntico ao esperado

- **WHEN** o arquivo possui exatamente os cabeçalhos do contrato canônico na ordem esperada
- **THEN** o sistema propõe o mapeamento automaticamente
- **AND** o usuário pode revisá-lo antes de confirmar

#### Scenario: Colunas deslocadas

- **WHEN** o arquivo possui uma coluna a mais no início, deslocando todas as demais
- **THEN** o sistema detecta a divergência de cabeçalho
- **AND** exige mapeamento explícito antes de prosseguir
- **AND** não interpreta os dados pela posição original

### Requirement: Detecção de tipos incompatíveis

O sistema SHALL detectar e reportar, por linha e por coluna, valores cujo tipo é incompatível com o campo de destino, incluindo datas em colunas numéricas e texto em colunas de medição.

*Status: CONFIRMADO NA AUDITORIA / HIPÓTESE A VALIDAR NOS DADOS — os indícios de valores dendrométricos interpretados como data e de `"MORTA"` em coluna de DAP foram relatados pelo usuário; o arquivo `dendrometria_julho.xlsx` não está disponível para confirmação. Classificação: ERRO DE DADO.*

#### Scenario: Data em coluna numérica

- **WHEN** a coluna DAP contém um valor reconhecível como data
- **THEN** a linha é reportada com erro de tipo
- **AND** o valor original é preservado no relatório
- **AND** o sistema não converte o valor por inferência

#### Scenario: Texto em coluna de medição

- **WHEN** a coluna DAP contém o texto `"MORTA"`
- **THEN** a linha é reportada com erro de tipo
- **AND** o sistema oferece ao usuário a decisão de mapear o texto para um motivo de ausência de medição
- **AND** não aplica essa conversão automaticamente

#### Scenario: Linha com número de colunas divergente

- **WHEN** uma linha possui menos ou mais campos do que o cabeçalho declara
- **THEN** a linha é reportada como estruturalmente quebrada
- **AND** a ocorrência é classificada como bloqueante para aquela linha

### Requirement: Bloqueio de importação estruturalmente inválida

O sistema SHALL impedir a conclusão da importação quando o arquivo apresentar erro estrutural que impeça a interpretação confiável do conjunto, mesmo que algumas linhas sejam individualmente válidas.

#### Scenario: Arquivo sem cabeçalho reconhecível

- **WHEN** o arquivo não possui cabeçalho e o usuário não fornece mapeamento
- **THEN** a importação é bloqueada
- **AND** o motivo é apresentado ao usuário

#### Scenario: Arquivo com maioria das linhas quebradas

- **WHEN** o arquivo apresenta erro estrutural generalizado
- **THEN** a importação é bloqueada integralmente
- **AND** o sistema não importa apenas o subconjunto válido sem consentimento explícito

### Requirement: Prevenção de sobrescrita e preservação do original

O sistema SHALL preservar o arquivo de origem inalterado e MUST NOT substituir registros já existentes sem apresentar ao usuário quais registros seriam afetados.

#### Scenario: Importação colidindo com registros existentes

- **WHEN** o arquivo importado contém pares Parcela + Árvore que já existem no dispositivo
- **THEN** o sistema lista as colisões antes de gravar
- **AND** exige que o usuário escolha entre manter, adicionar como nova medição ou cancelar
- **AND** não sobrescreve por padrão

#### Scenario: Arquivo de origem após a importação

- **WHEN** a importação é concluída com sucesso
- **THEN** o arquivo de origem permanece inalterado no dispositivo

### Requirement: Resumo final da importação

Ao término, o sistema SHALL apresentar o número de registros aceitos, aceitos com ressalva e rejeitados, com acesso ao detalhamento por linha.

#### Scenario: Importação parcialmente aceita

- **WHEN** a importação conclui com registros aceitos e rejeitados
- **THEN** o resumo apresenta as três contagens
- **AND** a soma das contagens é igual ao número de linhas de dados do arquivo
