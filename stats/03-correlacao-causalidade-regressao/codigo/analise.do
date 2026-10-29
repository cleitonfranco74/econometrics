* Conteúdo 3 — Correlação, causalidade e regressão simples (Estatística e Econometria, PROFINIT)
* Execute a partir desta pasta (codigo/).

import delimited "../dados/publicidade_vendas.csv", clear

pwcorr vendas publicidade tamanho, sig
spearman vendas publicidade

regress vendas publicidade
regress vendas publicidade, robust

* Previsão para publicidade = 15
margins, at(publicidade = 15)

twoway (scatter vendas publicidade) (lfit vendas publicidade)

regress vendas publicidade tamanho
