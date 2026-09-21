# Qualidade dos dados

## Purpose

Torna visível ao usuário o que o aplicativo fez com cada registro: quantos foram aceitos, quantos foram rejeitados, quantos entraram em cada cálculo e por que algum ficou de fora. Sem isso, nenhum indicador apresentado pode ser auditado.

## ADDED Requirements

### Requirement: Relatório de qualidade sempre disponível

O sistema SHALL produzir, a cada carregamento dos dados, um relatório de qualidade acessível ao usuário contendo registros processados, aceitos, aceitos com ressalva e rejeitados, com o motivo de cada rejeição e ressalva.

*Status: ESCOPO ATUAL — capacidade inexistente hoje. Classificação: MELHORIA NECESSÁRIA PARA AUDITABILIDADE.*

#### Scenario: Conjunto de dados com problemas

- **WHEN** o usuário abre a tela de qualidade dos dados com registros contendo erros
- **THEN** o sistema exibe o total processado, o total aceito, o total com ressalva e o total rejeitado
- **AND** a soma das categorias é igual ao total processado

#### Scenario: Conjunto de dados íntegro

- **WHEN** todos os registros atendem ao contrato canônico
- **THEN** o sistema informa explicitamente que nenhum registro foi rejeitado ou excluído
- **AND** não omite a tela por ausência de problemas

#### Scenario: Detalhe por registro

- **WHEN** o usuário seleciona uma ocorrência no relatório
- **THEN** o sistema identifica a linha de origem, o campo afetado e o valor original
- **AND** não exibe um valor corrigido por inferência no lugar do original

### Requirement: Erro bloqueante distinto de aviso

O sistema SHALL classificar cada ocorrência como bloqueante ou como aviso. Uma ocorrência bloqueante MUST impedir o uso do registro nos indicadores afetados; um aviso MUST NOT impedir o uso do registro.

#### Scenario: Registro sem identidade

- **WHEN** um registro não possui parcela ou número de árvore
- **THEN** a ocorrência é classificada como bloqueante
- **AND** o registro é excluído dos indicadores que dependem de identidade

#### Scenario: Observação com formatação atípica

- **WHEN** um registro possui observação livre com quebras de linha
- **THEN** a ocorrência é classificada como aviso
- **AND** o registro permanece elegível para todos os indicadores

### Requirement: Cobertura de medição por indicador

Cada indicador quantitativo SHALL expor o número de registros elegíveis e o número de registros considerados, de modo que a cobertura da medição seja verificável.

*Status: CONFIRMADO NO CÓDIGO — hoje apenas `coberturaDados` (cruzamento dendro/fenologia) é exposto; nenhum indicador individual expõe seu denominador efetivo. Classificação: ERRO DE APRESENTAÇÃO.*

#### Scenario: Indicador com dados parciais

- **WHEN** um indicador de DAP médio é calculado sobre 40 de 120 indivíduos elegíveis
- **THEN** o sistema apresenta a cobertura junto ao valor
- **AND** o usuário consegue distinguir um valor calculado sobre poucos registros de um valor calculado sobre a maioria

#### Scenario: Indicador sem nenhum dado elegível

- **WHEN** nenhum registro atende aos critérios de elegibilidade de um indicador
- **THEN** o sistema apresenta o indicador como indisponível
- **AND** não apresenta zero como se fosse um valor medido

### Requirement: Duplicidades e divergências expostas

O sistema SHALL listar chaves duplicadas, divergências de espécie para a mesma árvore e registros de dendrometria sem correspondência em fenologia (e vice-versa).

#### Scenario: Chave duplicada

- **WHEN** o mesmo par Parcela + Árvore aparece mais de uma vez na mesma campanha
- **THEN** todas as ocorrências são listadas com suas diferenças
- **AND** o sistema não elege automaticamente uma delas

#### Scenario: Registro sem par no cruzamento

- **WHEN** um indivíduo possui registro dendrométrico mas nenhum registro fenológico
- **THEN** o sistema o lista como não cruzado
- **AND** informa o efeito dessa ausência sobre os indicadores dependentes de fenologia
