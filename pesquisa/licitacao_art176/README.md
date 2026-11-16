# Licitação eletrônica obrigatória e o art. 176 da Lei 14.133/2021 (Paraná)

Base de dados e estimações para o projeto *"Licitação eletrônica obrigatória e
eficiência das compras públicas municipais: evidência causal do art. 176 da
Lei 14.133/2021"*. Universo: os 399 municípios do Paraná, 2018–2026.

## Resultado principal: o teste de viabilidade falha

O projeto condiciona o desenho a um teste prévio (seção 6 e Quadro 1): *"se os
municípios abaixo de 20.000 habitantes já operavam majoritariamente no
ambiente eletrônico, o primeiro estágio será nulo e o desenho deve ser
abandonado"*. Os dados mostram exatamente isso:

| % de municípios com Elet ≥ 0,5 | 2023 | 2024 | 2025 |
|---|---|---|---|
| até 5 mil hab. | 8% | 71% | 81% |
| 5–10 mil | 13% | 70% | 81% |
| 10–15 mil | 12% | 75% | 90% |
| 15–20 mil | 9% | 84% | 94% |
| 20–25 mil | 6% | 88% | 88% |
| 25–50 mil | 18% | 78% | 88% |
| mais de 50 mil | 14% | 80% | 91% |

Os municípios dispensados pelo art. 176 migraram **na mesma data (2024) e na
mesma proporção** que os obrigados. Primeiro estágio estimado:

- DiD (Elet ~ obrigado × pós): **0,027 (e.p. 0,023)**;
- descontinuidade em 20 mil hab. (Elet 2024): **0,03 (e.p. 0,27)**.

A regra do art. 176 não vinculou, na prática, os municípios paranaenses: a
mudança para o eletrônico foi geral em 2024, coincidindo com a revogação da
Lei 8.666. O corte de 20 mil não pode servir de fonte de variação exógena
para a adoção.

## Limitações dos dados (diferentes do previsto no projeto)

1. **O Mural de Licitações do TCE-PR não distingue pregão eletrônico de
   presencial** (a modalidade aparece só como "Pregão"). A adoção (eq. 1) foi
   medida no **PNCP**, que separa as formas (códigos 4/6 eletrônicos, 5/7
   presenciais).
2. **O Mural tem uma lacuna de jul/2021 a dez/2024** (não há arquivos de 2022
   e 2023; o de 2024 só cobre o 1º trimestre). Trimestres completos:
   2018T1–2021T1 e 2025T1–2026T1. Diagnóstico em
   `dados/processados/mural_cobertura_trimestral.csv`.
3. **O Mural não traz nº de licitantes, preço homologado nem fornecedor
   vencedor.** Os desfechos H1 (licitantes), H2 (preço unitário) e H4
   (fornecedores de fora) não podem ser construídos com dados abertos do
   TCE-PR. Os desfechos disponíveis são os da H6: nº de processos,
   competitivos e diretos e a participação de dispensas/inexigibilidades
   (em número e em valor de referência).
4. Elet(i,t) = certames eletrônicos do município no PNCP no ano t ÷ média
   anual de certames competitivos do município no Mural em 2018–2020. Antes
   de 2024 a publicação no PNCP era facultativa para quem licitava pela Lei
   8.666/10.520, por isso Elet subestima o pregão eletrônico feito em outras
   plataformas nesse período.
5. Despesa com pessoal: o RGF de 2019 só está na API do SICONFI para ~1/3 dos
   municípios; usa-se a despesa liquidada com Pessoal e Encargos (DCA) sobre a
   receita corrente (`pessoal_rc_2019`). Distância a Curitiba é em linha reta.
   Alternância de prefeitos (TSE) e banda larga (Anatel) não foram incluídas.
6. HonestDiD não foi executado (o pacote não compilou no ambiente).

## Estimações (R) — `codigo/05_estimacoes.R`, saída em `resultados/`

**A. DiD do corte legal (ITT)**, painel município × trimestre, EF de
município e trimestre, erros agrupados por município:

