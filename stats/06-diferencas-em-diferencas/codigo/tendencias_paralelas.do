* Conteúdo 6 — Tendências paralelas: verificação (Estatística e Econometria, PROFINIT)
* Execute a partir da pasta codigo/.

import delimited "../dados/programa_saude.csv", clear
xtset municipio ano

* 1. Gráfico das médias
collapse (mean) gasto_saude_pc, by(ano tratado)
twoway (connected gasto_saude_pc ano if tratado == 1) ///
       (connected gasto_saude_pc ano if tratado == 0), xline(2014.5)

* 2. Teste formal com o comando nativo (Stata 17+)
import delimited "../dados/programa_saude.csv", clear
generate D = tratado * pos
didregress (gasto_saude_pc) (D), group(municipio) time(ano)
estat ptrends              // H0: tendências paralelas no pré-tratamento
estat trendplots

* 3. Tendência diferencial e placebo de data, só com o período pré
preserve
keep if ano <= 2014
generate tend  = tratado * (ano - 2010)
generate falso = tratado * (ano >= 2012)
reghdfe gasto_saude_pc tend,  absorb(municipio ano) vce(cluster municipio)
reghdfe gasto_saude_pc falso, absorb(municipio ano) vce(cluster municipio)
restore
