# Apostas online (bets) e saúde financeira dos municípios — DiD contínuo

Base de dados e estimações para o artigo *"Apostas esportivas online e saúde
financeira das famílias: evidência causal a partir do bloqueio de sites
ilegais nos municípios brasileiros"*. Choque: bloqueio de ~2.040 sites pela
Anatel em **out/2024**; painel município × mês, **jan/2023 a dez/2025**.

## O que foi possível estimar

| Item do artigo | Situação |
|---|---|
| BetExposure (eq. 1): Pix para CNAE 92 por município | **Não é público.** O BCB só divulga Pix por CNAE em nível nacional e por seção (a seção R inteira). Mesmo via LAI, o município do *recebedor* indicaria onde ficam as empresas de apostas, não onde moram os apostadores. |
| DigYouth (eq. 2), pré-determinada | **Construída**: homens 18–35 / população (Censo 2022, SIDRA 9514) × banda larga fixa por 100 domicílios (Anatel, dez/2022). |
| H1 poupança, depósitos, crédito (ESTBAN) | **Estimado**, 2.917 municípios com agência nos 36 meses. |
| H2 inadimplência PF por município | **Não é possível**: o SCR/IF.Data só é público por UF ou por instituição. |
| H3, H4 heterogeneidade (renda, jovens) | **Estimado** (Bolsa Família e 4G não incluídos). |
| H5 dois eventos (bloqueio x vigência) | **Estimado** (eq. 6). |
| H6 ISS | **Estimado**, ISS **mensal** (SICONFI, RREO Anexo 3), 3.525 municípios. |
| CGBS (DiD contínuo) | **Estimado** com o pacote `contdid`, sem covariáveis. |
| HonestDiD | Não executado (pacote não instalável no ambiente). |

## Resultados

**Exposição não é aleatória.** DigYouth é, na prática, banda larga
(correlação 0,98) e está correlacionada com renda (0,43 com ln PIB pc). Já
antes do bloqueio, a poupança cresceu menos onde DigYouth é maior
(−0,043 por desvio-padrão; −0,025 controlando renda e população).

**DiD contínuo (eq. 3)**, coeficiente de DigYouth(z) × Pós (erros
agrupados por município):

| Desfecho | (a) EF mun.+mês | (b) + UF×mês | (c) + mês×(renda, pop) + agências |
|---|---|---|---|
| ln poupança pc | −0,045*** | −0,010** | −0,0065 (p = 0,10) |
| ln dep. à vista pc | −0,029*** | −0,003 | −0,008 |
| ln dep. a prazo pc | −0,057*** | −0,047*** | −0,010 |
| ln crédito pc | −0,020*** | −0,011** | −0,009* |
| asinh ISS pc | −0,002 | 0,004 | 0,008 |

- A estimativa encolhe para perto de zero à medida que entram controles
  regionais e de renda, sinal de que a especificação ingênua capta a
  diferença urbano/rural, não as bets.
- **H1 não é confirmada**: na especificação mais controlada, a poupança
  *cai* levemente (não sobe) onde a exposição era maior. Pré-tendências
  conjuntas: p = 0,07 (poupança), 0,82 (à vista), 0,38 (prazo), 0,23
  (crédito).
- **H5**: bloqueio (out–dez/2024) e vigência (2025) ≈ 0 para todos os
  desfechos.
- **H6**: ISS sem efeito e sem pré-tendência.
- **H3**: efeito mais negativo em municípios de baixa renda (−0,026***),
  sinal oposto ao esperado; **H4**: nenhuma diferença por proporção de
  jovens.
- Placebo (bloqueio fictício em out/2023): nulo para todos os desfechos.
- **CGBS** (1º decil como dose zero, trimestral, sem covariáveis): ATT
  poupança −0,061 (e.p. 0,013), mas com pré-tendências significativas em
  todos os trimestres pré — não interpretável como causal.

**Conclusão**: com a exposição pré-determinada disponível, não há evidência
de que o bloqueio tenha recomposto a poupança ou os depósitos nos municípios
mais expostos. A medida DigYouth está tão ligada a urbanização e renda que
dificulta separar bets de outros choques do período (Selic em alta a partir
de set/2024, que favorece aplicações fora da poupança justamente nos
municípios mais ricos e conectados).

## Problemas nos dados do ESTBAN tratados

- **Santander, jan–mar/2025**: crédito nacional zerado e, em jan/2025,
  depósitos à vista de R$ 276 trilhões (registro corrompido). Regra: se a
  instituição tem crédito, depósitos à vista ou poupança zerados no país
  inteiro (com saldo antes e depois) ou acima de 20× a sua mediana, o
  registro do mês inteiro é imputado com o último valor (LOCF).
- **Banco Cooperativo Sicredi**: poupança com sinal trocado a partir de
  jan/2025 (convertida em valor absoluto; o mesmo para outros saldos de
  depósito negativos).
- **BRB e Banco Master (nov–dez/2025)**: não-reporte imputado.
- Mesmo com a correção, o crédito cai em fev–mar/2025 nos municípios mais
  expostos — provável reflexo da reestruturação da carteira do Santander
  (de R$ 569 bi em dez/2024 para R$ 430 bi em abr/2025), cujas agências se
  concentram em municípios com mais banda larga. Uma robustez útil é refazer
  os desfechos sem o Santander.
- O ESTBAN cobre só municípios com **agência** (2.917 com dados nos 36
  meses), não os ~4.800 previstos no artigo.

## Sugestões para o artigo

1. Pedir ao BCB, via LAI, o volume de Pix para CNPJs de apostas **por
   município do pagador** (jan–set/2024). Sem isso, o desenho fica apoiado
   numa proxy que é essencialmente banda larga.
2. Considerar a portaria que proibiu o uso de cartão de crédito e de
   recursos de programas sociais nas bets e a alta da Selic como choques
   concorrentes no mesmo período.
3. Para H2, usar o SCR.data por UF e modalidade (27 unidades) como análise
   complementar.

## Arquivos e reprodução

| Arquivo | Conteúdo |
|---|---|
| `dados/processados/estban_municipio_mes.csv` | ESTBAN agregado por município e mês |
| `dados/processados/iss_municipio_mes.csv` | ISS mensal (SICONFI) |
| `dados/processados/covariaveis_municipio.csv` | DigYouth, Censo 2022, Anatel, PIB |
| `resultados/` | tabelas, gráficos e `saida_estimacoes.txt` |

O painel final (`dados/painel_bets_mensal.csv`, 85 MB) não vai para o Git;
recrie-o com o script 04. De dentro de `codigo/`:

```bash
python 01_estban_bcb.py      # ESTBAN jan/2023-dez/2025 (~30 min)
python 02_iss_siconfi.py     # ISS mensal, RREO Anexo 3 (~20 min)
python 03_covariaveis.py     # requer dados/brutos/anatel/bl.zip (Anatel, ~1 GB)
python 04_montar_painel.py
Rscript 05_estimacoes.R      # fixest e contdid
```

Fonte do arquivo da Anatel:
`https://www.anatel.gov.br/dadosabertos/paineis_de_dados/acessos/acessos_banda_larga_fixa.zip`.
