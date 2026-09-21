# Tarefas

> Plano de execução. Nenhuma tarefa deve ser iniciada antes da aprovação da proposta.
> Fases 3 e 4 estão bloqueadas por decisões metodológicas (`design.md` § Decisões metodológicas pendentes).

## 0. Desbloqueio

- [ ] 0.1 Disponibilizar `dendrometria_julho.xlsx` no diretório do projeto para confirmação das hipóteses de corrupção de dados
- [ ] 0.2 Disponibilizar os CSVs originais de dendrometria e fenologia para os Stage Gates 1 e 2
- [ ] 0.3 Disponibilizar `MÉTRICAS PARA ESTUDO DO ARBORETO.docx` para resolver M4–M10 e M13
- [ ] 0.4 Registrar o número de indivíduos implantados por parcela e suas exceções (R27)
- [ ] 0.5 Registrar área das parcelas, unidade e desenho amostral (R26)
- [ ] 0.6 Decidir M14 — normalização de zeros à esquerda no número da árvore (bloqueia 1.2)

## 1. Fase 1 — Contrato de dados e diagnóstico

- [ ] 1.1 Reescrever `parseCsv` como máquina de estados sobre caracteres, tratando quebra de linha dentro de campo entre aspas (R14)
- [ ] 1.2 Criar o módulo de normalização canônica de parcela, árvore, espécie, número e data, idempotente e preservando o valor original (R12)
- [ ] 1.3 Definir os tipos canônicos de medição com os estados medido, não medido, não aplicável e inválido (contrato canônico)
- [ ] 1.4 Validar o cabeçalho do CSV antes do mapeamento posicional e reportar divergência (R15)
- [ ] 1.5 Implementar detecção de versão do formato a partir do cabeçalho
- [ ] 1.6 Substituir `catch { return [] }` em `dataLoader` por propagação de erro distinguível de ausência de dados (R16)
- [ ] 1.7 Produzir a estrutura de diagnóstico de qualidade no carregamento, ainda sem tela
- [ ] 1.8 Tornar a gravação do CSV atômica: escrever em temporário e trocar (R31)
- [ ] 1.9 Escrever testes de ida e volta do CSV: vírgula, aspas escapadas, multilinha, campo final vazio, acentuação com BOM
- [ ] 1.10 Escrever testes de normalização: idempotência, espaços, caixa, separador decimal, valor com dois separadores
- [ ] 1.11 Comparar a leitura dos arquivos reais entre parser antigo e novo, registro a registro, e explicar cada divergência
- [ ] 1.12 **Stage Gate 1** — paridade do parser confirmada nos arquivos reais; nenhum valor de indicador alterado nesta fase

## 2. Fase 2 — Correções críticas dos cálculos

