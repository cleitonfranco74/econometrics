* Estudos de caso — 03-correlacao-causalidade-regressao (Estatística e Econometria, PROFINIT)
* Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

use "../../dados_caso/gini_pib_mundo.dta", clear
generate lpib = ln(gdppercapita)
bysort code (year): keep if _n == _N            // observação mais recente
pwcorr ginicoefficient gdppercapita lpib, sig
spearman ginicoefficient gdppercapita
regress ginicoefficient c.lpib##c.lpib, robust
twoway (scatter ginicoefficient lpib) (qfit ginicoefficient lpib)

import excel "../../dados_caso/google_reglinear.xlsx", firstrow clear
rename (InvestimentoemIAbiUSD ReceitadePublicidadebiUSD) (ia receita)
regress receita ia

import excel "../../dados_caso/correlacoes_empresariais.xlsx", sheet("Apple") firstrow clear
pwcorr _all, sig
