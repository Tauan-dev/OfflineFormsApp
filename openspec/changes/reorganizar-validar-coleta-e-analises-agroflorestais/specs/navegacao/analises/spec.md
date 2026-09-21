# Navegação das análises

## Purpose

Organiza as telas de análise em blocos temáticos coerentes com o domínio e garante que a qualidade dos dados seja um destino de primeira classe, nunca um detalhe escondido atrás dos indicadores.

## ADDED Requirements

### Requirement: Qualidade dos dados como destino de primeira classe

A tela de qualidade dos dados SHALL ser acessível diretamente a partir do menu de análises, e MUST NOT estar subordinada a uma tela de indicador específico.

*Status: ESCOPO ATUAL — a navegação atual em `AppNavigator.tsx` expõe `StatsHome`, `DendrometryStats`, `PhenologyStats`, `InventoryStatsHome`, `InventoryStats`, `InventoryParcela`, `PopulationDynamics` e `GeneralStats`; não há nenhuma rota de qualidade de dados.*

#### Scenario: Acesso à qualidade dos dados

- **WHEN** o usuário abre o menu de análises
- **THEN** a qualidade dos dados é uma opção visível no primeiro nível

#### Scenario: Indicador com exclusões

- **WHEN** um indicador exclui registros do seu cálculo
- **THEN** a tela do indicador oferece acesso ao detalhamento dessas exclusões

### Requirement: Organização temática das análises

As telas de análise SHALL estar organizadas em blocos temáticos nomeados, e cada tela SHALL declarar qual conjunto de dados e qual recorte utiliza.

*Status: ESCOPO ATUAL — a estrutura conceitual proposta pelo usuário deve ser confrontada com a navegação real antes de ser fixada. Classificação: HIPÓTESE A VALIDAR quanto ao mapeamento de cada tela existente para o novo bloco.*

#### Scenario: Tela declara sua origem de dados

- **WHEN** o usuário abre qualquer tela de análise
- **THEN** a tela identifica se utiliza dendrometria, fenologia ou o cruzamento
- **AND** identifica o recorte aplicado, por parcela ou geral

#### Scenario: Preservação de comportamento correto

- **WHEN** a navegação é reorganizada
- **THEN** todas as análises hoje acessíveis permanecem acessíveis
- **AND** nenhuma análise cujo comportamento esteja correto é removida

### Requirement: Exposição da cobertura em cada tela

Cada tela de análise SHALL apresentar a cobertura dos dados que sustentam seus indicadores.

#### Scenario: Tela com dados parciais

- **WHEN** os indicadores de uma tela derivam de um subconjunto dos registros
- **THEN** a tela apresenta quantos registros sustentam os indicadores
- **AND** apresenta quantos ficaram de fora

#### Scenario: Tela sem dados

- **WHEN** não há registros para a tela
- **THEN** a tela informa a ausência de dados
- **AND** distingue ausência de dados de falha de leitura do arquivo

### Requirement: Funcionamento offline preservado

Todas as telas de análise, a qualidade dos dados e a importação SHALL operar sem qualquer acesso à rede.

#### Scenario: Navegação sem conectividade

- **WHEN** o dispositivo está sem conexão
- **THEN** todas as telas de análise funcionam normalmente
- **AND** a exportação e o compartilhamento local permanecem disponíveis
