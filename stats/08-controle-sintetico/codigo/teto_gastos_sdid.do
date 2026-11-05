* Conteúdo 8 — SDID: teto de gastos de 2016, base SIMULADA (Estatística e Econometria, PROFINIT)
* Execute a partir da pasta codigo/.

* ssc install sdid
import delimited "../../dados_caso/teto_gastos_sintetica.csv", clear encoding(utf-8)
generate teto = (pais == "Brasil" & ano >= 2017)
encode pais, generate(id)

sdid juro_real_10a id ano teto, vce(placebo) reps(200) seed(2016) graph
sdid juro_real_10a id ano teto, vce(placebo) reps(200) method(sc)    // controle sintético
sdid juro_real_10a id ano teto, vce(placebo) reps(200) method(did)   // DiD

* Resultado primário sem a recessão de 2014–2016
sdid resultado_primario id ano teto if !inrange(ano, 2014, 2016), vce(placebo) reps(200) seed(2016) graph