- [ ] 2.1 Alinhar `classificarFito` ao vocabulário canônico `vivo | morto | com dano`, com categoria explícita para valor não reconhecido (R1)
- [ ] 2.2 Excluir do denominador dos percentuais de condição os registros com fitossanitário vazio (R32)
- [ ] 2.3 Corrigir `alertasFito` para alertar apenas em estados problemáticos (R2)
- [ ] 2.4 Remover `pctDanoLeve` e `pctDanoSevero` da saída e da apresentação (R3)
- [ ] 2.5 Redefinir `indicadorSaude` com denominador explícito e retorno indisponível quando não houver registros avaliados (R4)
- [ ] 2.6 Unificar a contagem de saúde entre `calcInventoryStats` e `calcParcelaStats` em uma única implementação
- [ ] 2.7 Corrigir `classificarPovoamento` para nunca tratar `mediaDap === null` como limiar atendido (R5)
- [ ] 2.8 Implementar a política única de elegibilidade de DAP, parametrizada, aplicada a média, mínimo, máximo, área basal e distribuição (R6, R7)
- [ ] 2.9 Reportar por indicador o número de valores considerados e excluídos com motivo (R17)
- [ ] 2.10 Expor contagem bruta e denominador nos indicadores fenológicos (R8)
- [ ] 2.11 Remover de `StatsScreen` a reconstrução de contagem a partir de percentual arredondado (R8)
- [ ] 2.12 Tratar intensidade fenológica como variável numérica em vez de categoria textual (R9)
- [ ] 2.13 Separar contagem de registros de contagem de indivíduos no inventário (R10)
- [ ] 2.14 Separar e rotular abundância, frequência em parcelas, frequência relativa e riqueza (R11)
- [ ] 2.15 Aplicar a chave canônica normalizada em `calcCobertura` (R12)
- [ ] 2.16 Renomear `interacoesFauna` para refletir o que de fato mede enquanto não houver campo estruturado (R13)
- [ ] 2.17 Apresentar indicadores de parcela sem fenologia como indisponíveis e retirá-los do ranking de saúde (R18)
- [ ] 2.18 Deixar de tratar registros sem parcela como uma parcela chamada "Sem parcela" (R19)
- [ ] 2.19 Corrigir `isReplanted` e `extractYear` para não aceitar texto arbitrário como replantio nem como ano (R20)
- [ ] 2.20 Remover das interpretações automáticas a equiparação entre taxa de replantio e mortalidade (R21)
- [ ] 2.21 Apresentar o maior indivíduo com critério nomeado, unidade e data da medição (R30)
- [ ] 2.22 Rotular cada indicador de altura com a variável utilizada (R29, parte de apresentação)
- [ ] 2.23 Escrever, por indicador, o teste entrada → cálculo manual → esperado → produzido → tolerância → conclusão
- [ ] 2.24 Escrever testes de casos-limite: zero, ausência, inválido, extremo, divisão por zero, múltiplas parcelas, duplicidade, morto, com dano, DAP ausente
- [ ] 2.25 Documentar o antes/depois do indicador de saúde e dos alertas sobre um conjunto conhecido
- [ ] 2.26 **Stage Gate 2** — validação assistida pelo usuário dos cálculos corrigidos, em especial saúde e alertas

## 3. Fase 3 — Evolução do modelo de coleta (bloqueada por M1, M2, M3, M11)

- [ ] 3.1 Separar estado vital de condição fitossanitária no contrato e no formulário de fenologia (R23)
- [ ] 3.2 Adicionar o campo de motivo de ausência de medição no formulário de dendrometria (R24)
- [ ] 3.3 Adicionar a representação de indivíduo multifuste (R25)
- [ ] 3.4 Anexar as colunas novas ao final do cabeçalho, preservando a ordem das existentes
- [ ] 3.5 Mapear os valores históricos `vivo`, `morto` e `com dano` para o novo modelo sem alterar os arquivos
- [ ] 3.6 Implementar backup datado verificado antes da primeira gravação no formato novo
- [ ] 3.7 Implementar validação pós-migração com comparação de contagem de registros e rollback automático em divergência
- [ ] 3.8 Implementar o relatório de migração apresentado ao usuário
- [ ] 3.9 Escrever testes de compatibilidade de leitura de arquivos da versão anterior
- [ ] 3.10 Escrever teste de representação de indivíduo vivo com dano
- [ ] 3.11 **Stage Gate 3** — em dispositivo com dados reais, nenhum registro perdido e rollback verificado

## 4. Fase 4 — Métricas do arboreto (bloqueada por M4–M10, M13, M15)

- [ ] 4.1 Documentar cada métrica com objetivo, entradas, unidades, obrigatoriedade, inclusão, exclusão, fórmula, variáveis, tratamento de ausência, unidade do resultado, interpretação, casos-limite e exemplo numérico
- [ ] 4.2 Implementar totais de parcelas, indivíduos cadastrados e indivíduos avaliados
- [ ] 4.3 Implementar mortalidade e sobrevivência sobre denominador de implantação registrado (R27)
- [ ] 4.4 Implementar altura média por parcela e do arboreto, com a variável declarada (M6)
- [ ] 4.5 Implementar diâmetro médio pelo método aprovado (M5)
- [ ] 4.6 Implementar área basal absoluta; manter a área basal por hectare não implementada até M/R26
- [ ] 4.7 Implementar os rankings de maior indivíduo conforme M7
- [ ] 4.8 Implementar a distribuição diamétrica com classes explícitas e cobertura reportada
- [ ] 4.9 Implementar abundância, frequência e riqueza conforme M9
- [ ] 4.10 Implementar o índice de diversidade somente se M8 o aprovar
- [ ] 4.11 Implementar os indicadores de flores, frutos, folhas e fitossanidade por parcela
- [ ] 4.12 Implementar os indicadores de replantio conforme M15
- [ ] 4.13 Implementar os registros ecológicos aprovados; manter serrapilheira sem escala inventada (M10)
- [ ] 4.14 Escrever o teste com exemplo numérico verificado manualmente para cada métrica
- [ ] 4.15 Listar explicitamente as métricas não implementadas e o motivo do bloqueio
- [ ] 4.16 **Stage Gate 4** — conferência das métricas contra cálculo manual do usuário sobre os dados de validação