| Desfecho | Obrigado × Pós | e.p. |
|---|---|---|
| Part. de contratações diretas (nº) | 0,021 | 0,015 |
| Part. de contratações diretas (valor) | −0,008 | 0,016 |
| asinh(nº de processos) | −0,117 | 0,041 |
| asinh(nº de competitivos) | −0,216 | 0,045 |

Os efeitos sobre contagens **não são causais**: o estudo de evento mostra o
mesmo hiato já em 2021T1 (antes da obrigação) e em 2018, e ele desaparece ao
controlar tendências por covariáveis de 2019 (−0,026 e −0,047, n.s.).

**B. Diferenças-em-descontinuidades** (ΔY pós − pré, `rdrobust`): nada
significativo para participação de diretas em número nem para contagens; para
a participação em valor aparece −0,09 a −0,13 (p < 0,01) com bandwidth ótima,
mas não com h = 2.900 (17 × 5 municípios). Como o primeiro estágio é nulo,
esse salto não pode ser atribuído à forma eletrônica. As covariáveis são
balanceadas no corte.

**C. DiD pela adoção efetiva** (Callaway e Sant'Anna, Elet ≥ 0,5; painel
anual 2018, 2019, 2020, 2025). Como só há desfechos em 2025 depois de 2021,
toda adoção entre 2022 e 2025 é observada como uma única coorte (2025);
controles = adotam em 2026 ou nunca (41 municípios). Resultados:

- part. de diretas em **valor: −0,058 (e.p. 0,021)**, pré-tendências ≈ 0
  (0,008 e −0,003) — o resultado mais robusto; com Elet ≥ 0,75: −0,042
  (0,017);
- part. de diretas em número: −0,049 (0,030); com Elet ≥ 0,75: −0,083 (0,017);
- nº de competitivos: +0,115 (0,085) sem covariáveis, +0,225 (0,072) com
  covariáveis, mas com pré-tendência negativa (−0,12 em 2018).

O sinal **contraria a H6**: a adoção do eletrônico vem acompanhada de
**menos** contratação direta, não mais. Mas a adoção é endógena (o corte
legal não serve de instrumento), o grupo de controle é pequeno e
selecionado, e não há observação de 2022–2024.

## Sugestões para o artigo

1. Reportar o teste de viabilidade como resultado: o art. 176 não teve
   efeito sobre a adoção no PR. É um achado relevante para o debate sobre a
   prorrogação/fim do prazo em 2027.
2. Reorientar a identificação: (a) usar a coorte de adoção precoce
   (2022–2023, ~49 municípios) contra a de 2024 com dados de 2022–2024 —
   exige obter do TCE-PR o Mural desses anos ou o SIM-AM (via LAI);
   (b) testar outros estados em que o art. 176 possa ter vinculado.
3. Para H1, H2 e H4, os dados de licitantes e preços precisam vir do
   SIM-AM/TCE-PR ou de portais de compras (BLL, BNC, Licitanet) — fora dos
   dados abertos.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `dados/painel_trimestral.csv` | 399 municípios × 18 trimestres (desfechos do Mural + grupos + covariáveis) |
| `dados/painel_anual.csv` | 399 × 2018–2026 (desfechos em anos completos; Elet e coortes de adoção) |
| `dados/primeiro_estagio_faixas.csv` | teste de viabilidade por faixa de população |
| `dados/processados/` | Mural agregado, covariáveis, população |
| `resultados/` | tabelas (.csv), gráficos (.png) e `saida_estimacoes.txt` |

## Como reproduzir

De dentro de `codigo/`:

```bash
python 01_tcepr_mural.py   # Mural de Licitações (TCE-PR)
python 02_pncp.py          # compras municipais do PR no PNCP (~30 min)
python 03_covariaveis.py   # IBGE, SICONFI, distância a Curitiba
python 04_montar_painel.py # painéis e coortes de adoção
Rscript 05_estimacoes.R    # estimações (did, fixest, rdrobust)
```

Fontes: [TCE-PR, dados abertos](https://servicos.tce.pr.gov.br/servicos/arquivos/dadosabertos/);
[PNCP, API de consulta](https://pncp.gov.br/api/consulta); IBGE/SIDRA;
SICONFI (API do Tesouro); coordenadas de
[kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros).
