# Bases dos estudos de caso

Bases usadas nos estudos de caso dos Conteúdos 3 a 6. Os arquivos `.dta`
abrem no Stata, no R (`haven::read_dta`) e no Python (`pandas.read_stata`).

| Arquivo | Unidade e período | Uso | Observação |
|---|---|---|---|
| `sorvete_afogamentos_aula.csv` | 12 meses | Conteúdo 3 | Vendas de sorvete e afogamentos (planilha da disciplina) |
| `sorvete_afogamentos.csv` | 36 meses (ilustrativo) | Conteúdo 3 | Mesma ideia com temperatura, para a correlação parcial (simulado por `exemplos_slides.py`) |
| `margarina_divorcio_maine.csv` | EUA, 2000–2009 | Conteúdo 3 | Série original de Tyler Vigen ([tylervigen.com/spurious-correlations](https://www.tylervigen.com/spurious-correlations)); r = 0,993, como no slide |
| `nicolas_cage_afogamentos.csv` | EUA, 1999–2009 | Conteúdo 3 | Correlação espúria de Tyler Vigen |
| `carga_tributaria_gini.csv` | 17 países | Conteúdo 3 | Planilha da disciplina (valores aproximados) + coluna `gini_bm_2019` com o Gini do Banco Mundial (de `gini_pib_mundo.dta`) |
| `salario_minimo_cesta_basica.csv` | Mensal, jan/2018–out/2021 | Conteúdo 3 | Planilha da disciplina |
| `vacinacao_obitos.csv` | 10 meses | Conteúdo 3 | Planilha da disciplina |
| `gasto_saude_suicidio_ocde.csv` | 12 países da OCDE | Conteúdo 3 | Valores aproximados do gráfico dos slides (Peterson-KFF; OECD Health Statistics) |
| `correlacoes_empresariais.xlsx` | Abas Apple, Netflix, CocaCola, Tesla, Tarifaço, Tesla_BYD | Conteúdo 3 | Séries ilustrativas da disciplina |
| `google_reglinear.xlsx` | Google, mensal, 2019–2023 | Conteúdo 3 | Série ilustrativa |
| `gini_pib_mundo.dta` | 164 países, 2010–2019 | Conteúdos 3 e 5 | Gini, PIB per capita (PPC) e população (Our World in Data / Banco Mundial) |
| `gini_pib_america_sul.dta` | 6 países sul-americanos, 2010–2019 | Conteúdo 3 | Recorte da base anterior |
| `coca_cola_regioes.csv` | 80 regiões × 2022–2025 | Conteúdos 3 e 4 | Obesidade, consumo de refrigerante e controles (ilustrativa) |
| `estudos_caso_regressao_multipla.xlsx` | Abas Amazon, Google, Microsoft, Petrobras, MercadoLivre (mensal, 2019–2023) + Dicionário | Conteúdo 4 | Séries ilustrativas; o dicionário indica a variável dependente e as variáveis “originais” e “novas” |
| `wage1.dta` | 526 trabalhadores (EUA, 1976) | Conteúdo 4 | Base clássica de Wooldridge, *Introdução à Econometria* |
| `pnad_2009_2011_internet_renda.dta` | 600.266 pessoas, PNAD/IBGE (2009, 2011 e 2012) | Conteúdo 4 | Microdados da PNAD; variáveis com o código original (V…) no rótulo |
| `samu_mt_2000_2020.dta` | 141 municípios de MT, 2000–2020 | Conteúdos 4, 5 e 6 | SAMU e mortes no trânsito (base didática) |
| `farmacia_popular_mt.dta` | 141 municípios de MT, 2003–2011 | Conteúdo 6 | Base didática que reproduz o desenho de Mesquita & Nishimura (Farmácia Popular e hipertensão) |
| `ifood_crime_sp.dta` | 644 municípios de SP, 2010–2019 | Conteúdo 6 | Base didática inspirada em Frankenthal (2025), *The Gig Economy and Crime* |
| `did_ifood_sintetica.csv` | 50 áreas, 2018–2025 | Conteúdo 6 | Base sintética 2×2 (efeito simulado −10); documentação em `documentacao_did_ifood_sintetica.docx` |
| `did_deams_sintetica_2000_2018.csv` | 100 municípios de MT, 2000–2018 | Conteúdo 6 | Base sintética 2×2: DEAMs, Lei Maria da Penha e homicídios femininos |
| `co2_pd_2000_2020.dta` | 193 países, 2000–2020 | Conteúdos 5 e 6 | Política de P&D e emissões de CO2 (base didática) |

## Diferenças entre versões

- **Margarina × divórcio:** a planilha da disciplina tinha valores arredondados (8,0 lb em 2000; r = 0,983). A base usa a série original de Tyler Vigen, a mesma mostrada no slide (8,2 lb; r = 0,993).
- **Carga tributária × Gini:** o gráfico do slide e a planilha diferem (por exemplo, Suécia: Gini 0,31 e carga 54% no gráfico; 0,23 e 50% na planilha). Comparados com o Gini do Banco Mundial de 2019, os dois têm o mesmo erro médio (0,03). A página usa a planilha. Para uso formal, substitua por séries oficiais do mesmo ano (OCDE *Revenue Statistics* e Banco Mundial).

## Artigos

O artigo da Farmácia Popular (Mesquita & Nishimura) está em `stats/artigos/`. O de Frankenthal (2025) está disponível no site do MIT: <https://economics.mit.edu/sites/default/files/inline-files/Gig_Economy_and_Crime_Oct25.pdf>.

## Observações sobre a PNAD

- `genero`: variável binária (0/1). O coeficiente positivo na regressão de renda sugere 1 = homem; confira na documentação da sua extração.
- `raça`, `estcivil`, `horas_trabalhadas` (faixas de horas) e `tipo_de_familia` são **códigos de categorias** do IBGE. Em regressões, o correto é tratá-los como variáveis categóricas (`i.raca` no Stata, `C(raca)` no Python, `factor(raca)` no R).
- A renda (`Renda`, V4720) inclui zeros. Para usar `ln(Renda)`, restrinja a renda positiva.

## Arquivos gerados

`exemplos_slides.py` gera as pequenas bases dos exemplos clássicos de correlação. `preparar_web.py` gera os arquivos `casos_dados.js` que as páginas usam nos exploradores interativos. Rode-o de novo se alterar as bases.