## 5. Fase 5 — Importação segura

- [ ] 5.1 Implementar a seleção local de arquivo, sem qualquer acesso à rede
- [ ] 5.2 Implementar a leitura estrutural do arquivo e a detecção de cabeçalho
- [ ] 5.3 Implementar o mapeamento de colunas com proposta automática e confirmação do usuário
- [ ] 5.4 Implementar a pré-visualização das linhas interpretadas
- [ ] 5.5 Implementar a detecção de tipos incompatíveis, incluindo data em coluna numérica e texto em coluna de medição
- [ ] 5.6 Implementar a detecção de linhas quebradas e colunas deslocadas
- [ ] 5.7 Implementar a detecção de chaves duplicadas e de registros sem parcela ou árvore
- [ ] 5.8 Implementar o relatório de erros por linha com separação entre bloqueante e aviso
- [ ] 5.9 Implementar o bloqueio de importação estruturalmente inválida
- [ ] 5.10 Implementar a detecção de colisão com registros existentes e a escolha explícita do usuário
- [ ] 5.11 Garantir a preservação do arquivo de origem
- [ ] 5.12 Implementar o resumo final de aceitos, aceitos com ressalva e rejeitados
- [ ] 5.13 Avaliar e decidir a dependência de parser XLSX offline para importação de Excel
- [ ] 5.14 Escrever testes com arquivos contendo cada classe de defeito prevista
- [ ] 5.15 Escrever teste de importação com o dispositivo em modo avião
- [ ] 5.16 Escrever teste de cancelamento sem gravação
- [ ] 5.17 **Stage Gate 5** — importação de arquivo real problemático produz relatório correto sem gravar dados inválidos

## 6. Fase 6 — Reorganização das telas

- [ ] 6.1 Confrontar a estrutura conceitual proposta com a navegação real e definir o mapeamento de cada tela existente
- [ ] 6.2 Implementar a tela de qualidade dos dados no primeiro nível do menu de análises
- [ ] 6.3 Apresentar registros processados, válidos, inválidos, incompletos, duplicidades, medições ausentes e exclusões com motivo
- [ ] 6.4 Implementar o acesso ao detalhamento de exclusões a partir de cada indicador
- [ ] 6.5 Reorganizar as rotas de análise em blocos temáticos
- [ ] 6.6 Apresentar a cobertura dos dados em cada tela de análise
- [ ] 6.7 Distinguir na interface a ausência de dados da falha de leitura
- [ ] 6.8 Verificar que toda análise previamente acessível permanece acessível
- [ ] 6.9 Escrever teste de operação sem conectividade em todas as telas
- [ ] 6.10 **Stage Gate 6** — navegação validada em dispositivo pelo usuário

## 7. Fase 7 — Migração, regressão e validação final

- [ ] 7.1 Executar a migração em dispositivo com dados reais, com backup e relatório
- [ ] 7.2 Verificar o rollback a partir do backup
- [ ] 7.3 Executar a suíte de regressão de todas as funcionalidades existentes
- [ ] 7.4 Executar o fluxo ponta a ponta offline: coleta, gravação, leitura, cálculo, exibição, exportação e compartilhamento
- [ ] 7.5 Preencher a matriz de rastreabilidade com o resultado obtido por linha
- [ ] 7.6 Registrar formalmente toda pendência não resolvida
- [ ] 7.7 **Stage Gate 7** — aceite final do usuário sobre os dados reais
