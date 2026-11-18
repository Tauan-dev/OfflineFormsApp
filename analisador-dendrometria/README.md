# Analisador de Dendrometria

Ferramenta local para importar, validar, processar e visualizar planilhas de dendrometria
(`dendometria_julho.xlsx`, `dendrometria.csv` e similares). Independente do aplicativo mobile.
Todo o processamento ocorre no computador do usuário; nenhum dado é enviado à internet.

## Como executar

| Forma | Comando | Quando usar |
|---|---|---|
| Desenvolvimento | `pip install -r requirements-dev.txt` e depois `streamlit run app.py` | quem já tem Python |
| Atalho com logo | duplo clique em `criar_atalho.bat` | cria "Analisador de Dendrometria" na Área de Trabalho (e na pasta) com o ícone `assets/icone.ico`; o logo é regenerável com `python assets/gerar_logo.py` |
| Launcher Windows | duplo clique em `iniciar_analises.bat` | usa a pasta distribuível ou cria um `.venv` na 1ª execução (requer internet uma vez e Python 3.10+) |
| Pasta distribuível | `build_windows.bat` gera `dist\AnalisadorDendrometria\` e `.zip` | usuário final sem Python e sem internet |

O launcher (`launcher.py`) escolhe uma porta livre, inicia o servidor só em `127.0.0.1`, abre o navegador e
encerra de forma controlada pelo botão **Encerrar aplicação**, por Ctrl+C ou ao fechar a janela.

### Empacotamento para Windows

1. Em um Windows x64 com internet, execute `build_windows.bat` na pasta do projeto.
2. O script baixa o Python 3.12 embutido oficial, instala as dependências fixadas, copia a aplicação,
   valida as importações e gera `dist\AnalisadorDendrometria.zip` (~150–200 MB).
3. Distribua o `.zip`. O usuário descompacta e executa `iniciar_analises.bat`.

Optou-se por uma **pasta distribuível com Python embutido** em vez de um `.exe` único (PyInstaller), que
costuma ser instável com Streamlit e produz executáveis grandes e lentos para iniciar.

## Uso

1. Selecione o arquivo `.xlsx` ou `.csv` na barra lateral (para XLSX, escolha a planilha).
2. **Importação**: metadados (tamanho, linhas, SHA-256) e mapeamento de colunas. Se faltar coluna obrigatória,
   a análise não roda até o mapeamento manual.
3. **Qualidade dos dados** e **Registros excluídos**: cada problema com linha, célula, valor original,
   severidade e classe de recuperação.
4. **Visão geral, Dendrometria, Parcelas, Espécies, Indivíduos, Observações**: indicadores com unidade,
   denominador, cobertura e status. Filtros da barra lateral são aplicados **antes** do cálculo.
5. **Exportação**: XLSX completo, CSVs, manifesto JSON e relatório HTML.
6. **Metodologia**: fórmulas, tolerâncias, decisões em uso e itens pendentes de definição.

Sem interface: `python processar_planilha.py ARQUIVO.xlsx --planilha dendrometria --saida resultados`.

### Indicadores fundamentados na literatura

Sem depender de decisões da equipe, os itens abaixo foram resolvidos pela literatura citada. Cada um mostra
fórmula, denominador, cobertura e fonte, e tem teste e caso de validação matemática:

| Indicador | Regra | Fonte | Status |
|---|---|---|---|
| Diâmetro quadrático médio (dg) | dg = √(Σ DAP²/n), exibido **separado** da média aritmética | Finger (1992); Soares, Paula Neto & Souza (2011) | VÁLIDO |
| Área basal com multifustes | g do indivíduo = Σ π·dⱼ²/40000; DAP equivalente = √(Σ dⱼ²); fustes extraídos da observação só quando a quantidade declarada = valores listados | Finger (1992), adotado no Manual de Dendrometria da CEPLAC; Stewart & Salazar (1992) | VÁLIDO COM RESSALVA |
| Área basal por hectare | ABₕₐ = G / Σaⱼ; predefinição do arboreto ESARM: 98 parcelas, 36 plantas, 2 × 2 m → 144 m² (área útil); parcelas fora do desenho (PX1–PX5) excluídas de G e de A; sensibilidade a 100 m² e 196 m² exibida | Barazetti et al. (2011); Gama-Rodrigues et al. (1999) | VÁLIDO COM RESSALVA |
| Shannon (ln), Pielou, Simpson (1 − D) | sobre indivíduos únicos por espécie | Brower & Zar (1984); Magurran (2004) | VÁLIDO COM RESSALVA (arboreto plantado) |
| DR, DoR, FA, FR, VI | parâmetros fitossociológicos por espécie | Mueller-Dombois & Ellenberg (1974) | na tabela de espécies |
| Limite físico de altura | > 120 m é EXTREMO (maior árvore viva medida: 115,92 m) | Hyperion, *Sequoia sempervirens* | validado |
| Siglas de altura | HESG (solo → 1º galho vivo), HESGCOPA (solo → início da copa), HC, HT (solo → ápice) | `referencias/WhatsApp Image 2026-11-17 17.35.09.jpeg` | definido |
| Copa | comprimento = HT − HESGCOPA; proporção = comprimento/HT | derivado das definições acima | válido com ressalva |
| Coerência entre alturas | HC, HESG, HESGCOPA ≤ HT (advertência, nada é corrigido) | definição de altura total (Manual CEPLAC; Soares et al., 2007) | validado |

A predefinição da ESARM só é oferecida quando as parcelas numéricas do arquivo cabem no desenho publicado (1–98).
Na barra lateral (**Decisões metodológicas → Área basal por hectare**) o usuário pode trocá-la por outra área ou
desligá-la; na linha de comando, `--area-parcela 400 --unidade-area m² --desenho "..."` ou `--sem-predefinicao`.
Toda escolha vai para o manifesto (`decisoes_do_usuario`).

## Estrutura

```
app.py                  interface Streamlit (só exibe resultados)
launcher.py             porta livre + navegador + encerramento
iniciar_analises.bat    launcher Windows
criar_atalho.bat/.ps1   cria o atalho com logo na Area de Trabalho
static/                 fontes (Atkinson Hyperlegible Next, Source Serif 4; licenca OFL) servidas offline pelo app
assets/                 logo.svg/png e icone.ico
build_windows.bat       empacotamento (Python embutido)
processar_planilha.py   processamento em linha de comando + relatório + conferência independente
validar_indicadores.py  relatório de validação matemática (relatorios/validacao_matematica.md)
analytics/
  ingestion.py          leitura XLSX/CSV preservando tipo, coordenada e hash
  canonicalization.py   mapeamento de colunas e interpretação de números, datas e identificadores
  quality.py            diagnósticos, status do registro e classes de recuperação
  dendrometry.py        DAP, alturas, área basal, volumes, rankings, distribuição diamétrica
  inventory.py          contagens, parcelas, espécies, indivíduos, mortalidade, replantio
  observations.py       menções potenciais em observações (com negação)
  results.py            contrato dos indicadores, estados e tolerâncias
  export.py             XLSX, CSV, HTML e manifesto
