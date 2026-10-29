# Bases dos estudos de caso

Bases usadas nos estudos de caso dos Conteúdos 3 a 6. Os arquivos `.dta`
abrem no Stata, no R (`haven::read_dta`) e no Python (`pandas.read_stata`).

| Arquivo | Unidade e período | Uso | Observação |
|---|---|---|---|
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
| `co2_pd_2000_2020.dta` | 193 países, 2000–2020 | Conteúdos 5 e 6 | Política de P&D e emissões de CO2 (base didática) |

## Observações sobre a PNAD

- `genero`: variável binária (0/1). O coeficiente positivo na regressão de renda sugere 1 = homem; confira na documentação da sua extração.
- `raça`, `estcivil`, `horas_trabalhadas` (faixas de horas) e `tipo_de_familia` são **códigos de categorias** do IBGE. Em regressões, o correto é tratá-los como variáveis categóricas (`i.raca` no Stata, `C(raca)` no Python, `factor(raca)` no R).
- A renda (`Renda`, V4720) inclui zeros. Para usar `ln(Renda)`, restrinja a renda positiva.

## Arquivos gerados

`preparar_web.py` gera os arquivos `casos_dados.js` que as páginas usam nos exploradores interativos. Rode-o de novo se alterar as bases.
