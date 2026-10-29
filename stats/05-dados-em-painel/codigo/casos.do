* Estudos de caso — 05-dados-em-painel (Estatística e Econometria, PROFINIT)
* Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

use "../../dados_caso/samu_mt_2000_2020.dta", clear
xtset cod_mun ano
generate frota_pc = frota / pop * 100
regress tx_mortes_transito samu frota_pc i.ano, vce(cluster cod_mun)    // pooled
xtreg   tx_mortes_transito samu frota_pc i.ano, fe vce(cluster cod_mun) // efeitos fixos
xtsum ortopedista samu tx_analfa                                        // variação within

use "../../dados_caso/gini_pib_mundo.dta", clear
encode code, generate(pais)
xtset pais year
generate lpib = ln(gdppercapita)
xtsum lpib ginicoefficient
regress ginicoefficient lpib i.year, vce(cluster pais)
xtreg   ginicoefficient lpib i.year, fe vce(cluster pais)

use "../../dados_caso/co2_pd_2000_2020.dta", clear
xtset cod_pais ano
xtreg ln_co2_pc pd taxadeurbanizacao crescimentopop i.ano, fe vce(cluster cod_pais)
