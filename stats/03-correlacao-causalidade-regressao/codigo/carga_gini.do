* Conteúdo 3 — Estudo de caso: carga tributária e desigualdade (Estatística e Econometria, PROFINIT)
* Execute a partir da pasta codigo/.

import delimited "../../dados_caso/carga_gini_ocde_brasil.csv", clear encoding(utf-8)
pwcorr carga_pib gini, sig                       // todos (38): r = −0,66
pwcorr carga_pib gini if pais != "Brasil", sig   // sem o Brasil: −0,70
bysort grupo: pwcorr carga_pib gini, sig         // Simpson: −0,46 e +0,31
regress gini carga_pib
twoway (scatter gini carga_pib, mlabel(pais) mlabsize(vsmall)) (lfit gini carga_pib)
