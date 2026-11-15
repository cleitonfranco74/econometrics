# Base de dados — Pix PJ e inclusão digital-financeira (DiD escalonado)

Base para o artigo *"Efeito causal da chegada do Pix Pessoa Jurídica sobre a
inclusão digital-financeira dos pequenos negócios: evidência com
diferenças-em-diferenças escalonadas em municípios do Centro-Oeste"*.

Painel **município × mês**, jan/2019 a dez/2024 (72 meses).

**Amostra do artigo: os 40 municípios de MT, MS e GO com população entre
50 mil e 600 mil habitantes em 2019** (IBGE): GO 23, MT 10, MS 7. Estão em
`dados/painel_pix_pj_mensal_amostra40.csv`. O arquivo completo
(`painel_pix_pj_mensal.csv`) traz os 467 municípios das três UFs, com a
indicadora `amostra_50a600mil`, para robustezes (ex.: os 142 de MT).

## Arquivos finais

| Arquivo | Conteúdo |
|---|---|
| `dados/painel_pix_pj_mensal_amostra40.csv` | **painel da amostra** (40 × 72 = 2.880 linhas) |
| `dados/painel_pix_pj_mensal.csv` | painel mensal, todos os municípios de MT/MS/GO (467 × 72) |
| `dados/painel_pix_pj_anual.csv` | painel anual 2019–2024 (para juntar ao IDF-MT) |
| `dados/dicionario_variaveis.csv` | dicionário de variáveis |
| `dados/processados/*.csv` | bases intermediárias por fonte |

`dados/brutos/` (arquivos originais, ~8 GB) não vai para o Git; os scripts
baixam tudo de novo.

## Como reproduzir

Execute de dentro de `codigo/`, nesta ordem:

```bash
python 01_pix_bcb.py            # Pix por município (BCB/Olinda)
bash 02a_baixar_cnpj.sh         # Cadastro CNPJ, release 2024.09 (GitHub), ~5,6 GB
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
| Empresas, aberturas, baixas, MEI, Simples | Receita Federal — Cadastro Nacional da Pessoa Jurídica (dados abertos), retrato de set/2024 | release 2024.09 de github.com/jonathands/dados-abertos-receita-cnpj (espelho dos arquivos da Receita) |
| Crédito, depósitos, agências, IHH | BCB — ESTBAN por município (Documento 4500) | bcb.gov.br |
| População | IBGE — Estimativas (SIDRA 6579) e Censo 2022 (SIDRA 4709) | API SIDRA |
| PIB municipal | IBGE — PIB dos Municípios (SIDRA 5938) | API SIDRA |
| IDHM 2010 | Atlas do Desenvolvimento Humano (PNUD/IPEA/FJP), série `ADH_IDHM` | Ipeadata |

## Decisões e limitações que afetam o artigo

**1. Quase não há variação no "primeiro Pix PJ".** Com os dados mensais do
BCB, 456 dos 467 municípios já registram transação Pix com PJ em
**nov/2020**, o mês de lançamento (os demais, em dez/2020). Na amostra de
municípios médios, todos são tratados em nov/2020. É exatamente a ameaça
"variação insuficiente nas datas" do Quadro 4: com a definição original
não há DiD escalonado (todos são tratados ao mesmo tempo e não existe grupo
de controle ainda-não-tratado).

Por isso a base traz **definições alternativas de tratamento por intensidade
de adoção**, que geram coortes de fato escalonadas:

- `G_adesao10/25/50`: mês em que a fração de empresas ativas que recebem Pix
  (`QT_PES_RecebedorPJ / ativas`) atinge 10%, 25% ou 50%;
- `G_difusao25/50`: mês em que o número de empresas que recebem Pix no
  município atinge 25% ou 50% do seu próprio nível médio de 2024 (medida sem
  escala, à moda das curvas de difusão).

Têm interpretação econômica clara ("chegada efetiva do Pix PJ aos pequenos
negócios"). Sugere-se reescrever a seção 4.2 com uma delas e manter a
original apenas como descrição. A distribuição das coortes na amostra está em
`dados/coortes_amostra40.csv`.

**2. Crédito PJ.** O ESTBAN não separa crédito a pessoas jurídicas e físicas.
`y3_ihh_credito` e `y5_credito_pc` usam o **crédito total** (verbete 160).
Para crédito PJ por município seria preciso o SCR (não público nesse nível).
Os depósitos à vista também vêm agregados (PF+PJ+governo) no ESTBAN.
Municípios sem agência bancária não aparecem no ESTBAN
(`tem_agencia_estban = 0`; 296 dos 467 municípios aparecem).
**O ESTBAN não inclui cooperativas de crédito** (Sicredi, Sicoob etc.), muito
relevantes no Centro-Oeste: o IHH mede a concentração entre bancos, não do
mercado de crédito inteiro. Vale citar essa limitação ao discutir H3.

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
confiáveis. Como o retrato é de **set/2024**, as variáveis do CNPJ (e as que
dependem delas: `y1_pix_pj_por_empresa`, `y2_aberturas_mei`, `G_adesao*`)
vão até set/2024; out–dez/2024 ficam vazios. Para fechar dez/2024, rode
`bash 02a_baixar_cnpj.sh receita 2025-01` (servidor da Receita, lento).

**5. Novos MEIs.** `aberturas_mei` = CNPJs abertos no mês que optaram pelo
MEI no mesmo mês (formalização de MEI). `opcoes_mei` conta todas as opções
pelo MEI no mês (inclui empresas já existentes que migraram).

**6. Amostra.** O critério "50 mil a 600 mil habitantes" (população de 2019)
seleciona **40** municípios, não 33: o texto do artigo (resumo, seção 4.1 e
limitações) deve ser atualizado. Cuiabá, Goiânia e Campo Grande, citadas
como exemplo no Quadro 1, têm mais de 600 mil habitantes e ficam fora;
Aparecida de Goiânia (578 mil) entra.

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
p <- read.csv("dados/painel_pix_pj_mensal_amostra40.csv")
cs <- att_gt(yname = "asinh_y1_pix_pj_mil_hab", tname = "periodo",
             idname = "id", gname = "G_difusao50_t",
             xformla = ~ ln_pop_2019 + idhm_2010 + ln_pib_pc_2019 + campus,
             data = p, control_group = "notyettreated", est_method = "dr",
             clustervars = "id", bstrap = TRUE)
aggte(cs, type = "dynamic")
```