tests/                  85 testes (pytest)
fixtures/synthetic/     arquivos sintéticos; fixtures/expected/ resultados manuais
```

## Testes

```
pip install -r requirements-dev.txt
python -m pytest --cov=analytics
python validar_indicadores.py
```

Os testes de regressão da planilha real rodam quando `../OfflineFormsApp/referencias/DENDROMETRIA.xlsx_15-09_ATUAL.xlsx`
existe; caso contrário são ignorados.

## Regras principais

- Nenhum dado original é alterado; nada inválido é corrigido por suposição; ausência nunca vira zero.
- Identificadores: só remove espaço externo (`7`, `07` e `007` são distintos).
- DAP elegível: número > 0, medição não duplicada e ≤ 300 cm. O limite de 300 cm é **regra legada não validada**:
  valores acima são preservados, listados para revisão e só entram no cálculo por opção explícita.
- Datas gravadas pelo Excel em colunas numéricas (ex.: DAP `12.4` → 12/abr) **não são reconstruídas**; o texto
  exibido aparece apenas como pista para revisão humana.
- Indicador sem metodologia definida aparece como **BLOQUEADO**, nunca como zero.
- Área seccional `g = π·DAP²/40000` (m²); volume cilíndrico `g·HT`; volume comercial de Spurr
  (Jorge, 1982) só com HC — conforme referências em `OfflineFormsApp/referencias/`.

## Decisões ainda pendentes (não resolvíveis pela literatura)

- **Diâmetro médio oficial do projeto (M5):** dg e média aritmética são calculados; qual deles é a referência é escolha da equipe.
- **Estado vital estruturado:** sem coluna vivo/morto/não localizado/não avaliado, mortalidade e sobrevivência seguem
  bloqueadas (falta de dado, não de método). O desenho de 36 plantas por parcela já é documentado.
- **Nota (*) da definição de HESGCOPA:** a imagem de siglas traz um asterisco sem a nota; comprimento e proporção de copa saem com ressalva até a nota ser fornecida.
- **Área da parcela em campo:** a literatura dá 100 m² (texto) e 144 m² (geometria 6 × 6 a 2 × 2 m); adotou-se 144 m²
  com sensibilidade exibida. Uma medição de campo encerra a questão.
- **Multifustes sem padrão estrutural** (45 na planilha real): revisão humana.
- Indicador composto de saúde, dano leve/severo, serrapilheira, classificação do povoamento: sem escala ou dado.
- Limite legado de 300 cm de DAP: não é limite físico; sem efeito na planilha real (máximo 125 cm).


## Interface

As fichas de indicador são um componente React próprio (`componentes/fichas/`) carregado dentro do Streamlit. Ele usa três componentes copiados do código-fonte original, com adaptações mínimas indicadas no topo de cada arquivo:

| Componente | Origem | Uso |
|---|---|---|
| BlurFade | Magic UI (MIT) | entrada dos cartões em cascata |
| CountUp, modo "roll" | React Bits (MIT + Commons Clause) | dígitos rolando até o valor; ao filtrar, rola do valor anterior ao novo; separador decimal brasileiro |
| SpotlightCard | React Bits (MIT + Commons Clause) | brilho que segue o cursor e o foco do teclado |

As licenças estão em `componentes/fichas/licencas/`. A Commons Clause permite o uso dentro de um aplicativo; proíbe revender ou redistribuir os componentes isoladamente.

**Quem só usa o sistema não precisa de Node:** o build compilado (`componentes/fichas/frontend/build/`) vai junto, com as fontes, e funciona offline. Para alterar os cartões: `cd componentes/fichas/frontend`, `npm install`, `npm run build`. O `build_windows.bat` copia o componente sem a pasta `node_modules`.

Cada ficha mostra valor, barra de cobertura, denominador, a **ressalva visível** (quando há) e o estado; "Fórmula e notas" abre com clique ou Enter. Indicadores sem valor aparecem hachurados, nunca como zero. Se o build não existir (ou com `ANALISADOR_FICHAS_HTML=1`), o app usa fichas equivalentes em HTML/CSS.

**Acessibilidade:** com "reduzir movimento" ativado no sistema operacional, nada se move e o valor final aparece direto; leitores de tela recebem "nome: valor unidade, estado" (nunca os dígitos em movimento) e o quadro se chama "Fichas de indicadores"; a página é declarada em pt-BR; foco por teclado visível; estado indicado por ícone e texto, não só por cor (contraste ≥ 4,5:1).
