# Base de dados — Pix PJ e inclusão digital-financeira (DiD escalonado)

Base para o artigo *"Efeito causal da chegada do Pix Pessoa Jurídica sobre a
inclusão digital-financeira dos pequenos negócios: evidência com
diferenças-em-diferenças escalonadas em municípios do Centro-Oeste"*.

Painel **município × mês**, jan/2019 a dez/2024 (72 meses), para **todos os
467 municípios de MT, MS e GO**. A amostra do artigo é marcada por
indicadoras, para que a mesma base sirva à estimação principal e às
robustezes (ex.: ampliar para os 142 municípios de MT).

## Arquivos finais

| Arquivo | Conteúdo |
|---|---|
| `dados/painel_pix_pj_mensal.csv` | painel mensal (467 × 72 = 33.624 linhas) |
| `dados/painel_pix_pj_anual.csv` | painel anual 2019–2024 (para juntar ao IDF-MT) |
| `dados/dicionario_variaveis.csv` | dicionário de variáveis |
| `dados/processados/*.csv` | bases intermediárias por fonte |

`dados/brutos/` (arquivos originais, ~8 GB) não vai para o Git; os scripts
baixam tudo de novo.

## Como reproduzir

Execute de dentro de `codigo/`, nesta ordem:

```bash
python 01_pix_bcb.py            # Pix por município (BCB/Olinda)
bash 02a_baixar_cnpj.sh 2026-10 # Cadastro CNPJ (Receita), ~7 GB
python 02b_processar_cnpj.py    # séries mensais de empresas e MEI
python 03_estban_bcb.py         # ESTBAN (crédito por banco e município)
python 04_covariaveis_ibge.py   # população, PIB, IDHM
python 05_montar_painel.py      # junta tudo e cria tratamento/resultados
```

Requisitos: Python 3 com `pandas` e `numpy`; `curl`, `unzip` e `grep`.

## Fontes

| Bloco | Fonte | Acesso |
|---|---|---|
| Pix por município | BCB — Estatísticas do Pix, série `TransacoesPixPorMunicipio` (desde nov/2020) | API Olinda |
| Empresas, aberturas, baixas, MEI, Simples | Receita Federal — Cadastro Nacional da Pessoa Jurídica (dados abertos, referência 2026-10) | arquivos.receitafederal.gov.br |
| Crédito, depósitos, agências, IHH | BCB — ESTBAN por município (Documento 4500) | bcb.gov.br |
| População | IBGE — Estimativas (SIDRA 6579) e Censo 2022 (SIDRA 4709) | API SIDRA |
| PIB municipal | IBGE — PIB dos Municípios (SIDRA 5938) | API SIDRA |
| IDHM 2010 | Atlas do Desenvolvimento Humano (PNUD/IPEA/FJP), série `ADH_IDHM` | Ipeadata |
| Validação | MEMP — Mapa de Empresas, planilhas mensais 2026 | gov.br/memp |

## Decisões e limitações que afetam o artigo

**1. Quase não há variação no "primeiro Pix PJ".** Com os dados mensais do
BCB, 456 dos 467 municípios já registram transação Pix com PJ em
**nov/2020**, o mês de lançamento (os demais, em dez/2020). Na amostra de
municípios médios, todos são tratados em nov/2020. É exatamente a ameaça
"variação insuficiente nas datas" do Quadro 4: com a definição original
não há DiD escalonado (todos são tratados ao mesmo tempo e não existe grupo
de controle ainda-não-tratado).

Por isso a base traz **definições alternativas de tratamento por intensidade
de adoção** — o mês em que a fração de empresas ativas que recebem Pix
(`QT_PES_RecebedorPJ / ativas`) atinge 10%, 25% ou 50% (`G_adesao10`,
`G_adesao25`, `G_adesao50`). Elas geram coortes de fato escalonadas e têm
interpretação econômica clara ("chegada efetiva do Pix PJ aos pequenos
negócios"). Sugere-se reescrever a seção 4.2 com essa definição e manter a
original apenas como descrição.

**2. Crédito PJ.** O ESTBAN não separa crédito a pessoas jurídicas e físicas.
`y3_ihh_credito` e `y5_credito_pc` usam o **crédito total** (verbete 160).
Para crédito PJ por município seria preciso o SCR (não público nesse nível).
Os depósitos à vista também vêm agregados (PF+PJ+governo) no ESTBAN.
Municípios sem agência/posto bancário não aparecem no ESTBAN
(`tem_agencia_estban = 0`).

**3. Não-reporte no ESTBAN.** Quando uma instituição aparece com todos os
saldos zerados no país inteiro num mês (falha de envio — ex.: Santander em
jan–mar/2025), o saldo é imputado com o último valor reportado no mesmo
município (`estban_imputado = 1`).

**4. Reconstrução histórica do CNPJ.** O cadastro da Receita é uma foto da
data de referência. Os estoques mensais (empresas ativas, MEIs ativos) são
reconstruídos pelas datas de início de atividade, de situação cadastral e de
opção/exclusão do Simples/MEI. Como o arquivo guarda só a **última**
situação e a **última** opção de cada empresa, o estoque do passado é uma
aproximação (empresas que foram inaptas e voltaram, ou que saíram e
voltaram ao MEI, perdem esse histórico). As aberturas por mês são
confiáveis. A validação contra o Mapa de Empresas (MEMP) está em
`dados/processados/validacao_mapa_empresas.csv`.

**5. Novos MEIs.** `aberturas_mei` = CNPJs abertos no mês que optaram pelo
MEI no mesmo mês (formalização de MEI). `opcoes_mei` conta todas as opções
pelo MEI no mês (inclui empresas já existentes que migraram).

**6. Amostra de 33 municípios.** O critério "50 mil a 600 mil habitantes"
aplicado à população de 2019 seleciona **40** municípios (GO 23, MT 10, MS 7),
marcados em `amostra_50a600mil`. Para usar exatamente os 33 de Franco (2026),
crie `dados/amostra_artigo.csv` com a coluna `cod_ibge` e rode o script 05:
será criada a indicadora `amostra_artigo`. Cuiabá, Goiânia e Campo Grande,
citadas como exemplo no Quadro 1, têm mais de 600 mil habitantes.

**7. IDF-MT (Y4).** O índice de Franco (2026) não é público e não foi
reconstruído aqui. Junte-o ao painel anual pela chave `cod_ibge` + `ano`.

**8. Campus universitário.** Os microdados do INEP não puderam ser baixados
(cadeia de certificado incompleta no servidor). `campus` = existe ao menos um
estabelecimento ativo em dez/2019 com CNAE de educação superior (8531-7/00 ou
8532-5/00) no município. Útil como proxy; pode ser substituído pelo Censo da
Educação Superior.

## Exemplo de estimação (R, pacote `did`)

```r
library(did)
p <- read.csv("dados/painel_pix_pj_mensal.csv")
p <- subset(p, amostra_50a600mil == 1)
cs <- att_gt(yname = "asinh_y1_pix_pj_por_empresa", tname = "periodo",
             idname = "id", gname = "G_adesao25_t",
             xformla = ~ ln_pop_2019 + idhm_2010 + ln_pib_pc_2019 + campus,
             data = p, control_group = "notyettreated", est_method = "dr",
             clustervars = "id", bstrap = TRUE)
aggte(cs, type = "dynamic")
```
