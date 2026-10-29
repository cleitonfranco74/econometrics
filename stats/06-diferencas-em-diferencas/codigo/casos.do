* Estudos de caso — 06-diferencas-em-diferencas (Estatística e Econometria, PROFINIT)
* Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

* ssc install reghdfe ; ssc install csdid ; ssc install drdid ; ssc install event_plot
* Casos 2x2: iFood sintético e DEAMs
import delimited "../../dados_caso/did_ifood_sintetica.csv", clear
regress criminalidade treated post did, vce(cluster id_area)
encode id_area, generate(area)
xtset area ano
xtreg criminalidade did i.ano, fe vce(cluster area)

import delimited "../../dados_caso/did_deams_sintetica_2000_2018.csv", clear
regress taxa_homicidios_femininos treated post did, vce(cluster id_municipio)
generate lpopf = ln(pop_feminina)
generate lpib = ln(pib_per_capita)
regress taxa_homicidios_femininos treated post did lpopf lpib prop_eleitoras_primario, ///
    vce(cluster id_municipio)

* Adoção escalonada: iFood em SP
use "../../dados_caso/ifood_crime_sp.dta", clear
xtset cod_mun ano
generate lcrimes = ln(crimes)

* TWFE
reghdfe lcrimes post_ifood, absorb(cod_mun ano) vce(cluster cod_mun)

* Estudo de eventos TWFE (referência: ano -1)
generate rel = cond(ifood_ano > 0, ano - ifood_ano, .)
replace rel = max(min(rel, 5), -5) if rel < .
forvalues k = 5(-1)2 {
    generate pre`k' = (rel == -`k')
}
forvalues k = 0/5 {
    generate pos`k' = (rel == `k')
}
reghdfe lcrimes pre5-pre2 pos0-pos5, absorb(cod_mun ano) vce(cluster cod_mun)

* Callaway & Sant'Anna: gvar = ano da primeira adoção (0 = nunca tratado)
csdid lcrimes, ivar(cod_mun) time(ano) gvar(ifood_ano)   // controle: nunca tratados
estat simple
estat event, window(-5 5)
csdid_plot

* Farmácia Popular: TWFE, intensidade e placebos
use "../../dados_caso/farmacia_popular_mt.dta", clear
reghdfe mortes_hipertensao fp, absorb(cod_mun ano) vce(robust)
foreach p in mortes_afogamento mortes_neoplasias mortes_pneumonia {
    reghdfe `p' fp, absorb(cod_mun ano) vce(robust)
}
